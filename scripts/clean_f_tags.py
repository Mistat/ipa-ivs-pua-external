#!/usr/bin/env python3
import json, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
WITH_F = os.path.join(ROOT, 'mji_analysis_with_f_column.json')
C_TO_F = os.path.join(ROOT, 'c_to_f_mapping.json')
F_TO_C = os.path.join(ROOT, 'mji_analysis_f_to_c_mapping.json')

def normalize_map_per_d(data):
  changed = 0
  for d_key, entry in data.items():
    if not isinstance(d_key, str) or not d_key.startswith('U+'): continue
    hexcode = d_key[2:].upper()
    cvf = entry.get('C_values_with_F', {})
    newmap = {}
    for mj, ftag in cvf.items():
      if isinstance(ftag, str) and ';' in ftag:
        tokens = [t.strip() for t in ftag.split(';') if t.strip()]
        pick = None
        for t in tokens:
          if t.upper().startswith(hexcode + '_'):
            pick = t; break
        if pick is None and tokens:
          pick = tokens[0]
        if pick != ftag:
          changed += 1
        newmap[mj] = pick
      else:
        newmap[mj] = ftag
    entry['C_values_with_F'] = newmap
  return changed

def rebuild_f_to_c(data):
  out = {}
  for d_key, entry in data.items():
    od = out.setdefault(d_key, {k: entry.get(k) for k in ('B_value','C_values')})
    odc = od.setdefault('F_to_C', {})
    for mj, ftag in entry.get('C_values_with_F', {}).items():
      if ftag:
        odc[ftag] = mj
    # copy base info if present
    for k in ('base_f_tag','base_mj','base_source'):
      if k in entry:
        od[k] = entry[k]
  return out

def is_smp_base(ftag:str)->bool:
  try:
    base = ftag.split('_',1)[0]
    return int(base,16) >= 0x10000
  except Exception:
    return False

def rebuild_c_to_f(data):
  # Build MJ -> canonical F tag using normalized per-D mappings, prefer SMP base when multiple candidates
  candidates = {}
  for d_key, entry in data.items():
    cvf = entry.get('C_values_with_F', {})
    for mj, ftag in cvf.items():
      if not ftag:
        continue
      s = candidates.setdefault(mj, set())
      s.add(ftag)
  result = {}
  for mj, fs in candidates.items():
    if len(fs) == 1:
      result[mj] = next(iter(fs))
    else:
      # prefer SMP-base tags
      smp = [f for f in fs if is_smp_base(f)]
      choice = sorted(smp if smp else list(fs))[0]
      result[mj] = choice
  return result

def main():
  with open(WITH_F,'r',encoding='utf-8') as f:
    data = json.load(f)
  changed = normalize_map_per_d(data)
  with open(WITH_F,'w',encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  print(f"✓ Cleaned {changed} F-tags in mji_analysis_with_f_column.json")
  f2c = rebuild_f_to_c(data)
  with open(F_TO_C,'w',encoding='utf-8') as f:
    json.dump(f2c, f, ensure_ascii=False, indent=2)
  print(f"✓ Rebuilt {F_TO_C}")
  c2f = rebuild_c_to_f(data)
  with open(C_TO_F,'w',encoding='utf-8') as f:
    json.dump(c2f, f, ensure_ascii=False, indent=2)
  print(f"✓ Rebuilt {C_TO_F} (prefer SMP base when conflicting)")

if __name__ == '__main__':
  main()
