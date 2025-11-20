#!/usr/bin/env python3
from math import lgamma

import fontforge
import os
import json
import sys
import time
import argparse


DEBUG = False
ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONT_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipam.ttf')

def encode_to_surrogate_pair(codepoint):
    if codepoint < 0x10000:
        return None
    codepoint -= 0x10000
    high = 0xD800 + (codepoint >> 10)
    low = 0xDC00 + (codepoint & 0x3FF)
    return high, low

def format_codepoint_literal(codepoint):
    def _c(c):
        if c < 0x10000:
            return f"\\u{c:04X}"
        else:
            high, low = encode_to_surrogate_pair(c)
            return f"\\u{high:04X}\\u{low:04X}"
    if isinstance(codepoint, tuple):
        return ''.join(_c(cp) for cp in codepoint if cp != -1)
    else:
        return _c(codepoint)


def get_vs_name(vs_codepoint):
    """Variation SelectorのコードポイントからVS名を取得"""
    if 0xFE00 <= vs_codepoint <= 0xFE0F:
        # VS1-16
        return f"VS{vs_codepoint - 0xFE00 + 1}"
    elif 0xE0100 <= vs_codepoint <= 0xE01EF:
        # VS17-256
        return f"VS{vs_codepoint - 0xE0100 + 17}"
    else:
        return None

def analyze_pua_glyphs(pua_glyphs):
    print("Analyzing PUA glyphs...")
    t = 0
    vs_distribution = dict()
    for glyph in pua_glyphs:
        if not glyph.altuni:
            print(f"Warning: PUA glyph {glyph.glyphname} has no alternate unicode mapping.")
            continue
        for unicode, vs, _ in glyph.altuni:
            vs_name = get_vs_name(vs)
            if vs_name not in vs_distribution:
                vs_distribution[vs_name] = 0
            vs_distribution[vs_name] += 1
            t += 1

    for vs_name, count in vs_distribution.items():
        print(f"  {vs_name}: {count} glyphs")
    print(f"Total distinct VS entries: {len(vs_distribution)}")
    print(f"Total pua codepoint: {t}")
    return vs_distribution

def analyze_vs_distribution(vs_distribution):
    sorted_vs = sorted(vs_distribution.items(), key=lambda x: x[1], reverse=True)
    bmp_pua_capacity = 6400
    bmp_allocation = []
    smp_allocation = []
    current_bmp_used = 0
    for vs_name, count in sorted_vs:
        if current_bmp_used + count <= bmp_pua_capacity:
            # BMP PUAに全て配置可能
            bmp_allocation.append((vs_name, count, "full"))
            current_bmp_used += count
            print(f"  ✓ {vs_name}: {count:,}文字 → BMP PUA (全て)")
        elif current_bmp_used < bmp_pua_capacity:
            # 部分的にBMP PUAに配置
            bmp_portion = bmp_pua_capacity - current_bmp_used
            smp_portion = count - bmp_portion
            bmp_allocation.append((vs_name, bmp_portion, "partial"))
            smp_allocation.append((vs_name, smp_portion, "remaining"))
            current_bmp_used = bmp_pua_capacity
            print(f"  ⚠ {vs_name}: {count} {bmp_portion:,}文字 → BMP PUA, {smp_portion:,}文字 → SMP PUA")
        else:
            # SMP PUAに配置
            smp_allocation.append((vs_name, count, "full"))
            print(f"  → {vs_name}: {count:,}文字 → SMP PUA")
    current_smp_used = sum(count for _, count, _ in smp_allocation)

    print(f"配置結果:")
    print(f"  PUA文字数: {current_bmp_used + current_smp_used:,}文字")
    print(f"  BMP PUA使用: {current_bmp_used:,}/{bmp_pua_capacity:,}文字")
    print(f"  SMP PUA使用: {current_smp_used:,}文字")

    return {
        "bmp_allocation": bmp_allocation,
        "smp_allocation": smp_allocation,
        "bmp_used": current_bmp_used,
        "smp_used": current_smp_used,
    }

def build_pua_mapping(glyphs, pua_strategy):
    pua_map = dict()
    bmp_pua_start = 0xE000
    smp_pua_start = 0xF0000
    current_bmp_used = 0

    # glyph_name -> assigned PUA codepoint
    pua_glyph_map = dict()

    __vs = dict()

    def cnt(vsname):
        if vsname is None:
            return
        if vsname not in __vs:
            __vs[vsname] = 0
        __vs[vsname] += 1

    # Returns True if this call created a NEW PUA assignment for the glyph
    def add_pua_mapping(cp, vs, candidate_pua_cp, glyph):
        base_cp = cp
        if glyph not in pua_glyph_map:
            # New glyph assignment
            # map to IVS glyph
            pua_glyph_map[glyph] = candidate_pua_cp
            pua_map[(base_cp, vs)] = (candidate_pua_cp, glyph)
            cnt(get_vs_name(vs))
            return True
        else:
            # Reuse existing glyph assignment
            pua_map[(base_cp, vs)] = (pua_glyph_map[glyph], glyph)
            cnt(get_vs_name(vs))
            return False

    def altiuns(_glyphs):
        for g in _glyphs:
            for unicode, vs, _ in g.altuni:
                yield g.glyphname, unicode, vs

    # BMP allocation: assign new PUA only when a glyph first appears; increment pointer only then
    for vs_name, count, allocation_type in pua_strategy['bmp_allocation']:
        if allocation_type == "full":
            for glyph_name, uncode, vs in altiuns(glyphs):
                if add_pua_mapping(uncode, vs, bmp_pua_start + current_bmp_used, glyph_name):
                    current_bmp_used += 1
        elif allocation_type == "partial":
            remaining_slots = count
            for glyph_name, uncode, vs in altiuns(glyphs):
                add_pua_mapping(uncode, vs, pua_glyph_map[glyph_name], glyph_name)
                if remaining_slots <= 0:
                    # No BMP slots left for new glyphs; defer mapping to SMP phase
                    continue
                # Assign a new BMP PUA slot to this glyph and map all its sequences
                if add_pua_mapping(uncode, vs, bmp_pua_start + current_bmp_used, glyph_name):
                    current_bmp_used += 1
                    remaining_slots -= 1
    if DEBUG:
        print(f"PUAマッピング内訳1:")
        for _vs_name, used in __vs.items():
            print(f"  {_vs_name}: {used:,}文字")

    __vs = dict()
    # SMP allocation: only create new assignment for glyphs without one; otherwise reuse
    for vs_name, count, allocation_type in pua_strategy['smp_allocation']:
        if allocation_type in ["full", "remaining"]:
            for glyph_name, uncode, vs in altiuns(glyphs):
                if glyph_name in pua_glyph_map:
                    add_pua_mapping(uncode, vs, pua_glyph_map[glyph_name], glyph_name)
                else:
                    if add_pua_mapping(uncode, vs, smp_pua_start, glyph_name):
                        smp_pua_start += 1
    if DEBUG:
        print(f"PUAマッピング内訳:")
        for _vs_name, used in __vs.items():
            print(f"  {_vs_name}: {used:,}文字")

    return pua_map, pua_glyph_map

def pua_map(pua_glyphs):
    for glyph in pua_glyphs:
        print(glyph.glyphname)


def copy_glyph(original_font, external_font, glyph_name, dist_code, full=False):
    external_font.createChar(-1, glyph_name)
    external_font[glyph_name].clear()

    original_font.selection.select(glyph_name)
    original_font.copy()
    external_font.selection.select(glyph_name)
    external_font.paste()
    external_font[glyph_name].width = original_font[glyph_name].width
    if hasattr(original_font[glyph_name], 'vwidth'):
        external_font[glyph_name].vwidth = original_font[glyph_name].vwidth
    external_font[glyph_name].unicode = dist_code
    if full:
        if not glyph_name.startswith("aj"):
            return
        if hasattr(original_font[glyph_name], "altuni") and original_font[glyph_name].altuni:
            external_font[glyph_name].altuni = list(original_font[glyph_name].altuni)

def create_new_font_from_original_font_metrics(original_font):
    external_font = fontforge.font()
    external_font.fontname = "IPA-IVS-External"
    external_font.fullname = "IPA Mincho IVS External Characters"
    external_font.familyname = "IPA-IVS-External"
    external_font.weight = "Regular"
    external_font.copyright = "Based on IPA Font License Agreement v1.0"
    external_font.encoding = "unicode4"

    # 元フォントと同じメトリクスを設定
    external_font.em = original_font.em
    external_font.ascent = original_font.ascent
    external_font.descent = original_font.descent
    # OS/2 テーブル相当（存在するプロパティのみ安全にコピー）
    for attr in (
            'os2_winascent','os2_windescent',
            'os2_typoascent','os2_typodescent','os2_typolinegap',
            'os2_use_typo_metrics','os2_capheight','os2_xheight',
            'os2_panose','os2_family_class','os2_vendor','os2_weight','os2_width','os2_fstype',
            'os2_unicoderanges','os2_codepages','os2_unicoderange','os2_codepageranges','os2_codepagerange'
    ):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                print(f"{attr}のコピーに失敗しました。")
    # hhea / vhea
    for attr in ('hhea_ascent','hhea_descent','hhea_linegap'):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                print(f"{attr}のコピーに失敗しました。")
    for attr in ('vhea_ascent','vhea_descent','vhea_linegap'):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                print(f"{attr}のコピーに失敗しました。")
    # 下線位置/太さ
    for attr in ('upos','uwidth'):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                print(f"{attr}のコピーに失敗しました。")
    # 縦組メトリクス有効化
    if hasattr(external_font, 'hasvmetrics'):
        try:
            external_font.hasvmetrics = True
        except Exception:
            print("縦組メトリクス有効化に失敗しました。")
    # gasp（ヒンティング閾値）
    if hasattr(original_font, 'gasp') and hasattr(external_font, 'gasp'):
        try:
            external_font.gasp = original_font.gasp
        except Exception:
            print("gaspテーブルコピーに失敗しました。")
    return external_font

def generate_character_map(pusMap, basemap):
    def _make_map(_map):
        base_lines = []
        for key, value in _map.items():
            base_lines.append(f"  \"{format_codepoint_literal(key)}\": \"{format_codepoint_literal(value[0])}\", // {value[1]}")
        return base_lines

    js_content = "\nexport const ivsToExternalCharMap = {\n" + ",\n".join(_make_map(pusMap)) + "\n};\n"
    js_content += "\nexport const baseCharFallbackToExternalMap = {\n" + ",\n".join(_make_map(basemap)) + "\n};\n"
    return js_content

def optimize_glyph_metrics(original_font, output_ttf_path, output_woff2_path):
    # 生成直後に FontForge が内部再計算で hhea/OS2 Typo を肥大化させる場合がある。
    # 一度書き出したTTFを開き直し、最終メトリクスを確実に上書きしてから再保存する。
    try:
        fix = fontforge.open(output_ttf_path)
        try:
            if "nonmarkingreturn" in fix:
                g = fix["nonmarkingreturn"]
                g.unlinkReferences()
                fix.removeGlyph("nonmarkingreturn")
        except Exception:
            print("nonmarkingreturn削除に失敗しました。")

        # 元フォント由来の Typo 値を適用
        try:
            if hasattr(fix, 'os2_typoascent') and hasattr(original_font, 'os2_typoascent'):
                fix.os2_typoascent = int(original_font.os2_typoascent)
            if hasattr(fix, 'os2_typodescent') and hasattr(original_font, 'os2_typodescent'):
                fix.os2_typodescent = int(original_font.os2_typodescent)
            if hasattr(fix, 'os2_use_typo_metrics'):
                fix.os2_use_typo_metrics = True
            if hasattr(fix, 'os2_typolinegap'):
                fix.os2_typolinegap = 0
        except Exception:
            print("OS/2 Typoメトリクス最適化に失敗しました。")

        # 全グリフ bbox から WinAscent/Descent の下限を算出し、過大化しないように調整
        ymin2, ymax2 = None, None
        for gname in fix:
            try:
                g = fix[gname]
                bb = g.boundingBox()
                if not bb:
                    continue
                _, y0, _, y1 = bb
                if ymin2 is None or y0 < ymin2:
                    ymin2 = y0
                if ymax2 is None or y1 > ymax2:
                    ymax2 = y1
            except Exception:
                print("グリフのbbox取得に失敗しました。")
        if ymin2 is None or ymax2 is None:
            ymin2, ymax2 = -abs(getattr(original_font, 'os2_windescent', 0) or 0), getattr(original_font, 'os2_winascent', 0) or 0
        try:
            if hasattr(fix, 'os2_winascent'):
                fix.os2_winascent = int(max(getattr(original_font, 'os2_winascent', 0) or 0, ymax2))
            if hasattr(fix, 'os2_windescent'):
                fix.os2_windescent = int(max(abs(getattr(original_font, 'os2_windescent', 0) or 0), abs(ymin2)))
        except Exception:
            print("Winメトリクス最適化に失敗しました。")

        # hhea を Typo に同期し、LineGap を 0 に固定
        try:
            if hasattr(fix, 'hhea_ascent'):
                fix.hhea_ascent = int(getattr(original_font, 'os2_typoascent', original_font.ascent))
            if hasattr(fix, 'hhea_descent'):
                d = int(getattr(original_font, 'os2_typodescent', -abs(original_font.descent)))
                if d > 0:
                    d = -d
                fix.hhea_descent = d
            if hasattr(fix, 'hhea_linegap'):
                fix.hhea_linegap = 0
        except Exception:
            print("hheaメトリクス最適化に失敗しました。")

        # FontForge の ascent/descent も同期
        try:
            fix.ascent = int(original_font.ascent)
            fix.descent = int(original_font.descent)
        except Exception:
            print("フォント最適化中のascent/descent設定に失敗しました。")

        # 再保存（上書き）
        try:
            fix.generate(output_ttf_path)
        except Exception:
            print("フォント最適化後のTTF保存に失敗しました。")
        try:
            fix.generate(output_woff2_path)
        except Exception:
            print("フォント最適化後のWOFF2保存に失敗しました。")
        try:
            fix.close()
        except Exception:
            print("フォント最適化後のフォントクローズに失敗しました。")
    except Exception:
        print("フォント最適化中にエラーが発生しましたが、処理を継続します。")

class ProgressBar:
    def __init__(self, total, desc="Progress", bar_length=40, enable=True):
        self.enable = enable
        self.total = total
        self.desc = desc
        self.bar_length = bar_length
        self.current = 0
        self.start_time = time.time()

    def update(self, n=1):
        self.current += n
        self._display()

    def _format_time(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds / 3600)
            mins = int((seconds % 3600) / 60)
            return f"{hours}h {mins}m"

    def _display(self):
        if not self.enable:
            return
        percent = float(self.current) / self.total
        filled = int(self.bar_length * percent)
        bar = '█' * filled + '░' * (self.bar_length - filled)

        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)

        if self.current > 0:
            rate = self.current / elapsed  # items/sec
            remaining_items = self.total - self.current
            remaining_time = remaining_items / rate if rate > 0 else 0
            eta_str = self._format_time(remaining_time)
            speed_str = f"{rate:.2f} it/s"
        else:
            eta_str = "--"
            speed_str = "-- it/s"

        sys.stdout.write(
            f'\r{self.desc}: |{bar}| {percent:.1%} '
            f'{self.current}/{self.total} '
            f'[{elapsed_str}<{eta_str}, {speed_str}]'
        )
        sys.stdout.flush()

        if self.current >= self.total:
            print(f'\nCompleted in {elapsed_str}')

    def close(self):
        if self.current < self.total:
            self.current = self.total
            self._display()

def parse_args():
    parser = argparse.ArgumentParser(description="Generate external PUA-mapped font and mapping table.")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Analyze only; do not write any files.")
    # accept both --no-progress and --no-progressw for convenience/typo tolerance
    parser.add_argument("--no-progress", "--no-progressw", dest="no_progress", action="store_true", help="Disable progress bar output.")
    return parser.parse_args()

def main():
    args = parse_args()
    dryrun = bool(args.dry_run)

    src_font = fontforge.open(FONT_PATH)

    pua_glyphs = []
    codepoint_map = dict()
    keeping_glyphs = []

    for glyph in src_font.glyphs():
        if glyph.unicode == -1 and glyph.altuni and glyph.glyphname.startswith("mj"):
            # mj始まりで base unicodeが無いものはPUA扱い
            pua_glyphs.append(glyph)
        else:
            keeping_glyphs.append(glyph)

        if glyph.altuni:
            for unicode, vs, _ in glyph.altuni:
                if glyph.unicode != -1 and not glyph.glyphname.startswith("aj"):
                    codepoint_map[(unicode, vs)] = (glyph.unicode, glyph.glyphname)

    print(f"Found {len(list(src_font.glyphs()))} all glyphs")
    print(f"  {len(keeping_glyphs)} Keeping glyphs")
    print(f"  {len(pua_glyphs)} PUA glyphs")

    print(f"Keeping {len(keeping_glyphs)} glyphs with standard unicode")
    vs_distribution = analyze_pua_glyphs(pua_glyphs)
    pua_strategy = analyze_vs_distribution(vs_distribution)
    pua_map, pua_glyph_map = build_pua_mapping(pua_glyphs, pua_strategy)

    print(f"Generated PUA mapping for {len(pua_map)} codepoint+VS combinations")
    print(f"Generated PUA Glyph mapping for {len(pua_glyph_map)} codepoint+VS combinations")

    ext_font = create_new_font_from_original_font_metrics(src_font)

    total_generate_glyphs = len(pua_glyph_map) + len(keeping_glyphs)
    print(f"Copying keeping glyphs... {len(keeping_glyphs)} glyphs")
    print(f"Copying pua glyphs... {len(pua_glyph_map)} glyphs")
    print(f"Copying total glyphs... {total_generate_glyphs} glyphs")

    print(f"Generate alternate codepoint map {len(codepoint_map)} ")
    print(f"Generate pua codepoint map {len(pua_map)} ")

    js_content = generate_character_map(pua_map, codepoint_map)
    output_js_path = os.path.join(ROOT_DIR, 'src', 'utils', 'ivsCharacterMap.js')
    with open(output_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"Wrote character map to {output_js_path}")

    pbar = ProgressBar(total=total_generate_glyphs, desc="グリフコピー中", enable=not args.no_progress)

    for g in keeping_glyphs:
        if not dryrun:
            copy_glyph(src_font, ext_font, g.glyphname, g.unicode, full=True)
        pbar.update(1)

    for glyphname, pua_code in pua_glyph_map.items():
        if not dryrun:
            copy_glyph(src_font, ext_font, glyphname, pua_code, full=False)
        pbar.update(1)

    pbar.close()

    output_woff2_path = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.woff2')
    output_ttf_path = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.ttf')
    if not dryrun:
        print("TrueType形式で保存中...")
        ext_font.generate(output_ttf_path)

        print("WebFont形式で保存中...")
        ext_font.generate(output_woff2_path)
        ext_font.close()

        print("フォント最適化中...")
        optimize_glyph_metrics(src_font, output_ttf_path, output_woff2_path)
    src_font.close()
if __name__ == '__main__':
    main()