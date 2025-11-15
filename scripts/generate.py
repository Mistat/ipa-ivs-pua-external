#!/usr/bin/env python3

import fontforge
import os
import json
import sys
import time

ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONT_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipam.ttf')

vs_distribution = dict()
base_char_map = dict()
no_unicode_mapped = []
total_glyphs = 0
ivs_chars = 0
skip = 0
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
    global skip, no_unicode_mapped, total_glyphs
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

        if glyph.unicode == -1 and not glyph.altuni:
            no_unicode_mapped.append(glyph.glyphname)


def list_glyphs(font):
    global total, ivs_chars, vs_distribution, base_char_map
    covered_codepoints = dict()
    has_base_glyph = set()
    glyphs_proceeded = dict()
    for glyph_name, unicode_val, vs in process_glyphs(font.glyphs()):
        info = {
            "glyph": glyph_name,
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
                if unicode_val == ord(proceeded.get("char", "")):
                    continue
                base_char_map[format_codepoint_literal(unicode_val)] = format_codepoint_literal(ord(proceeded.get("char", "")))
                continue
            elif info.get("base", False):
                print(f"Replacing glyph {glyph_name} with base glyph.")
                glyphs_proceeded[glyph_name] = info
                for u in covered_codepoints[unicode_val]:
                    if u["glyph"] == glyph_name:
                        print(f"Updating covered codepoint U+{unicode_val:04X} to base glyph.")
                        base_char_map[format_codepoint_literal(ord(proceeded.get("char", "")))] = format_codepoint_literal(unicode_val)
                        covered_codepoints[unicode_val].remove(u)
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
            print(f"Codepoint U+{codepoint:04X}({codepoint})  has no base glyph but has IVS variants.")
        if len(covered_codepoints[codepoint]) > 1:
            if len(list(filter(lambda x: x.get("base", True), covered_codepoints[codepoint]))) == 0:
                print(f"Codepoint U+{codepoint:04X} has multiple IVS variants but no base glyph.")

    print(f"has_base_glyph count: {len(has_base_glyph)}")
    return covered_codepoints

def analyze_vs_distribution(vs_distribution, total_chars):
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
            print(f"✓ {vs_name}: {count:,}文字 → BMP PUA (全て)")
        elif current_bmp_used < bmp_pua_capacity:
            # 部分的にBMP PUAに配置
            bmp_portion = bmp_pua_capacity - current_bmp_used
            smp_portion = count - bmp_portion
            bmp_allocation.append((vs_name, bmp_portion, "partial"))
            smp_allocation.append((vs_name, smp_portion, "remaining"))
            current_bmp_used = bmp_pua_capacity
            print(f"⚠ {vs_name}: {bmp_portion:,}文字 → BMP PUA, {smp_portion:,}文字 → SMP PUA")
        else:
            # SMP PUAに配置
            smp_allocation.append((vs_name, count, "full"))
            print(f"→ {vs_name}: {count:,}文字 → SMP PUA")

    print(f"\n配置結果:")
    print(f"BMP PUA使用: {current_bmp_used:,}/{bmp_pua_capacity:,}文字")
    print(f"SMP PUA使用: {sum(count for _, count, _ in smp_allocation):,}文字")

    return {
        "bmp_allocation": bmp_allocation,
        "smp_allocation": smp_allocation,
        "bmp_used": current_bmp_used,
        "smp_used": sum(count for _, count, _ in smp_allocation),
        "total_chars": total_chars
    }

def build_pua_mapping(covered_codepoints, pua_strategy):
    pua_map = dict()
    bmp_pua_start = 0xE000
    smp_pua_start = 0xF0000
    current_bmp_used = 0
    for vs_name, count, allocation_type in pua_strategy['bmp_allocation']:
        if allocation_type == "full":
            for codepoint, glyphs in covered_codepoints.items():
                for glyph_info in glyphs:
                    if glyph_info.get("vs_name", "") == vs_name:
                        pua_map[(codepoint, glyph_info["vs"])] = bmp_pua_start + current_bmp_used
                        current_bmp_used += 1
        elif allocation_type == "partial":
            portion = count
            for codepoint, glyphs in covered_codepoints.items():
                for glyph_info in glyphs:
                    if glyph_info.get("vs_name", "") == vs_name:
                        if portion <= 0:
                            break
                        pua_map[(codepoint, glyph_info["vs"])] = bmp_pua_start + current_bmp_used
                        current_bmp_used += 1
                        portion -= 1

    for vs_name, count, allocation_type in pua_strategy['smp_allocation']:
        if allocation_type in ["full", "remaining"]:
            for codepoint, glyphs in covered_codepoints.items():
                for glyph_info in glyphs:
                    if glyph_info.get("vs_name", "") == vs_name:
                        pua_map[(codepoint, glyph_info["vs"])] = smp_pua_start
                        smp_pua_start += 1

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

def copy_glyph(original_font, external_font, code, dist_code):
    external_font.createChar(dist_code)
    external_font[dist_code].clear()

    # スペース文字は特別処理
    if code in [0x0020, 0x3000]:  # 半角スペース、全角スペース
        external_font[dist_code].width = original_font[code].width
        if hasattr(original_font[code], 'vwidth'):
            external_font[dist_code].vwidth = original_font[code].vwidth
    else:
        # 通常の文字はグリフをコピー
        original_font.selection.select(code)
        original_font.copy()
        external_font.selection.select(dist_code)
        external_font.paste()
        if code not in original_font:
            raise ValueError(f"Glyph for codepoint U+{code:04X}({code}) not found in original font.")
        external_font[dist_code].width = original_font[code].width

def generate_character_map(ivsMap, basemap):
    js_content  = "\nexport const ivsToExternalCharMap = {\n" + ",\n".join([f"  \"{key}\": \"{value}\"" for key, value in ivsMap.items()]) + "\n};\n"
    js_content += "\nexport const baseCharFallbackToExternalMap = {\n" + ",\n".join([f"  \"{key}\": \"{value}\"" for key, value in basemap.items()]) + "\n};\n"
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

if __name__ == "__main__":
    src_font = fontforge.open(FONT_PATH)
    covered_codepoints = list_glyphs(src_font)
    pua_strategy = analyze_vs_distribution(vs_distribution, total)
    pua_map = build_pua_mapping(covered_codepoints, pua_strategy)
    output = {
        "covered_codepoints": covered_codepoints,
        "vs_distribution": vs_distribution,
        "base_char_map": base_char_map,
        "ivs_chars": ivs_chars,
        "skip": skip,
        "total_covered": total,
        "diff": 61360 - (total + len(base_char_map)),
        "strategy": pua_strategy,
    }

    print(f"Total glyphs processed: {total_glyphs}")
    print(f"作成予定のグリフ数: {total}")
    print(f"　ベース: {len(covered_codepoints)}")
    print(f"　IVS文字: {ivs_chars}")
    print(f"　ベースマッピング: {len(base_char_map)}")
    print(f"　差分： {total_glyphs - total}")
    print(f"　処理をスキップ： {skip}")
    print(f"　ユニコードを持たない文字（対象外） {len(no_unicode_mapped)}")

    output_path = os.path.join(ROOT_DIR, 'tmp', 'covered_codepoints.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Covered codepoints written to {output_path}")

    pua_literal_map = convert_pua_mapping_to_literal_map(pua_map)
    js = generate_character_map(pua_literal_map, base_char_map)

    mapping_file_path = os.path.join(ROOT_DIR, 'src', 'utils', 'ivsCharacterMap.js')
    with open(mapping_file_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f"IVS to PUA character map written to {mapping_file_path}")

    new_font = create_new_font_from_original_font_metrics(src_font)
    pbar = ProgressBar(total=total, desc="Generate IVS External Font")
    for codepoint, glyphs in covered_codepoints.items():
        for glyph_info in glyphs:
            if glyph_info.get("base", False):
                copy_glyph(src_font, new_font, codepoint, codepoint)
            else:
                vs = glyph_info.get("vs", -1)
                glyph_name = glyph_info.get("glyph", "")
                if vs == -1:
                    raise ValueError(f"Invalid VS -1 for IVS glyph {glyph_info['glyph']}")
                ivs_sequence = chr(codepoint) + chr(vs)
                copy_glyph(src_font, new_font, glyph_name, pua_map.get((codepoint, vs)))
            pbar.update(1)

    output_woff2_path = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.woff2')
    output_ttf_path = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.ttf')

    print("WebFont形式で保存中...")
    new_font.generate(output_woff2_path)
    new_font.generate(output_ttf_path)