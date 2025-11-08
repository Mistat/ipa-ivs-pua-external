#!/usr/bin/env python3
"""
Rebuild src/utils/ivsCharacterMap.js from ipam.ttf only (no XLSX), and emit
tmp/ivs_from_font.json for font building.

Steps
- Parse cmap format 14 for Non-Default UVS (base_cp, vs_cp) pairs.
- Resolve each pair to a glyph name via hb-shape.
- Assign PUA sequentially: BMP (E000–F8FF) then SMP (F0000–).
- Write ivsCharacterMap.js with:
  - ivsToExternalCharMap
  - cjkCompatibilityMap derived from NFKC folding
  - baseCharFallbackToExternalMap = {}
  - puaAllocationStats
"""
import os, json, subprocess, unicodedata

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FONT_PATH = os.path.join(ROOT, 'fonts', 'ipam.ttf')
IVS_JS_PATH = os.path.join(ROOT, 'src', 'utils', 'ivsCharacterMap.js')
TMP_JSON = os.path.join(ROOT, 'tmp', 'ivs_from_font.json')

def u16(b,o): return (b[o]<<8)|b[o+1]
def u24(b,o): return (b[o]<<16)|(b[o+1]<<8)|b[o+2]
def u32(b,o): return ((b[o]<<24)&0xFFFFFFFF)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3]

def find_table(buf, tag):
  num=u16(buf,4); off=12
  tag_int=(ord(tag[0])<<24)|(ord(tag[1])<<16)|(ord(tag[2])<<8)|ord(tag[3])
  for _ in range(num):
    ttag=u32(buf,off); toff=u32(buf,off+8); tlen=u32(buf,off+12)
    if ttag==tag_int: return toff,tlen
    off+=16
  return None,0

def parse_cmap14(buf, cmap_off):
  pairs=[]
  numTables=u16(buf, cmap_off+2)
  for i in range(numTables):
    rec=cmap_off+4+i*8
    subBase=cmap_off+u32(buf,rec+4)
    fmt=u16(buf,subBase)
    if fmt!=14: continue
    numVar=u32(buf,subBase+6)
    p=subBase+10
    for _ in range(numVar):
      varSel=u24(buf,p); ndOff=u32(buf,p+7); p+=11
      if ndOff:
        base=subBase+ndOff
        nrecs=u32(buf,base); q=base+4
        for _ in range(nrecs):
          uni24=u24(buf,q); q+=5
          pairs.append((uni24, varSel))
  return pairs

def cp_to_js(cp):
  if cp<=0xFFFF: return '\\u'+format(cp,'04X')
  p=cp-0x10000; hi=0xD800+(p>>10); lo=0xDC00+(p&0x3FF)
  return '\\u'+format(hi,'04X')+'\\u'+format(lo,'04X')

def vs_to_js(vs):
  if 0xE0100<=vs<=0xE01EF:
    idx=vs-0xE0100; hi=0xDB40; lo=0xDD00+idx
    return '\\u'+format(hi,'04X')+'\\u'+format(lo,'04X')
  if 0xFE00<=vs<=0xFE0F:
    return '\\u'+format(vs,'04X')
  return cp_to_js(vs)

def hb_shape_name(seq):
  out=subprocess.check_output(['hb-shape', FONT_PATH, '--no-positions', '--unicodes', ','.join(seq)]).decode().strip()
  if not out.startswith('[') or '=' not in out: return None
  inner=out[1:-1]; first=inner.split('|',1)[0]
  return first.split('=',1)[0]

def main():
  os.makedirs(os.path.join(ROOT,'tmp'), exist_ok=True)
  buf=open(FONT_PATH,'rb').read()
  cmap_off,_=find_table(buf,'cmap')
  if not cmap_off: raise SystemExit('cmap not found in ipam.ttf')
  pairs=parse_cmap14(buf, cmap_off)
  recs=[]
  for base,vs in pairs:
    if not (0xE0100<=vs<=0xE01EF or 0xFE00<=vs<=0xFE0F):
      continue
    key=cp_to_js(base)+vs_to_js(vs)
    try:
      gname=hb_shape_name([f'U+{base:X}', f'U+{vs:X}'])
    except subprocess.CalledProcessError:
      gname=None
    if not gname: continue
    recs.append({'ivs_literal': key, 'base_cp': base, 'vs_cp': vs, 'glyph_name': gname})
  # dedup + order
  uniq={}
  for r in recs: uniq[r['ivs_literal']]=r
  recs=list(uniq.values())
  recs.sort(key=lambda r:(r['vs_cp'], r['base_cp'], r['glyph_name']))

  # Assign PUA
  out=[]; bmp=0xE000; smp=0xF0000
  def esc(cp):
    if cp<=0xFFFF: return '\\u'+format(cp,'04X')
    p=cp-0x10000; hi=0xD800+(p>>10); lo=0xDC00+(p&0x3FF)
    return '\\u'+format(hi,'04X')+'\\u'+format(lo,'04X')
  for r in recs:
    if bmp<=0xF8FF: cp=bmp; bmp+=1
    else: cp=smp; smp+=1
    out.append({**r,'pua':esc(cp)})

  with open(TMP_JSON,'w',encoding='utf-8') as f:
    json.dump({'records': out}, f, ensure_ascii=False, indent=2)
  print(f"✓ Wrote {TMP_JSON} with {len(out)} records")

  # Write JS file
  js=[]
  js.append("// IVS文字マッピング定義（generated from font-only）\n")
  js.append("export function convertSMPToString(codePoint) {\n  if (codePoint > 0xFFFF) {\n    const high = Math.floor((codePoint - 0x10000) / 0x400) + 0xD800;\n    const low = ((codePoint - 0x10000) % 0x400) + 0xDC00;\n    return String.fromCharCode(high, low);\n  }\n  return String.fromCharCode(codePoint);\n}\n")
  js.append("export function getPUAPlane(puaChar) {\n  const codePoint = puaChar.codePointAt(0);\n  if (codePoint >= 0xE000 && codePoint <= 0xF8FF) return 'BMP';\n  if (codePoint >= 0xF0000 && codePoint <= 0xFFFFD) return 'SMP_P15';\n  if (codePoint >= 0x100000 && codePoint <= 0x10FFFD) return 'SMP_P16';\n  return 'UNKNOWN';\n}\n")
  js.append("export function convertIVSText(text) {\n  const ivsPattern = /(?:[\\u3400-\\u9FFF]|[\\uD800-\\uDBFF][\\uDC00-\\uDFFF])[\\uDB40-\\uDB7F][\\uDC00-\\uDFFF]/g;\n  return text.replace(ivsPattern, match => ivsToExternalCharMap[match] || match);\n}\n")
  js.append("export const ivsToExternalCharMap = {\n")
  for r in out:
    js.append(f"  '{r['ivs_literal']}': '{r['pua']}',\n")
  if js[-1].endswith(',\n'): js[-1]=js[-1][:-2]+"\n"
  js.append("};\n")
  # cjkCompatibilityMap via NFKC
  js.append("export const cjkCompatibilityMap = {\n")
  compat=[]
  for cp in list(range(0xF900,0xFB00))+list(range(0x2F800,0x2FA20)):
    ch=chr(cp); nfkc=unicodedata.normalize('NFKC', ch)
    if nfkc!=ch:
      def escs(s): return ''.join('\\u'+format(ord(c),'04X') for c in s)
      compat.append((cp, escs(ch), escs(nfkc)))
  for _,k,v in compat:
    js.append(f"  '{k}': '{v}',\n")
  if js[-1].endswith(',\n'): js[-1]=js[-1][:-2]+"\n"
  js.append("};\n")
  js.append("export const baseCharFallbackToExternalMap = {};\n")
  total=len(out); bmp_used=min(total, 0xF8FF-0xE000+1); smp_used=max(0,total-bmp_used)
  js.append("export const puaAllocationStats = {\n")
  js.append("  strategy: 'sequential',\n")
  js.append(f"  bmpPUA: {{ allocated: {bmp_used}, capacity: 6400, range: '0xE000-0xF8FF' }},\n")
  js.append(f"  smpPUA: {{ allocated: {smp_used}, capacity: 65534, range: '0xF0000-0xFFFFD' }},\n")
  js.append(f"  totalCharacters: {total}\n")
  js.append("};\n")
  os.makedirs(os.path.dirname(IVS_JS_PATH), exist_ok=True)
  open(IVS_JS_PATH,'w',encoding='utf-8').write(''.join(js))
  print(f"✓ Rewrote {IVS_JS_PATH}")

if __name__ == '__main__':
  main()
