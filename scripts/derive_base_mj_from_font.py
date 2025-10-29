#!/usr/bin/env python3
"""
Derive base_mj/base_f_tag for each U+XXXX by inspecting the actual font cmap.

Policy:
 1) If cmap format 14 (UVS) has a mapping for the base codepoint with a VS whose
    glyph equals the default cmap glyph, adopt that VS (e.g., E0100/E0101/...).
 2) If not found, prefer E0100 when present among candidates.
 3) Else, prefer the VS indicated by B_value if present.
 4) Else, choose the smallest VS among candidates.

Updates both:
 - mji_analysis_with_f_column.json (MJ -> F mapping inside each entry)
 - mji_analysis_f_to_c_mapping.json (F -> MJ mapping inside each entry)

If fontTools is unavailable or font lacks format 14, the script falls back to 2)–4).
"""
import json
import os
import sys

ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONT_PATH = os.path.join(ROOT_DIR, 'fonts', 'ipam.ttf')
WITH_F_JSON = os.path.join(ROOT_DIR, 'mji_analysis_with_f_column.json')
F_TO_C_JSON = os.path.join(ROOT_DIR, 'mji_analysis_f_to_c_mapping.json')

def load_font():
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(FONT_PATH)
        return tt
    except Exception as e:
        print(f"WARN: fontTools or font not available ({e}); falling back to heuristic (no UVS check).")
        return None

def get_default_cmap(tt):
    if tt is None:
        return {}
    # getBestCmap selects a reasonable Unicode cmap (format 12 preferred if present)
    try:
        return tt.getBestCmap() or {}
    except Exception:
        return {}

def get_uvs_map(tt):
    if tt is None:
        return None
    try:
        cmap = tt['cmap']
        for sub in cmap.tables:
            if getattr(sub, 'format', None) == 14:
                return sub  # has uvsDict
        return None
    except Exception:
        return None

def vs_to_codepoint(vs_tag: str):
    try:
        if isinstance(vs_tag, str) and vs_tag.upper().startswith('E'):
            return int(vs_tag[1:], 16)
    except Exception:
        pass
    return None

def vs_rank(vs_tag: str):
    try:
        return int(vs_tag[1:], 16) if vs_tag and vs_tag.upper().startswith('E') else 1<<30
    except Exception:
        return 1<<30

def bvalue_vs(bval: str):
    if not isinstance(bval, str):
        return None
    for ch in bval:
        cp = ord(ch)
        if 0xE0100 <= cp <= 0xE01EF:
            return f"E0{cp - 0xE0000:03X}"
    return None

def main():
    # Load JSONs
    with open(WITH_F_JSON, 'r', encoding='utf-8') as f:
        with_f = json.load(f)
    with open(F_TO_C_JSON, 'r', encoding='utf-8') as f:
        f_to_c = json.load(f)

    # Load font
    tt = load_font()
    dmap = get_default_cmap(tt)
    uvs = get_uvs_map(tt)

    changed = 0
    total = 0

    for ukey, entry in with_f.items():
        if not (isinstance(ukey, str) and ukey.startswith('U+') and isinstance(entry, dict)):
            continue
        total += 1
        try:
            cp = int(ukey[2:], 16)
        except Exception:
            continue

        cvf = entry.get('C_values_with_F', {})  # MJ -> F
        if not isinstance(cvf, dict) or not cvf:
            continue

        # Build helpers
        # map VS tag to (F, MJ)
        vs_to_pair = {}
        for mj, ftag in cvf.items():
            if isinstance(ftag, str) and '_' in ftag:
                vs = ftag.split('_', 1)[1]
                vs_to_pair[vs] = (ftag, mj)

        selected = None
        source = None
        # Step 1: Try matching VS glyph to default glyph in the font
        try:
            def_name = dmap.get(cp)
            if def_name and uvs is not None and hasattr(uvs, 'uvsDict'):
                for vs, pair in vs_to_pair.items():
                    vscp = vs_to_codepoint(vs)
                    if vscp is None:
                        continue
                    vsdict = uvs.uvsDict.get(vscp)
                    if not vsdict:
                        continue
                    uvs_mappings = vsdict.get('uvsMappings', {})
                    gname = uvs_mappings.get(cp)
                    if gname and gname == def_name:
                        selected = pair  # (ftag, mj)
                        source = 'uvs'
                        break
        except Exception:
            pass

        # Step 2: Prefer E0100 if present
        if selected is None and 'E0100' in vs_to_pair:
            selected = vs_to_pair['E0100']
            source = 'e0100'

        # Step 3: Use B_value VS if present
        if selected is None:
            bvs = bvalue_vs(entry.get('B_value'))
            if bvs in vs_to_pair:
                selected = vs_to_pair[bvs]
                source = 'b_value'

        # Step 4: Min VS
        if selected is None:
            best = min(vs_to_pair.items(), key=lambda kv: vs_rank(kv[0]))
            selected = best[1]
            source = 'min'

        new_base_f, new_base_mj = selected

        # If changed, update both JSONs
        if entry.get('base_f_tag') != new_base_f or entry.get('base_mj') != new_base_mj:
            entry['base_f_tag'] = new_base_f
            entry['base_mj'] = new_base_mj
            entry['base_source'] = source
            # Update twin entry in f_to_c JSON
            f_entry = f_to_c.get(ukey)
            if isinstance(f_entry, dict):
                f_entry['base_f_tag'] = new_base_f
                f_entry['base_mj'] = new_base_mj
                f_entry['base_source'] = source
            changed += 1

    # Save back
    with open(WITH_F_JSON, 'w', encoding='utf-8') as f:
        json.dump(with_f, f, ensure_ascii=False, indent=2)
    with open(F_TO_C_JSON, 'w', encoding='utf-8') as f:
        json.dump(f_to_c, f, ensure_ascii=False, indent=2)

    print(f"✓ Derived base_mj from font cmap: {changed} updated out of {total} entries.")
    if tt is None:
        print("Note: fontTools/UVS not available. Used heuristic (E0100/B_value/minVS).")

if __name__ == '__main__':
    main()
