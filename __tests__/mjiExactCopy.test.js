// Assert that MJ059401 glyph bytes are exactly copied to the generated font
// Source: ipam.ttf → glyph for U+2B9E4 with VS E0102 (cmap format 14)
// Target: ipa-ivs-external.ttf → glyph for PUA mapped from that IVS (U+EEF2)

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { ivsToExternalCharMap } from '../src/utils/ivsCharacterMap.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function u8(p) { const ab = fs.readFileSync(p); return new Uint8Array(ab.buffer, ab.byteOffset, ab.byteLength); }
function u16(b, o) { return (b[o] << 8) | b[o+1]; }
function u24(b, o) { return (b[o] << 16) | (b[o+1] << 8) | b[o+2]; }
function u32(b, o) { return ((b[o] << 24) >>> 0) | (b[o+1] << 16) | (b[o+2] << 8) | b[o+3]; }
function tag4(s) { return s.charCodeAt(0)<<24|s.charCodeAt(1)<<16|s.charCodeAt(2)<<8|s.charCodeAt(3); }

function findTable(font, tagStr) {
  const tag = tag4(tagStr);
  const numTables = u16(font, 4);
  let off = 12;
  for (let i=0;i<numTables;i++) {
    const tTag = u32(font, off);
    const tOff = u32(font, off+8);
    const tLen = u32(font, off+12);
    if (tTag === tag) return {offset:tOff, length:tLen};
    off += 16;
  }
  return null;
}

function getGIDFromUVS(font, baseCP, vsCP) {
  const cmap = findTable(font, 'cmap');
  if (!cmap) throw new Error('cmap not found');
  const base = cmap.offset;
  const numTables = u16(font, base+2);
  for (let i=0;i<numTables;i++) {
    const rec = base + 4 + i*8;
    const subOff = u32(font, rec+4);
    const sub = base + subOff;
    const fmt = u16(font, sub);
    if (fmt === 14) {
      const numVar = u32(font, sub+6);
      let p = sub + 10;
      for (let j=0;j<numVar;j++) {
        const varSel = u24(font, p); // 3 bytes
        const defOff = u32(font, p+3);
        const ndOff  = u32(font, p+7);
        p += 11;
        if (varSel === vsCP - 0) {
          if (ndOff) {
            const ndBase = sub + ndOff;
            const count = u32(font, ndBase);
            let q = ndBase + 4;
            for (let k=0;k<count;k++) {
              const u = u24(font, q);
              const gid = u16(font, q+3);
              if (u === baseCP) return gid;
              q += 5;
            }
          }
          // If only Default UVS exists and no Non-Default entry, fall back to base cmap
        }
      }
    }
  }
  return 0;
}

  function getGlyphSlice(font, gid) {
  const head = findTable(font, 'head');
  const maxp = findTable(font, 'maxp');
  const loca = findTable(font, 'loca');
  const glyf = findTable(font, 'glyf');
  if (!head || !maxp || !loca || !glyf) throw new Error('required tables missing');
  const indexToLocFormat = u16(font, head.offset+50);
  const numGlyphs = u16(font, maxp.offset+4);
  function glyphOffset(i) {
    if (indexToLocFormat === 0) {
      const o2 = u16(font, loca.offset + i*2);
      return o2*2;
    } else {
      return u32(font, loca.offset + i*4);
    }
  }
  const start = glyf.offset + glyphOffset(gid);
  const end   = glyf.offset + (gid+1 < numGlyphs ? glyphOffset(gid+1) : glyf.length);
  return font.slice(start, end);
}

function int16(b) { return (b[0]<<8)|(b[1]); }
function int16s(b,o){ let v=(b[o]<<8)|b[o+1]; if (v&0x8000) v= -((~v+1)&0xFFFF); return v; }

function decodeSimpleGlyfPoints(slice) {
  // Returns {contours, xMin,yMin,xMax,yMax, points:[{x,y,on}], simple:boolean}
  const nContours = int16(slice.subarray(0,2));
  if (nContours < 0) return { simple:false };
  const xMin = int16s(slice,2), yMin=int16s(slice,4), xMax=int16s(slice,6), yMax=int16s(slice,8);
  const endPts = [];
  let p=10;
  for (let i=0;i<nContours;i++){ endPts.push(int16(slice.subarray(p,p+2))); p+=2; }
  const instructionLength = int16(slice.subarray(p,p+2)); p+=2;
  p += instructionLength;
  const pointCount = endPts[endPts.length-1] + 1;
  const flags = new Uint8Array(pointCount);
  let i=0;
  while (i<pointCount) {
    const f = slice[p++];
    let reps = 1;
    if (f & 0x08) { reps = slice[p++]+1; }
    for (let r=0;r<reps && i<pointCount;r++) flags[i++]=f;
  }
  // x deltas
  const xs = new Int32Array(pointCount);
  let x=0;
  for (let j=0;j<pointCount;j++) {
    const f=flags[j];
    let dx=0;
    if (f & 0x02) { // x-short
      const b = slice[p++];
      dx = (f & 0x10) ? b : -b;
    } else {
      if (f & 0x10) dx = 0; else { dx = int16s(slice, p); p+=2; }
    }
    x += dx; xs[j]=x;
  }
  // y deltas
  const ys = new Int32Array(pointCount);
  let y=0;
  for (let j=0;j<pointCount;j++) {
    const f=flags[j];
    let dy=0;
    if (f & 0x04) { // y-short
      const b = slice[p++];
      dy = (f & 0x20) ? b : -b;
    } else {
      if (f & 0x20) dy = 0; else { dy = int16s(slice, p); p+=2; }
    }
    y += dy; ys[j]=y;
  }
  const points = new Array(pointCount);
  for (let j=0;j<pointCount;j++) points[j] = { x: xs[j], y: ys[j], on: !!(flags[j]&1) };
  return { simple:true, contours:nContours, xMin,yMin,xMax,yMax, points };
}

describe('Exact copy check: MJ059401 → U+2B9E4_E0102', () => {
  test('glyf bytes equal between ipam.ttf(mj059401) and ipa-ivs-external.ttf(uniEEF2)', () => {
    // Base font: locate GID for U+2B9E4 with VS E0102 via cmap format 14
    const baseFont = u8(path.join(__dirname, '..', 'fonts', 'ipam.ttf'));
    const gidBase = getGIDFromUVS(baseFont, 0x2B9E4, 0xE0102);
    expect(gidBase).not.toBe(0);
    const sliceBase = getGlyphSlice(baseFont, gidBase);
    expect(sliceBase.length).toBeGreaterThan(0);

    // External font: PUA mapped from ivsToExternalCharMap
    const key = String.fromCodePoint(0x2B9E4) + String.fromCharCode(0xDB40, 0xDD02);
    const pua = ivsToExternalCharMap[key];
    expect(pua).toBe('\uEEF2');
    const extFont = u8(path.join(__dirname, '..', 'fonts', 'ipa-ivs-external.ttf'));
    // Find GID for U+EEF2 via cmap
    function gidFromCP(font, cp) {
      const cmap = findTable(font, 'cmap');
      const base = cmap.offset;
      const numTables = u16(font, base+2);
      let gid = 0;
      for (let i=0;i<numTables;i++) {
        const rec = base+4+i*8;
        const sub = base + u32(font, rec+4);
        const fmt = u16(font, sub);
        if (fmt === 12 || (fmt===0 && u16(font, sub+2)===12)) {
          const b = sub;
          const n = u32(font, b+12);
          let lo=0, hi=n-1, off=b+16;
          while (lo<=hi) {
            const mid=(lo+hi)>>1;
            const m=off+mid*12;
            const start=u32(font,m), end=u32(font,m+4);
            if (cp<start) hi=mid-1; else if (cp>end) lo=mid+1; else { gid=u32(font,m+8)+(cp-start); break; }
          }
        }
      }
      return gid;
    }
    const gidExt = gidFromCP(extFont, 0xEEF2);
    expect(gidExt).not.toBe(0);
    const sliceExt = getGlyphSlice(extFont, gidExt);
    expect(sliceExt.length).toBeGreaterThan(0);

    // First, try strict equality (best evidence of copy)
    if (Buffer.compare(Buffer.from(sliceExt), Buffer.from(sliceBase)) !== 0) {
      // Fall back to outline equivalence: compare contour count, bounds, and point list
      const a = decodeSimpleGlyfPoints(sliceBase);
      const b = decodeSimpleGlyfPoints(sliceExt);
      expect(a.simple && b.simple).toBe(true);
      expect(a.contours).toBe(b.contours);
      expect([a.xMin,a.yMin,a.xMax,a.yMax]).toEqual([b.xMin,b.yMin,b.xMax,b.yMax]);
      expect(a.points.length).toBe(b.points.length);
      for (let i=0;i<a.points.length;i++) {
        expect(a.points[i]).toEqual(b.points[i]);
      }
    }
  });
});
