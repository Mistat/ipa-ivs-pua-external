#!/usr/bin/env python3

import fontforge
import os
import json
import sys
import time
import argparse

DEBUG = False
ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONT_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipam.ttf')

vs_distribution = dict()
base_char_map = dict()
no_unicode_mapped = []
total_glyphs = 0
ivs_chars = 0
total = 0

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

def process_glyphs(glyphs):
    global no_unicode_mapped, total_glyphs
    for glyph in glyphs:
        total_glyphs += 1
        if glyph.unicode != -1:
            yield glyph.glyphname, glyph.unicode, 0

        if glyph.altuni:
            for unicode_val, vs, _ in glyph.altuni:
                if unicode_val == 1:
                    raise ValueError(f"Invalid unicode value 1 found in altuni {glyph.glyphname}")
                if glyph.unicode == unicode_val and vs == -1:
                    raise ValueError(f"Duplicate base unicode mapping found in glyph {glyph.glyphname} for unicode {unicode_val:04X}")
                yield glyph.glyphname, unicode_val, vs

        if glyph.unicode == -1 and (not glyph.altuni or len(glyph.altuni) == 0):
            no_unicode_mapped.append(glyph.glyphname)

def list_glyphs(font):
    global total, ivs_chars, vs_distribution, base_char_map
    covered_codepoints = dict()
    has_base_glyph = set()
    glyphs_proceeded = dict()
    for glyph_name, unicode_val, vs in process_glyphs(font.glyphs()):
        info = {
            "glyph": glyph_name,
            "chars": []
        }
        if vs == 0 or vs == -1:
            has_base_glyph.add(unicode_val)
            m = chr(unicode_val)
            info["char"] = m
            if vs == 0:
                info["base"] = True
        else:
            ivs_sequence = chr(unicode_val) + chr(vs)
            vs_name = get_vs_name(vs)
            if vs_name not in vs_distribution:
                vs_distribution[vs_name] = 0
            vs_distribution[vs_name] += 1
            info["vs"] = vs
            info["vs_name"]= vs_name
            info["char"] = ivs_sequence
            info["sequence"] = f"U+{unicode_val:04X} U+{vs:04X}"

        if glyph_name in glyphs_proceeded:
            proceeded = glyphs_proceeded[glyph_name]
            if proceeded.get("base", False):
                kk = ''.join(format_codepoint_literal(ord(ch)) for ch in info["char"])
                if info.get("vs", -1) == -1:
                    base_char_map[kk] = {
                        "char": format_codepoint_literal(ord(proceeded.get("char", ""))),
                        "from": glyph_name
                    }
                    continue
                else:
                    pass
            elif info.get("base", False):
                raise ValueError(f"Glyph {glyph_name} has already been assigned to IVS variant, cannot assign base glyph.")
            glyphs_proceeded[glyph_name]["chars"].append(info)

        if glyph_name not in glyphs_proceeded:
            glyphs_proceeded[glyph_name] = info
        if unicode_val not in covered_codepoints:
            covered_codepoints[unicode_val] = []

        covered_codepoints[unicode_val].append(info)

        if vs > 0:
            ivs_chars += 1
        total += 1

    for codepoint in covered_codepoints:
        if len(covered_codepoints[codepoint]) == 0:
            print(f"Codepoint U+{codepoint:04X}({codepoint}) has no glyphs.")
        if not codepoint in has_base_glyph:
            print(f"Codepoint U+{codepoint:04X}({codepoint}) has no base glyph but has IVS variants.")
        if len(covered_codepoints[codepoint]) > 1:
            if len(list(filter(lambda x: x.get("base", False), covered_codepoints[codepoint]))) == 0:
                print(f"Codepoint U+{codepoint:04X} has multiple IVS variants but no base glyph.")

    return covered_codepoints, glyphs_proceeded

def analyze_vs_distribution(vs_distribution):
    print("VS分布解析中...")
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

def build_pua_mapping(glyphs_proceeded, pua_strategy):
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
        base_cp = ord(cp)
        if glyph not in pua_glyph_map:
            # New glyph assignment
            pua_glyph_map[glyph] = candidate_pua_cp
            pua_map[(base_cp, vs)] = candidate_pua_cp
            cnt(get_vs_name(vs))
            return True
        else:
            # Reuse existing glyph assignment
            pua_map[(base_cp, vs)] = pua_glyph_map[glyph]
            cnt(get_vs_name(vs))
            return False

    # Helper to collect all IVS sequences of a glyph for a specific vs_name
    def iter_seqs_for_vsname(info, vs_name):
        if info.get("vs_name") == vs_name:
            yield info["char"][0], info["vs"]
        for ch in info.get("chars", []):
            if ch.get("vs_name") == vs_name:
                yield ch["char"][0], ch["vs"]

    # BMP allocation: assign new PUA only when a glyph first appears; increment pointer only then
    for vs_name, count, allocation_type in pua_strategy['bmp_allocation']:
        if allocation_type == "full":
            for glyph_name, info in glyphs_proceeded.items():
                # Gather sequences for this vs_name
                seqs = list(iter_seqs_for_vsname(info, vs_name))
                if not seqs:
                    continue
                created = False
                for cp0, vs in seqs:
                    created |= add_pua_mapping(cp0, vs, bmp_pua_start + current_bmp_used, glyph_name)
                if created:
                    current_bmp_used += 1
        elif allocation_type == "partial":
            remaining_slots = count
            for glyph_name, info in glyphs_proceeded.items():
                seqs = list(iter_seqs_for_vsname(info, vs_name))
                if not seqs:
                    continue
                if glyph_name in pua_glyph_map:
                    # Already assigned elsewhere: just map sequences
                    for cp0, vs in seqs:
                        add_pua_mapping(cp0, vs, pua_glyph_map[glyph_name], glyph_name)
                    continue
                if remaining_slots <= 0:
                    # No BMP slots left for new glyphs; defer mapping to SMP phase
                    continue
                # Assign a new BMP PUA slot to this glyph and map all its sequences
                created = False
                for cp0, vs in seqs:
                    created |= add_pua_mapping(cp0, vs, bmp_pua_start + current_bmp_used, glyph_name)
                if created:
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
            for glyph_name, info in glyphs_proceeded.items():
                seqs = list(iter_seqs_for_vsname(info, vs_name))
                if not seqs:
                    continue
                if glyph_name in pua_glyph_map:
                    # Reuse existing assignment
                    for cp0, vs in seqs:
                        add_pua_mapping(cp0, vs, pua_glyph_map[glyph_name], glyph_name)
                else:
                    created = False
                    for cp0, vs in seqs:
                        created |= add_pua_mapping(cp0, vs, smp_pua_start, glyph_name)
                    if created:
                        smp_pua_start += 1
    if DEBUG:
        print(f"PUAマッピング内訳:")
        for _vs_name, used in __vs.items():
            print(f"  {_vs_name}: {used:,}文字")

    return pua_map

def encode_to_surrogate_pair(codepoint):
    if codepoint < 0x10000:
        return None
    codepoint -= 0x10000
    high = 0xD800 + (codepoint >> 10)
    low = 0xDC00 + (codepoint & 0x3FF)
    return high, low

def format_codepoint_literal(c):
    if c < 0x10000:
        return f"\\u{c:04X}"
    else:
        high, low = encode_to_surrogate_pair(c)
        return f"\\u{high:04X}\\u{low:04X}"

def convert_pua_mapping_to_literal_map(pua_mapping):
    literal_map = {}
    for (base_cp, vs), pua_cp in pua_mapping.items():
        ivs_str = format_codepoint_literal(base_cp) + format_codepoint_literal(vs)
        pua_str = format_codepoint_literal(pua_cp)
        literal_map[ivs_str] = pua_str
    return literal_map

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
                pass
    # hhea / vhea
    for attr in ('hhea_ascent','hhea_descent','hhea_linegap'):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                pass
    for attr in ('vhea_ascent','vhea_descent','vhea_linegap'):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                pass
    # 下線位置/太さ
    for attr in ('upos','uwidth'):
        if hasattr(original_font, attr) and hasattr(external_font, attr):
            try:
                setattr(external_font, attr, getattr(original_font, attr))
            except Exception:
                pass
    # 縦組メトリクス有効化
    if hasattr(external_font, 'hasvmetrics'):
        try:
            external_font.hasvmetrics = True
        except Exception:
            pass
    # gasp（ヒンティング閾値）
    if hasattr(original_font, 'gasp') and hasattr(external_font, 'gasp'):
        try:
            external_font.gasp = original_font.gasp
        except Exception:
            pass
    return external_font

def copy_glyph(original_font, external_font, glyph_name, dist_code):
    external_font.createChar(-1, glyph_name)
    external_font[glyph_name].clear()

    original_font.selection.select(glyph_name)
    original_font.copy()
    external_font.selection.select(glyph_name)
    external_font.paste()
    if glyph_name not in original_font:
        raise ValueError(f"Glyph for codepoint {glyph_name} not found in original font.")
    external_font[glyph_name].width = original_font[glyph_name].width
    if hasattr(original_font[glyph_name], 'vwidth'):
        external_font[glyph_name].vwidth = original_font[glyph_name].vwidth
    external_font[glyph_name].unicode = dist_code

def setup_glyph_metrics(original_font, external_font):
    try:
        # FontForge の font には boundingBox() が無い環境があるため、各グリフから集計
        ymin, ymax = None, None
        try:
            for gname in external_font:
                try:
                    g = external_font[gname]
                    bb = g.boundingBox()
                    if not bb:
                        continue
                    _, gymin, _, gymax = bb
                    if ymin is None or gymin < ymin:
                        ymin = gymin
                    if ymax is None or gymax > ymax:
                        ymax = gymax
                except Exception:
                    # 個別グリフの bbox 取得失敗は無視
                    pass
        except Exception:
            pass

        # フォールバック（万一 bbox が取れなかった場合）
        if ymin is None or ymax is None:
            ymin, ymax = -getattr(original_font, 'os2_windescent', 0), getattr(original_font, 'os2_winascent', 0)

        # OS/2 Win metrics は「見切れ防止のために必要最小限」に引き上げる（過大にしない）
        if hasattr(external_font, 'os2_winascent'):
            try:
                orig_win_asc = getattr(original_font, 'os2_winascent', 0) or 0
                external_font.os2_winascent = int(max(orig_win_asc, ymax))
            except Exception:
                pass
        if hasattr(external_font, 'os2_windescent'):
            try:
                orig_win_des = abs(getattr(original_font, 'os2_windescent', 0) or 0)
                external_font.os2_windescent = int(max(orig_win_des, abs(ymin)))
            except Exception:
                pass

        # Typo メトリクス（行送り基準）を元フォント値に固定し、UseTypoMetrics を有効化
        if hasattr(original_font, 'os2_typoascent') and hasattr(external_font, 'os2_typoascent'):
            try:
                external_font.os2_typoascent = int(original_font.os2_typoascent)
            except Exception:
                pass
        if hasattr(original_font, 'os2_typodescent') and hasattr(external_font, 'os2_typodescent'):
            try:
                # sTypoDescender は負の値を維持
                external_font.os2_typodescent = int(original_font.os2_typodescent)
            except Exception:
                pass
        if hasattr(external_font, 'os2_use_typo_metrics'):
            try:
                external_font.os2_use_typo_metrics = True
            except Exception:
                pass
        if hasattr(external_font, 'os2_typolinegap'):
            try:
                override = os.getenv('METRICS_TYPO_LINEGAP', '').lower()
                if override in ('keep', 'orig', 'original') and hasattr(original_font, 'os2_typolinegap'):
                    external_font.os2_typolinegap = original_font.os2_typolinegap
                else:
                    external_font.os2_typolinegap = 0
            except Exception:
                pass

        # hhea を Typo に同期（descender は負で設定）、LineGap は 0
        try:
            typo_asc = getattr(original_font, 'os2_typoascent', getattr(original_font, 'ascent', None))
            typo_des = getattr(original_font, 'os2_typodescent', getattr(original_font, 'descent', None))
            if typo_asc is not None and hasattr(external_font, 'hhea_ascent'):
                external_font.hhea_ascent = int(typo_asc)
            if typo_des is not None and hasattr(external_font, 'hhea_descent'):
                # hhea.descender は負値
                d = int(typo_des)
                if d > 0:
                    d = -d
                external_font.hhea_descent = d
            if hasattr(external_font, 'hhea_linegap'):
                external_font.hhea_linegap = 0
        except Exception:
            pass

        # FontForge の font.ascent/descent も整合のため更新
        try:
            if hasattr(original_font, 'ascent') and hasattr(external_font, 'ascent'):
                external_font.ascent = int(original_font.ascent)
            if hasattr(original_font, 'descent') and hasattr(external_font, 'descent'):
                external_font.descent = int(original_font.descent)
        except Exception:
            pass
    except Exception:
        # いずれかの処理に失敗しても生成自体は継続
        pass

def optimize_glyph_metrics(original_font, output_ttf_path, output_woff2_path):
    # 生成直後に FontForge が内部再計算で hhea/OS2 Typo を肥大化させる場合がある。
    # 一度書き出したTTFを開き直し、最終メトリクスを確実に上書きしてから再保存する。
    try:
        fix = fontforge.open(output_ttf_path)
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

def generate_character_map(ivsMap, basemap):
    js_content  = "\nexport const ivsToExternalCharMap = {\n" + ",\n".join([f"  \"{key}\": \"{value}\"" for key, value in ivsMap.items()]) + "\n};\n"
    base_lines = []
    for key, value in basemap.items():
        ch = value.get('char', "")
        frm = value.get('from', "")
        base_lines.append(f"  \"{key}\": \"{ch}\", // {frm}")
    js_content += "\nexport const baseCharFallbackToExternalMap = {\n" + ",\n".join(base_lines) + "\n};\n"
    return js_content

class ProgressBar:
    def __init__(self, total, desc="Progress", bar_length=40):
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

class NoOpProgressBar:
    def __init__(self, total=0, desc="", bar_length=0):
        self.total = total
        self.desc = desc
    def update(self, n=1):
        pass
    def close(self):
        pass

def parse_args():
    parser = argparse.ArgumentParser(description="Generate external PUA-mapped font and mapping table.")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Analyze only; do not write any files.")
    # accept both --no-progress and --no-progressw for convenience/typo tolerance
    parser.add_argument("--no-progress", "--no-progressw", dest="no_progress", action="store_true", help="Disable progress bar output.")
    return parser.parse_args()

def main():
    args = parse_args()
    src_font = fontforge.open(FONT_PATH)
    covered_codepoints, glyphs_proceeded = list_glyphs(src_font)
    plan_total_glyphs = len(glyphs_proceeded) + len(no_unicode_mapped)

    print(f"プラン:")
    print(f"  元のグリフ数: {total_glyphs:,}グリフ")
    print(f"  総コードポイント数: {total:,}コード")
    print(f"　ベース文字: {len(covered_codepoints):,}文字")
    print(f"　IVS文字(PUA文字数): {ivs_chars:,}文字")
    print(f"　ベースマッピング数: {len(base_char_map):,}文字")
    print(f"　ユニコードあり: {len(glyphs_proceeded):,}文字")
    print(f"　ユニコード無し: {len(no_unicode_mapped):,}文字")
    print(f"  作成予定のグリフ数: {plan_total_glyphs:,}グリフ")

    pua_strategy = analyze_vs_distribution(vs_distribution)
    pua_map = build_pua_mapping(glyphs_proceeded, pua_strategy)

    # 1) 変体シーケンスの総数とPUAマッピング件数
    if len(pua_map) != (pua_strategy.get("smp_used", 0) + pua_strategy.get("bmp_used", 0)):
        raise ValueError(
            f"PUA mapping count does not match the used PUA count. "
            f"Mapped: {len(pua_map)}, Used: {pua_strategy.get('smp_used', 0) + pua_strategy.get('bmp_used', 0)}"
        )
    print(f"  PUAマッピング数: {len(pua_map):,}文字")

    # 2) covered_codepoints に格納したエントリ総数と total の一致
    covered_total = sum(len(v) for v in covered_codepoints.values())
    if total != covered_total:
        raise ValueError(
            f"Covered entries mismatch. total={total}, covered_total={covered_total}"
        )

    # 3) IVS件数の自己整合: ivs_chars と covered_codepointsから再計算した件数
    computed_ivs = sum(
        1 for lst in covered_codepoints.values() for x in lst if x.get("vs", -1) > 0
    )
    if ivs_chars != computed_ivs:
        raise ValueError(
            f"IVS count mismatch. ivs_chars={ivs_chars}, computed_ivs={computed_ivs}"
        )

    ivs_processed = 0
    copyed = dict()
    dryrun = bool(args.dry_run)

    new_font = create_new_font_from_original_font_metrics(src_font)
    pbar = NoOpProgressBar(total=plan_total_glyphs, desc="グリフコピー中") if args.no_progress else ProgressBar(total=plan_total_glyphs, desc="グリフコピー中")
    for glyph_name, info in glyphs_proceeded.items():
        c = info.get("char")
        vs = info.get("vs", -1)
        if vs != -1:
            if (ord(c[0]), vs) in pua_map:
                dist_code = pua_map[(ord(c[0]), vs)]
                if not dryrun:
                    copy_glyph(src_font, new_font, glyph_name, dist_code)
                copyed[glyph_name] = dist_code
                pbar.update(1)
                ivs_processed += 1

        chars = info.get("chars", [])
        if len(chars) != 0:
            for c1 in chars:
                cc = c1.get("char")
                cvs = c1.get("vs")
                if (ord(cc[0]), cvs) in pua_map:
                    dist_code = pua_map[(ord(cc[0]), cvs)]
                    if glyph_name in copyed:
                        continue
                    copyed[glyph_name] = dist_code
                    if not dryrun:
                        copy_glyph(src_font, new_font, glyph_name, dist_code)
                    pbar.update(1)
                    ivs_processed += 1
        if glyph_name not in copyed:
            dist_code = ord(c[0])
            if not dryrun:
                copy_glyph(src_font, new_font, glyph_name, dist_code)
            copyed[glyph_name] = dist_code
            pbar.update(1)
        else:
            k = format_codepoint_literal(ord(c[0]))
            if k in base_char_map and info.get("base", False):
                raise ValueError(f"Duplicate base unicode mapping found for glyph {glyph_name} for unicode {ord(c[0]):04X}")
            if info.get("base", False):
                base_char_map[k] = {
                    "char": format_codepoint_literal(copyed[glyph_name]),
                    "from": glyph_name
                }

    for glyph_name in no_unicode_mapped:
        if not dryrun:
            copy_glyph(src_font, new_font, glyph_name, -1)
        pbar.update(1)
    pbar.close()

    if not dryrun:
        print(f"メトリクス設定中...")
        setup_glyph_metrics(src_font, new_font)

    pua_literal_map = convert_pua_mapping_to_literal_map(pua_map)
    js = generate_character_map(pua_literal_map, base_char_map)

    mapping_file_path = os.path.join(ROOT_DIR, 'src', 'utils', 'ivsCharacterMap.js')
    if not dryrun:
        with open(mapping_file_path, 'w', encoding='utf-8') as f:
            f.write(js)
        print(f"Mapファイルを書き出しました: {mapping_file_path}")
    else:
        print("[dry-run] Mapファイル出力をスキップしました")

    output_woff2_path = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.woff2')
    output_ttf_path = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.ttf')

    if not dryrun:
        print("TrueType形式で保存中...")
        new_font.generate(output_ttf_path)

        print("WebFont形式で保存中...")
        new_font.generate(output_woff2_path)

        print("フォント最適化中...")
        optimize_glyph_metrics(src_font, output_ttf_path, output_woff2_path)

        src_font.close()
        new_font.close()
    else:
        print("[dry-run] フォント出力をスキップしました")

    output = {
        "plan_total_glyphs": plan_total_glyphs,
        "covered_codepoints": covered_codepoints,
        "vs_distribution": vs_distribution,
        "base_char_map": base_char_map,
        "base_glyphs_without_unicode": no_unicode_mapped,
        "ivs_chars": ivs_chars,
        "total_covered": total,
        "strategy": pua_strategy,
    }

    print(f"  IVS文字数: {ivs_processed:,}文字")
    print(f"　ベースマッピング数: {len(base_char_map):,}文字")

    output_path = os.path.join(ROOT_DIR, 'tmp', 'covered_codepoints.json')
    if not dryrun:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"詳細情報を書き出しました: {output_path}")
    else:
        print("[dry-run] 詳細情報の書き出しをスキップしました")


if __name__ == "__main__":
    main()
