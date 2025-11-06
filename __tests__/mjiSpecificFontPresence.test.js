// Verify that the generated font actually contains the glyph for
// U+2B9E4 (MJ059401) which corresponds to IVS 2B9E4_E0102 → PUA.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { ivsToExternalCharMap } from '../src/utils/ivsCharacterMap.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function readUInt16(buf, off) { return (buf[off] << 8) | buf[off + 1]; }
function readUInt32(buf, off) {
  return ((buf[off] << 24) >>> 0) | (buf[off + 1] << 16) | (buf[off + 2] << 8) | buf[off + 3];
}
function loadFont(filePath) {
  const ab = fs.readFileSync(filePath);
  return new Uint8Array(ab.buffer, ab.byteOffset, ab.byteLength);
}
function findTable(buf, tagStr) {
  const tag = tagStr.charCodeAt(0) << 24 | tagStr.charCodeAt(1) << 16 | tagStr.charCodeAt(2) << 8 | tagStr.charCodeAt(3);
  const numTables = readUInt16(buf, 4);
  let off = 12;
  for (let i = 0; i < numTables; i++) {
    const tTag = readUInt32(buf, off);
    const tOffset = readUInt32(buf, off + 8);
    const tLength = readUInt32(buf, off + 12);
    if (tTag === tag) return { offset: tOffset, length: tLength };
    off += 16;
  }
  return null;
}
function parseCmap(buf) {
  const tbl = findTable(buf, 'cmap');
  if (!tbl) throw new Error('cmap not found');
  const base = tbl.offset;
  const numTables = readUInt16(buf, base + 2);
  let f4 = null, f12 = null;
  for (let i = 0; i < numTables; i++) {
    const rec = base + 4 + i * 8;
    const platformID = readUInt16(buf, rec);
    const subOffset = readUInt32(buf, rec + 4);
    const subBase = base + subOffset;
    const fmt = readUInt16(buf, subBase);
    if (fmt === 12 || (fmt === 0 && readUInt16(buf, subBase + 2) === 12)) f12 = { base: subBase };
    else if (fmt === 4 && platformID === 3) f4 = { base: subBase };
  }
  function cpToGID(cp) {
    if (cp > 0xFFFF && f12) {
      const b = f12.base;
      const nGroups = readUInt32(buf, b + 12);
      let lo = 0, hi = nGroups - 1, off = b + 16;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const m = off + mid * 12;
        const start = readUInt32(buf, m);
        const end = readUInt32(buf, m + 4);
        if (cp < start) hi = mid - 1; else if (cp > end) lo = mid + 1; else {
          const startGlyphID = readUInt32(buf, m + 8);
          return startGlyphID + (cp - start);
        }
      }
    }
    if (cp <= 0xFFFF && f4) {
      const b = f4.base;
      const segCount = readUInt16(buf, b + 6) / 2;
      const endOff = b + 14;
      const startOff = endOff + segCount * 2 + 2;
      const idDeltaOff = startOff + segCount * 2;
      const idRangeOffsetOff = idDeltaOff + segCount * 2;
      let lo = 0, hi = segCount - 1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const end = readUInt16(buf, endOff + mid * 2);
        if (cp > end) lo = mid + 1; else hi = mid - 1;
      }
      const i = lo;
      if (i >= segCount) return 0;
      const end = readUInt16(buf, endOff + i * 2);
      const start = readUInt16(buf, startOff + i * 2);
      if (cp < start || cp > end) return 0;
      const idDelta = readUInt16(buf, idDeltaOff + i * 2);
      const idRangeOffset = readUInt16(buf, idRangeOffsetOff + i * 2);
      if (idRangeOffset === 0) {
        return (cp + idDelta) & 0xFFFF;
      } else {
        const roff = idRangeOffsetOff + i * 2 + idRangeOffset;
        const idx = (cp - start) * 2;
        const glyphIndex = readUInt16(buf, roff + idx);
        if (glyphIndex === 0) return 0;
        return (glyphIndex + idDelta) & 0xFFFF;
      }
    }
    return 0;
  }
  return { cpToGID };
}

function ivsLiteral(baseHex, vsHex) {
  const base = String.fromCodePoint(parseInt(baseHex, 16));
  const vsIdx = parseInt(vsHex.slice(1), 16) - 0xE0100; // E0100 -> 0
  const vs = String.fromCharCode(0xDB40, 0xDD00 + vsIdx);
  return base + vs;
}

describe('Font contains MJ059401 (U+2B9E4_E0102 → PUA)', () => {
  test('ipa-ivs-external.ttf has the PUA for U+2B9E4_E0102', () => {
    const extFontPath = path.join(__dirname, '..', 'fonts', 'ipa-ivs-external.ttf');
    const font = loadFont(extFontPath);
    const cmap = parseCmap(font);

    const key = ivsLiteral('2B9E4', 'E0102');
    const pua = ivsToExternalCharMap[key];
    expect(pua).toBe('\uEEF2'); // mapping side asserts MJ059401 expectation

    const cp = pua.codePointAt(0);
    const gid = cmap.cpToGID(cp);
    expect(gid).not.toBe(0);

    // Inspect glyf data for non-empty outline using loca/glyf
    const head = findTable(font, 'head');
    const indexToLocFormat = readUInt16(font, head.offset + 50);
    const maxp = findTable(font, 'maxp');
    const numGlyphs = readUInt16(font, maxp.offset + 4);
    const loca = findTable(font, 'loca');
    const glyf = findTable(font, 'glyf');
    function glyphOffset(i) {
      if (indexToLocFormat === 0) {
        const off2 = readUInt16(font, loca.offset + i * 2);
        return off2 * 2;
      } else {
        return readUInt32(font, loca.offset + i * 4);
      }
    }
    const off1 = glyf.offset + glyphOffset(gid);
    let off2;
    if (gid + 1 < numGlyphs) {
      off2 = glyf.offset + glyphOffset(gid + 1);
    } else {
      off2 = glyf.offset + glyf.length; // last glyph: compare to table end
    }
    expect(off2).toBeGreaterThan(off1); // has non-zero length
  });
});
