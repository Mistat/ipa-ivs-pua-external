// Verify display mapping around U+2B9E4 (𫧤):
// - IVS E0100 (𫧤󠄀) corresponds to MJ059399 and is copied to external PUA
// - Base character (𫧤) corresponds to MJ059400 in ipam.ttf

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { ivsToExternalCharMap } from '../src/utils/ivsCharacterMap.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function u8(p) { const ab = fs.readFileSync(p); return new Uint8Array(ab.buffer, ab.byteOffset, ab.byteLength); }
function u16(b,o){ return (b[o]<<8)|b[o+1]; }
function u24(b,o){ return (b[o]<<16)|(b[o+1]<<8)|b[o+2]; }
function u32(b,o){ return ((b[o]<<24)>>>0)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3]; }
function tag4(s){ return s.charCodeAt(0)<<24|s.charCodeAt(1)<<16|s.charCodeAt(2)<<8|s.charCodeAt(3); }

function findTable(font, tagStr) {
  const tag = tag4(tagStr);
  const num = u16(font, 4);
  let off = 12;
  for (let i=0;i<num;i++) {
    const ttag=u32(font,off); const toff=u32(font,off+8); const tlen=u32(font,off+12);
    if (ttag===tag) return { offset: toff, length: tlen };
    off+=16;
  }
  return null;
}

function parseCmapCpToGID(font) {
  const tbl = findTable(font, 'cmap');
  if (!tbl) throw new Error('cmap not found');
  const base = tbl.offset;
  const numTables = u16(font, base+2);
  let f4=null, f12=null;
  for (let i=0;i<numTables;i++) {
    const rec = base+4+i*8;
    const platformID = u16(font, rec);
    const subBase = base + u32(font, rec+4);
    const fmt = u16(font, subBase);
    if (fmt===12 || (fmt===0 && u16(font, subBase+2)===12)) f12={ base: subBase };
    else if (fmt===4 && platformID===3) f4={ base: subBase };
  }
  return function cpToGID(cp){
    if (cp>0xFFFF && f12) {
      const b=f12.base; const n=u32(font,b+12); let lo=0, hi=n-1, off=b+16;
      while(lo<=hi){ const mid=(lo+hi)>>1; const m=off+mid*12; const start=u32(font,m), end=u32(font,m+4);
        if (cp<start) hi=mid-1; else if (cp>end) lo=mid+1; else return u32(font,m+8)+(cp-start);
      }
    }
    if (cp<=0xFFFF && f4) {
      const b=f4.base; const segCount=u16(font,b+6)/2; const endOff=b+14; const startOff=endOff+segCount*2+2; const idDeltaOff=startOff+segCount*2; const idRangeOffsetOff=idDeltaOff+segCount*2;
      let lo=0, hi=segCount-1; while(lo<=hi){ const mid=(lo+hi)>>1; const end=u16(font,endOff+mid*2); if (cp>end) lo=mid+1; else hi=mid-1; }
      const i=lo; if (i>=segCount) return 0; const end=u16(font,endOff+i*2); const start=u16(font,startOff+i*2); if (cp<start||cp>end) return 0;
      const idDelta=u16(font,idDeltaOff+i*2); const idRangeOffset=u16(font,idRangeOffsetOff+i*2);
      if (idRangeOffset===0) return (cp+idDelta)&0xFFFF;
      const roff=idRangeOffsetOff+i*2+idRangeOffset; const idx=(cp-start)*2; const glyphIndex=u16(font, roff+idx); if (glyphIndex===0) return 0; return (glyphIndex+idDelta)&0xFFFF;
    }
    return 0;
  }
}

function getGIDFromUVS(font, baseCP, vsCP) {
  const cmap = findTable(font, 'cmap'); if (!cmap) throw new Error('cmap not found');
  const base=cmap.offset; const num=u16(font, base+2);
  for (let i=0;i<num;i++) {
    const sub=base+u32(font, base+4+i*8+4); const fmt=u16(font, sub);
    if (fmt===14){ const numVar=u32(font, sub+6); let p=sub+10; for(let j=0;j<numVar;j++){ const varSel=u24(font,p); const defOff=u32(font,p+3); const ndOff=u32(font,p+7); p+=11; if (varSel===vsCP){ if (ndOff){ const ndBase=sub+ndOff; const count=u32(font, ndBase); let q=ndBase+4; for(let k=0;k<count;k++){ const uni=u24(font,q); const gid=u16(font,q+3); if (uni===baseCP) return gid; q+=5; } } } }
    }
  }
  return 0;
}

function getGlyphSlice(font, gid) {
  const head=findTable(font,'head'); const maxp=findTable(font,'maxp'); const loca=findTable(font,'loca'); const glyf=findTable(font,'glyf');
  if (!head||!maxp||!loca||!glyf) throw new Error('required tables missing');
  const indexToLocFormat=u16(font, head.offset+50);
  const numGlyphs=u16(font, maxp.offset+4);
  const glyphOffset=(i)=>{ if (indexToLocFormat===0){ return u16(font, loca.offset+i*2)*2; } else { return u32(font, loca.offset+i*4); } };
  const start = glyf.offset + glyphOffset(gid);
  const end = glyf.offset + (gid+1 < numGlyphs ? glyphOffset(gid+1) : glyf.length);
  return font.slice(start, end);
}

function int16s(b,o){ let v=(b[o]<<8)|b[o+1]; if (v&0x8000) v= -((~v+1)&0xFFFF); return v; }
function decodeSimpleGlyfPoints(slice) {
  const nContours = (slice[0]<<8)|slice[1];
  if (nContours < 0) return { simple:false };
  const xMin = int16s(slice,2), yMin=int16s(slice,4), xMax=int16s(slice,6), yMax=int16s(slice,8);
  const endPts = []; let p=10;
  for (let i=0;i<nContours;i++){ endPts.push((slice[p]<<8)|slice[p+1]); p+=2; }
  const instructionLength = (slice[p]<<8)|slice[p+1]; p+=2; p+=instructionLength;
  const pointCount = endPts[endPts.length-1] + 1;
  const flags = new Uint8Array(pointCount); let i=0;
  while (i<pointCount) { const f=slice[p++]; let reps=1; if (f & 0x08) reps = slice[p++]+1; for (let r=0;r<reps&&i<pointCount;r++) flags[i++]=f; }
  const xs=new Int32Array(pointCount); let x=0;
  for (let j=0;j<pointCount;j++){ const f=flags[j]; let dx=0; if (f&0x02){ const b=slice[p++]; dx=(f&0x10)?b:-b; } else { if (f&0x10) dx=0; else { dx=int16s(slice,p); p+=2; } } x+=dx; xs[j]=x; }
  const ys=new Int32Array(pointCount); let y=0;
  for (let j=0;j<pointCount;j++){ const f=flags[j]; let dy=0; if (f&0x04){ const b=slice[p++]; dy=(f&0x20)?b:-b; } else { if (f&0x20) dy=0; else { dy=int16s(slice,p); p+=2; } } y+=dy; ys[j]=y; }
  const points=new Array(pointCount); for (let j=0;j<pointCount;j++) points[j]={ x:xs[j], y:ys[j], on: !!(flags[j]&1) };
  return { simple:true, contours:nContours, xMin,yMin,xMax,yMax, points };
}

function parsePost(font){
  const post = findTable(font, 'post'); if (!post) throw new Error('post not found');
  const b=post.offset; const version=u32(font,b);
  if (version!==0x00020000) throw new Error('post version not supported: 0x'+version.toString(16));
  const numGlyphs=u16(font, b+32);
  const glyphNameIndexOff=b+34;
  const nameIndex = new Uint16Array(numGlyphs);
  for (let i=0;i<numGlyphs;i++) nameIndex[i]=u16(font, glyphNameIndexOff+i*2);
  let p = glyphNameIndexOff + numGlyphs*2;
  const customNames=[];
  // Build custom names array (for indices >= 258)
  // We don't know count upfront; collect until we refer to all indices used
  const needs = new Set();
  for (let i=0;i<numGlyphs;i++) if (nameIndex[i] >= 258) needs.add(nameIndex[i]-258);
  const maxNeed = needs.size ? Math.max(...needs) : -1;
  for (let i=0;i<=maxNeed;i++){
    const len = font[p++];
    const s = new TextDecoder('ascii').decode(font.slice(p, p+len));
    p += len;
    customNames.push(s);
  }
  const macStandard = [];
  // We don't actually need Mac standard names, because we expect mjXXXXX which are custom (>=258)
  return function glyphName(gid){
    const idx = nameIndex[gid];
    if (idx >= 258) return customNames[idx-258] || null;
    return null; // not needed
  }
}

describe('U+2B9E4 display mapping around MJ059399/MJ059400', () => {
  const baseFont = u8(path.join(__dirname, '..', 'fonts', 'ipam.ttf'));
  const extFont = u8(path.join(__dirname, '..', 'fonts', 'ipa-ivs-external.ttf'));

  test('𫧤󠄀 (U+2B9E4 E0100) maps to mj059399 and is copied to external PUA', () => {
    const key = String.fromCodePoint(0x2B9E4) + String.fromCharCode(0xDB40, 0xDD00); // E0100
    const pua = ivsToExternalCharMap[key];
    expect(pua).toBeDefined();

    // In base font, get GID and glyph name for UVS E0100
    const gidBase = getGIDFromUVS(baseFont, 0x2B9E4, 0xE0100);
    expect(gidBase).not.toBe(0);
    const nameOf = parsePost(baseFont);
    const name = nameOf(gidBase);
    expect(name).toBe('mj059399');

    // External font: the PUA codepoint should carry the exact same outl__tests__/mji_2B9E4_display.test.jsine
    const cp = pua.codePointAt(0);
    const cpToGID = parseCmapCpToGID(extFont);
    const gidExt = cpToGID(cp);
    expect(gidExt).not.toBe(0);
    const sliceBase = getGlyphSlice(baseFont, gidBase);
    const sliceExt = getGlyphSlice(extFont, gidExt);
    expect(sliceExt.length).toBeGreaterThan(0);
    // Strict compare; fallback to outline equivalence if bytes differ
    if (Buffer.compare(Buffer.from(sliceExt), Buffer.from(sliceBase)) !== 0) {
      const a = decodeSimpleGlyfPoints(sliceBase);
      const b = decodeSimpleGlyfPoints(sliceExt);
      expect(a.simple && b.simple).toBe(true);
      expect(a.contours).toBe(b.contours);
      expect([a.xMin,a.yMin,a.xMax,a.yMax]).toEqual([b.xMin,b.yMin,b.xMax,b.yMax]);
      expect(a.points.length).toBe(b.points.length);
      for (let i=0;i<a.points.length;i++) expect(a.points[i]).toEqual(b.points[i]);
    }
  });

  test('𫧤 (U+2B9E4) base character is mj059400 in ipam.ttf', () => {
    const cpToGID = parseCmapCpToGID(baseFont);
    const gid = cpToGID(0x2B9E4);
    expect(gid).not.toBe(0);
    const nameOf = parsePost(baseFont);
    const name = nameOf(gid);
    expect(name).toBe('mj059400');
  });
});

// Bulk verification for many MJ glyphs referenced in ivsCharacterMap.js comments.
// For each MJ code below, we locate the corresponding IVS→PUA line in
// src/utils/ivsCharacterMap.js (by parsing the source file to keep the MJ comment),
// then verify:
//  - Base font (ipam.ttf) has a Non-Default UVS entry mapping that IVS to a glyph
//    and the glyph name in 'post' table matches the expected mjXXXXX.
//  - External font (ipa-ivs-external.ttf) has the PUA codepoint present.

function parseIvsMapComments() {
  const jsPath = path.join(__dirname, '..', 'src', 'utils', 'ivsCharacterMap.js');
  const src = fs.readFileSync(jsPath, 'utf-8');
  const lines = src.split(/\r?\n/);
  const out = new Map(); // MJxxxxx -> { ivsLiteral, pua }
  const re = /'([^']+)':\s*'([^']+)',\s*\/\/\s*(MJ\d{6})/;
  for (const line of lines) {
    const m = line.match(re);
    if (m) {
      const ivsLiteral = m[1];
      const pua = m[2];
      const mj = m[3];
      out.set(mj, { ivsLiteral, pua });
    }
  }
  return out;
}

function decodeEscapedJS(jsEscaped) {
  // jsEscaped like "\\uD86E\\uDDE4\\uDB40\\uDD02" → string with surrogate pairs
  return jsEscaped.replace(/\\u([0-9A-Fa-f]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
}

function ivsToBaseAndVS(ivsStr) {
  // Return { baseCP, vsCP } from actual string
  // base may be SMP (surrogate pair). VS is either E0100..E01EF (DB40/DDxx) or FE00..FE0F.
  if (!ivsStr || ivsStr.length < 2) return { baseCP: 0, vsCP: 0 };
  let i = 0;
  const c0 = ivsStr.charCodeAt(0);
  let baseCP;
  if (c0 >= 0xD800 && c0 <= 0xDBFF && ivsStr.length >= 2) {
    const c1 = ivsStr.charCodeAt(1);
    baseCP = 0x10000 + ((c0 - 0xD800) << 10) + (c1 - 0xDC00);
    i = 2;
  } else {
    baseCP = c0;
    i = 1;
  }
  let vsCP = 0;
  if (ivsStr.length >= i + 2) {
    const h = ivsStr.charCodeAt(i);
    const l = ivsStr.charCodeAt(i + 1);
    if (h === 0xDB40 && l >= 0xDD00 && l <= 0xDDEF) {
      vsCP = 0xE0100 + (l - 0xDD00);
      return { baseCP, vsCP };
    }
  }
  const v = ivsStr.charCodeAt(i);
  if (v >= 0xFE00 && v <= 0xFE0F) vsCP = v;
  return { baseCP, vsCP };
}

describe('Bulk MJ glyph checks via ivsCharacterMap.js comments', () => {
  const extFontPath = path.join(__dirname, '..', 'fonts', 'ipa-ivs-external.ttf');
  const baseFontPath = path.join(__dirname, '..', 'fonts', 'ipam.ttf');
  const extFont = u8(extFontPath);
  const baseFont = u8(baseFontPath);
  const cpToGIDExt = parseCmapCpToGID(extFont);
  const mjMap = parseIvsMapComments();

  const targets = [
    'MJ021335','MJ023164','MJ030293','MJ030309','MJ030319','MJ030387','MJ030550','MJ030742','MJ030927','MJ030984',
    'MJ031729','MJ031960','MJ032098','MJ032337','MJ032503','MJ032961','MJ032991','MJ033194','MJ033196','MJ033205',
    'MJ033579','MJ033817','MJ034186','MJ034313','MJ034543','MJ034827','MJ035471','MJ035828','MJ036334','MJ036351',
    'MJ037889','MJ037939','MJ038052','MJ038223','MJ038344','MJ038377','MJ038420','MJ038425','MJ039218','MJ039442',
    'MJ041409','MJ042964','MJ042970','MJ042975','MJ042980','MJ043007','MJ043035','MJ043047','MJ043051','MJ043063',
    'MJ043075','MJ043092','MJ043175','MJ043243','MJ043547','MJ043732','MJ044738','MJ045111','MJ045235','MJ045558',
    'MJ046224','MJ046309','MJ046537','MJ046954','MJ047032','MJ047141','MJ047259','MJ047772','MJ047986','MJ048162',
    'MJ048374','MJ048486','MJ048895','MJ049239','MJ049294','MJ049590','MJ049742','MJ049758','MJ050768','MJ050780',
    'MJ050822','MJ050868','MJ050877','MJ050933','MJ050936','MJ050944','MJ050956','MJ050991','MJ051009','MJ051044',
    'MJ051051','MJ051061','MJ051123','MJ051167','MJ051172','MJ052666','MJ053282','MJ053809','MJ053861','MJ053865',
    'MJ053980','MJ054089','MJ054116','MJ054143','MJ055217','MJ055265','MJ055301','MJ055928','MJ056431','MJ056830',
    'MJ056893','MJ056904','MJ056928','MJ056959','MJ056988','MJ056994','MJ057019','MJ057121','MJ057181','MJ057198',
    'MJ057235','MJ057266','MJ057285','MJ057447','MJ057482','MJ057545','MJ057641','MJ057782','MJ057879','MJ057891',
    'MJ057892','MJ057949','MJ057999','MJ058133','MJ058240','MJ058258','MJ058376','MJ058705','MJ058708','MJ058710',
    'MJ058869','MJ059002','MJ059016','MJ059171','MJ059252','MJ059329','MJ059399','MJ059400','MJ059483','MJ059514',
    'MJ059575','MJ059601','MJ059636','MJ059641','MJ059747','MJ059817','MJ059821','MJ059831','MJ059846','MJ059876',
    'MJ059996','MJ060113','MJ060245','MJ060253','MJ068061','MJ068075','MJ068076','MJ068078','MJ068080','MJ068081',
    'MJ068083','MJ068086','MJ068087','MJ068088','MJ068090','MJ068091','MJ068092','MJ068093','MJ068095','MJ068097',
    'MJ068098','MJ068099','MJ068100'
  ];

  test('all target MJs exist in ivsCharacterMap.js', () => {
    const missing = targets.filter(mj => !mjMap.has(mj));
    if (missing.length) {
      throw new Error('Missing MJ entries in ivsCharacterMap.js: ' + missing.join(', '));
    }
  });

  test('PUA presence and base font mj-name for targets', () => {
    for (const mj of targets) {
      const rec = mjMap.get(mj);
      const ivsStr = decodeEscapedJS(rec.ivsLiteral);
      const puaStr = decodeEscapedJS(rec.pua);
      const { baseCP, vsCP } = ivsToBaseAndVS(ivsStr);

      // External font must contain PUA codepoint
      const puaCP = puaStr.codePointAt(0);
      const gidExt = cpToGIDExt(puaCP);
      if (gidExt === 0) throw new Error(`${mj}: PUA U+${puaCP.toString(16).toUpperCase()} missing in external font`);

      // Base font mj-name via UVS
      const gidBase = getGIDFromUVS(baseFont, baseCP, vsCP);
      if (gidBase === 0) throw new Error(`${mj}: base UVS not present in ipam.ttf (U+${baseCP.toString(16)} + U+${vsCP.toString(16)})`);
      const nameOf = parsePost(baseFont);
      const gname = nameOf(gidBase);
      if ((gname || '').toLowerCase() !== mj.toLowerCase().replace('mj','mj')) {
        throw new Error(`${mj}: glyph name mismatch in ipam.ttf → ${gname}`);
      }
    }
  });
});
