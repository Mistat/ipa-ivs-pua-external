import fontforge
import os
import re
import json
import argparse
from collections import defaultdict

ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ORG_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipam.ttf')
EXT_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipa-ivs-external.ttf')
JSM_PATH = os.path.join(ROOT_DIR, 'src', 'utils', 'ivsCharacterMap.js')

def parse_ts_const(ts_file, const_name):
    """ivsCharacterMap.js から export const <const_name> = { ... } を最小コストで抽出/解析する。

    - 正規表現で対象オブジェクトだけを取り出し
    - 行コメントと末尾カンマを除去
    - JSON として読み取り、失敗時はシンプルな key/value パターンでフォールバック
    """
    with open(ts_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = rf'export\s+const\s+{const_name}\s*=\s*(\{{[\s\S]*?\}})\s*;'
    match = re.search(pattern, content)
    if not match:
        return None

    obj_str = match.group(1)

    # コメントと末尾カンマの除去（最小限の変換）
    obj_str = re.sub(r'//.*?$', '', obj_str, flags=re.MULTILINE)
    obj_str = re.sub(r',(\s*[}\]])', r'\1', obj_str)

    try:
        return json.loads(obj_str)
    except json.JSONDecodeError:
        # フォールバック: "key": "value" のみ抽出
        result = {}
        for key, value in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', obj_str):
            result[key] = value
        return result

def fonts(glyphs):
    """フォントの glyph 群から (glyphname, codepoint, vs, is_alt) を列挙する。"""
    for glyph in glyphs:
        u = glyph.unicode
        if u != -1:
            yield glyph.glyphname, u, -1, False
        alt = glyph.altuni
        if not alt:
            continue
        for cp, vs, _ in alt:
            yield glyph.glyphname, cp, vs, True


def font_check(org_font, ext_font, jsm_path=JSM_PATH):
    # マップを読み込み（Python 文字列 -> 文字列）
    pua_map = parse_ts_const(jsm_path, 'ivsToExternalCharMap') or {}
    base_map = parse_ts_const(jsm_path, 'baseCharFallbackToExternalMap') or {}

    # 事前に必要な構造を構築（反復回数を削減）
    org_glyph_list = list(org_font.glyphs())
    ext_glyph_list = list(ext_font.glyphs())

    logs = []
    for g in ext_font.glyphs():
        if g.glyphname not in org_font:
            logs.append(f"Extra glyph in external font: {g.glyphname}")

    # totals are included in the returned result

    # (codepoint, vs) -> [glyph_names]
    ext_by_code = defaultdict(list)
    for gname, cp, vs, _ in fonts(ext_glyph_list):
        ext_by_code[(cp, vs)].append(gname)

    org_by_code = defaultdict(list)
    for gname, cp, vs, _ in fonts(org_glyph_list):
        org_by_code[(cp, vs)].append(gname)

    # 拡張フォントの glyphname セットと unicode 参照を構築
    ext_name_set = {g.glyphname for g in ext_glyph_list}
    ext_name_to_unicode = {g.glyphname: g.unicode for g in ext_glyph_list}

    matched = set()
    mismatch = {}
    not_found = 0
    pua_mapped = 0
    pua_mismatched = 0

    for gname, cp, vs, _ in fonts(org_glyph_list):
        if gname not in ext_name_set:
            logs.append(f"Glyph {gname} not found in external font")

        # PUA / base へのマップ適用
        pua = False
        ukey = chr(cp) + (chr(vs) if vs != -1 else '')
        if ukey in pua_map:
            pua_mapped += 1
            pua = True
            mapped = pua_map[ukey]
            # 1文字想定（PUA 側）。サロゲートペアも Python では 1 文字扱い
            cp, vs = (ord(mapped), -1) if len(mapped) == 1 else (ord(mapped[0]), ord(mapped[1]))
        elif ukey in base_map:
            pua_mapped += 1
            pua = True
            mapped = base_map[ukey]
            cp, vs = (ord(mapped), -1) if len(mapped) == 1 else (ord(mapped[0]), ord(mapped[1]))

        # 目的の (cp, vs) が拡張フォントに存在するか
        key = (cp, vs)
        if key not in ext_by_code:
            # glyph 名はあるか？（同名でコードポイントが異なる場合の処理）
            if gname in ext_name_set:
                ext_u = ext_name_to_unicode[gname]
                if cp == ext_u:
                    # VS の差異のみ
                    vs = -1
                else:
                    if (ext_u, -1) not in org_by_code:
                        not_found += 1
                        logs.append(f"Mismatch: {chr(cp)} {gname}: U+{cp:04X} vs U+{ext_u:04X} pua={pua}")
                        continue
                    matched.add(org_by_code[(ext_u, -1)][0])
                    continue
            else:
                not_found += 1
                logs.append(f"{gname}: U+{cp:04X} U+{vs:04X} pua={pua}")
                continue

        # 存在する場合、名前の一致を確認
        cand_names = ext_by_code[key]
        if gname not in cand_names:
            if gname in matched:
                # if (cp, -1) not in org_by_code:
                    logs.append(f"Already matched glyph name {gname}, but now mismatch found for U+{cp:04X}")
                # else:
                #     matched.add(org_by_code[(cp, -1)][0])
                #     continue
            mismatch[gname] = (cp, cand_names)
            if pua:
                pua_mismatched += 1
            logs.append(f"Glyph name mismatch for U+{cp:04X}: {gname} (org) vs {cand_names} (ext)")
        else:
            matched.add(gname)
    return {
        'org_total': len(org_glyph_list),
        'ext_total': len(ext_glyph_list),
        'matched_count': len(matched),
        'mismatched_count': len(mismatch),
        'not_found_count': not_found,
        'pua_mapped': pua_mapped,
        'pua_mismatched': pua_mismatched,
        'mismatches': [
            {
                'glyph_name': g,
                'codepoint': cp,
                'candidates': names,
            }
            for g, (cp, names) in mismatch.items()
        ],
        'logs': logs,
    }


def format_markdown(result):
    lines = []
    lines.append(f"# Font Check Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Original glyphs: {result['org_total']}")
    lines.append(f"- External glyphs: {result['ext_total']}")
    lines.append(f"- Matched: {result['matched_count']}")
    lines.append(f"- Mismatched: {result['mismatched_count']}")
    lines.append(f"- Not Found: {result['not_found_count']}")
    lines.append(f"- PUA Mapped: {result['pua_mapped']}")
    lines.append(f"- PUA Mismatched: {result['pua_mismatched']}")
    lines.append("")
    if result['mismatches']:
        lines.append("## Mismatches")
        lines.append("")
        for m in result['mismatches'][:200]:
            cp_hex = f"U+{m['codepoint']:04X}"
            candidates = ', '.join(m['candidates'])
            lines.append(f"- {cp_hex}: `{m['glyph_name']}` vs [{candidates}]")
        if len(result['mismatches']) > 200:
            lines.append("")
            lines.append(f"… and {len(result['mismatches']) - 200} more")
        lines.append("")
    if result['logs']:
        lines.append("## Logs")
        lines.append("")
        for log in result['logs'][:500]:
            lines.append(f"- {log}")
        if len(result['logs']) > 500:
            lines.append("")
            lines.append(f"… and {len(result['logs']) - 500} more")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Compare glyph mappings between original and external fonts.')
    parser.add_argument('--org', default=ORG_PATH, help='Path to original font (default: fonts/ipam.ttf)')
    parser.add_argument('--ext', default=EXT_PATH, help='Path to external font (default: fonts/ipa-ivs-external.ttf)')
    parser.add_argument('--map', default=JSM_PATH, help='Path to ivsCharacterMap.js (default: src/utils/ivsCharacterMap.js)')
    parser.add_argument('--markdown', action='store_true', help='Output result as Markdown')
    parser.add_argument('--json', action='store_true', help='Output result as JSON')
    args = parser.parse_args()

    org_path = args.org
    ext_path = args.ext
    map_path = args.map

    org_font = fontforge.open(org_path)
    ext_font = fontforge.open(ext_path)
    result = font_check(org_font, ext_font, map_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.markdown:
        print(format_markdown(result))
    else:
        # Plain text summary
        print(f"Original font total glyphs: {result['org_total']}")
        print(f"External font total glyphs: {result['ext_total']}")
        for log in result['logs']:
            print(log)
        print(
            f"Matched: {result['matched_count']}, Mismatched: {result['mismatched_count']}, "
            f"Not Found: {result['not_found_count']} PUA Mapped: {result['pua_mapped']} "
            f"PUA Mismatched: {result['pua_mismatched']}"
        )


if __name__ == "__main__":
    main()
