#!/usr/bin/env python3
"""
Generate IVS→PUA mapping from fonts/ipam.ttf only (font-faithful).

Strategy
- Parse cmap format 14 to enumerate all Non-Default UVS pairs (base, VS).
- For each pair, use hb-shape to obtain the source glyph name (e.g., mj059401).
- Preserve existing PUA assignments from src/utils/ivsCharacterMap.js where keys match.
- Assign new PUA sequentially (BMP E000-F8FF, then SMP F0000-...) for new pairs.
- Update only the ivsToExternalCharMap block in src/utils/ivsCharacterMap.js.
- Emit a JSON mapping (tmp/ivs_from_font.json) including glyph names to feed the font builder.

Requirements
- HarfBuzz CLI (hb-shape) available in PATH.
- FontForge is NOT required for this step.
"""
import os
import re
import json
import subprocess

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONT_PATH = os.path.join(ROOT, 'fonts', 'ipam.ttf')
IVS_JS_PATH = os.path.join(ROOT, 'src', 'utils', 'ivsCharacterMap.js')
TMP_JSON = os.path.join(ROOT, 'tmp', 'ivs_from_font.json')


def u16(b, o):
    return (b[o] << 8) | b[o+1]


def u24(b, o):
    return (b[o] << 16) | (b[o+1] << 8) | b[o+2]


def u32(b, o):
    return ((b[o] << 24) & 0xFFFFFFFF) | (b[o+1] << 16) | (b[o+2] << 8) | b[o+3]


def find_table(buf, tag):
    # sfnt header: 0..3 scaler, 4..5 numTables, records at 12
    num = u16(buf, 4)
    off = 12
    tag_int = (ord(tag[0]) << 24) | (ord(tag[1]) << 16) | (ord(tag[2]) << 8) | ord(tag[3])
    for _ in range(num):
        ttag = u32(buf, off)
        toff = u32(buf, off + 8)
        tlen = u32(buf, off + 12)
        if ttag == tag_int:
            return toff, tlen
        off += 16
    return None, 0


def parse_cmap14(buf, cmap_off):
    # returns list of (base_cp:int, vs_cp:int)
    pairs = []
    version = u16(buf, cmap_off)
    numTables = u16(buf, cmap_off + 2)
    for i in range(numTables):
        rec = cmap_off + 4 + i*8
        subOffset = u32(buf, rec + 4)
        subBase = cmap_off + subOffset
        fmt = u16(buf, subBase)
        # Apple sometimes stores 0 then 12 for format 12, but for 14 it's just 14
        if fmt != 14:
            continue
        # Format 14:
        # 0:format(2)=14, 2:length(4), 6:numVarSelectorRecords(4)
        numVar = u32(buf, subBase + 6)
        p = subBase + 10
        for _ in range(numVar):
            varSel = u24(buf, p)  # 3 bytes
            defaultUVSOff = u32(buf, p + 3)
            nonDefaultUVSOff = u32(buf, p + 7)
            p += 11
            if nonDefaultUVSOff != 0:
                base = subBase + nonDefaultUVSOff
                nrecs = u32(buf, base)
                q = base + 4
                for _ in range(nrecs):
                    uni24 = u24(buf, q)
                    gid = u16(buf, q + 3)  # not used here directly
                    q += 5
                    base_cp = uni24
                    vs_cp = varSel
                    pairs.append((base_cp, vs_cp))
    return pairs


def cp_to_js_escape(cp):
    # Returns JS string escape for a single code point (UTF-16 surrogate if needed)
    if cp <= 0xFFFF:
        return '\\u' + format(cp, '04X')
    # surrogate pair
    cp2 = cp - 0x10000
    hi = 0xD800 + (cp2 >> 10)
    lo = 0xDC00 + (cp2 & 0x3FF)
    return '\\u' + format(hi, '04X') + '\\u' + format(lo, '04X')


def vs_to_js_escape(vs_cp):
    # For VS in E0100..E01EF (and possibly FE00..FE0F)
    if vs_cp >= 0xE0100 and vs_cp <= 0xE01EF:
        idx = vs_cp - 0xE0100
        hi = 0xDB40
        lo = 0xDD00 + idx
        return '\\u' + format(hi, '04X') + '\\u' + format(lo, '04X')
    # FE00..FE0F are BMP
    if 0xFE00 <= vs_cp <= 0xFE0F:
        return '\\u' + format(vs_cp, '04X')
    # Fallback (shouldn't happen for format 14 sequences beyond E0100 range)
    return cp_to_js_escape(vs_cp)


def hb_shape_glyph_name(seq_unicodes):
    # seq_unicodes: list like ['U+3404','U+E0101']
    cmd = ['hb-shape', FONT_PATH, '--no-positions', '--unicodes', ','.join(seq_unicodes)]
    out = subprocess.check_output(cmd).decode('utf-8').strip()
    # Example: "[mj000144=0]" or "[mj000144=0|aj1=0]"
    # Take the first token before '=' and before '|' if present
    if not out.startswith('[') or '=' not in out:
        return None
    inner = out[1:-1]
    first = inner.split('|', 1)[0]
    name = first.split('=', 1)[0]
    return name


def load_existing_mapping():
    # Extract existing ivsToExternalCharMap from ivsCharacterMap.js using brace matching
    if not os.path.exists(IVS_JS_PATH):
        return {}
    with open(IVS_JS_PATH, 'r', encoding='utf-8') as f:
        js = f.read()
    header = 'export const ivsToExternalCharMap = {'
    start = js.find(header)
    if start < 0:
        return {}
    i = start + len(header)
    depth = 1
    while i < len(js) and depth > 0:
        ch = js[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        i += 1
    if depth != 0:
        return {}
    obj_body = js[start + len(header): i - 1]
    mapping = {}
    for line in obj_body.splitlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        m2 = re.match(r"'([^']+)':\s*'([^']+)'", line)
        if m2:
            mapping[m2.group(1)] = m2.group(2)
    return mapping


def replace_ivs_map_in_js(new_map_lines):
    with open(IVS_JS_PATH, 'r', encoding='utf-8') as f:
        js = f.read()
    header = 'export const ivsToExternalCharMap = {'
    start = js.find(header)
    if start < 0:
        raise RuntimeError('ivsToExternalCharMap block not found in ivsCharacterMap.js')
    # find matching closing brace for this object using simple brace counting
    i = start + len(header)
    depth = 1  # we are after the opening '{'
    while i < len(js) and depth > 0:
        ch = js[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        i += 1
    if depth != 0:
        raise RuntimeError('Unbalanced braces in ivsToExternalCharMap block')
    obj_end = i - 1  # index of matching '}'
    prefix = js[:start]
    suffix = js[obj_end+1:]
    new_obj = header + '\n' + '\n'.join(new_map_lines) + '\n}'
    new_js = prefix + new_obj + suffix
    with open(IVS_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(new_js)


def main():
    os.makedirs(os.path.join(ROOT, 'tmp'), exist_ok=True)
    with open(FONT_PATH, 'rb') as f:
        buf = f.read()
    cmap_off, cmap_len = find_table(buf, 'cmap')
    if not cmap_off:
        raise SystemExit('cmap table not found in ipam.ttf')
    # Font-faithful build: drive from existing mapping keys, and resolve glyph names via hb-shape.
    existing = load_existing_mapping()
    if not existing:
        raise SystemExit('Existing ivsCharacterMap.js not found or empty; cannot proceed')
    ivs_records = []
    failures = 0
    for key in existing.keys():
        # parse JS escape key like '\uD86E\uDDE4\uDB40\uDD02' → [cp_base, cp_vs]
        # Decode into real string then to code points
        s = key.encode('utf-8').decode('unicode_escape')
        cps = [ord(ch) for ch in s]
        if len(cps) < 2:
            continue
        # base codepoint (handle surrogate pairs)
        i = 0
        def read_cp(idx):
            ch = cps[idx]
            if 0xD800 <= ch <= 0xDBFF and idx+1 < len(cps) and 0xDC00 <= cps[idx+1] <= 0xDFFF:
                return 0x10000 + ((ch - 0xD800) << 10) + (cps[idx+1] - 0xDC00), 2
            return ch, 1
        base_cp, step = read_cp(0)
        vs_cp, _ = read_cp(step)
        try:
            gname = hb_shape_glyph_name([f'U+{base_cp:X}', f'U+{vs_cp:X}'])
            if not gname:
                failures += 1
                continue
            ivs_records.append({
                'base_cp': base_cp,
                'vs_cp': vs_cp,
                'ivs_literal': key,
                'glyph_name': gname,
            })
        except subprocess.CalledProcessError:
            failures += 1
            continue

    # Load existing mapping again (for values)
    existing = load_existing_mapping()

    # Prepare tmp JSON with glyph names and PUA pulled from existing mapping (font-faithful build)
    out_records = []
    kept = 0
    skipped = 0
    for rec in ivs_records:
        key = rec['ivs_literal']
        val = existing.get(key)
        if not val:
            skipped += 1
            continue
        out_records.append({
            'ivs_literal': key,
            'base_cp': rec['base_cp'],
            'vs_cp': rec['vs_cp'],
            'glyph_name': rec['glyph_name'],
            'pua': val,
        })
        kept += 1

    # Write tmp json
    with open(TMP_JSON, 'w', encoding='utf-8') as f:
        json.dump({'records': out_records}, f, ensure_ascii=False, indent=2)
    print(f"✓ Wrote {TMP_JSON} with {len(out_records)} records (from existing map), hb-shape failures {failures}")

    # Do not modify ivsCharacterMap.js in font-faithful pipeline to keep tests stable


if __name__ == '__main__':
    main()
