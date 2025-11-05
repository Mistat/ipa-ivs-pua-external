// Sample-based presence check of codepoints in font files (no external deps)
// - Parses cmap format 4 (BMP) and 12 (UCS-4) minimally to confirm mapping
// - Verifies a sampled set of PUA codepoints exist in ipa-ivs-external.ttf
// - Optionally checks a sampled set of base CJK codepoints exist in ipam.ttf

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { ivsToExternalCharMap } from '../src/utils/ivsCharacterMap.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function readUInt16(buf, off) {
  return (buf[off] << 8) | buf[off + 1];
}
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
  let off = 12; // table records start
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
  const version = readUInt16(buf, base);
  const numTables = readUInt16(buf, base + 2);
  let format4 = null;
  let format12 = null;
  for (let i = 0; i < numTables; i++) {
    const recOff = base + 4 + i * 8;
    const platformID = readUInt16(buf, recOff);
    const encodingID = readUInt16(buf, recOff + 2);
    const subOffset = readUInt32(buf, recOff + 4);
    const subBase = base + subOffset;
    const format = readUInt16(buf, subBase);
    if (format === 12 || (format === 0 && readUInt16(buf, subBase + 2) === 12)) {
      // format 12 has 16-bit format field set to 0, followed by 32-bit '12'
      const trueFormat = format === 12 ? 12 : readUInt32(buf, subBase + 0);
      if (trueFormat === 12) {
        // prefer UCS-4 mappings
        format12 = { platformID, encodingID, base: subBase };
      }
    } else if (format === 4) {
      // Windows BMP mapping likely
      if (platformID === 3) format4 = { platformID, encodingID, base: subBase };
      else if (!format4) format4 = { platformID, encodingID, base: subBase };
    }
  }

  function hasCP(cp) {
    if (cp > 0xFFFF && format12) {
      const b = format12.base;
      // format 12 header: format(2)=12, reserved(2), length(4), language(4), nGroups(4)
      const nGroups = readUInt32(buf, b + 12);
      let off = b + 16;
      // groups: startCharCode(4), endCharCode(4), startGlyphID(4)
      // binary search over groups
      let lo = 0, hi = nGroups - 1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const mOff = off + mid * 12;
        const start = readUInt32(buf, mOff);
        const end = readUInt32(buf, mOff + 4);
        if (cp < start) hi = mid - 1;
        else if (cp > end) lo = mid + 1;
        else {
          const startGlyphID = readUInt32(buf, mOff + 8);
          const gid = startGlyphID + (cp - start);
          return gid !== 0;
        }
      }
      // if not found in 12, fall through to 4 (unlikely for SMP)
    }
    if (format4 && cp <= 0xFFFF) {
      const b = format4.base;
      const segCountX2 = readUInt16(buf, b + 6);
      const segCount = segCountX2 / 2;
      const endCountOff = b + 14;
      const startCountOff = endCountOff + segCount * 2 + 2; // +2 for reservedPad
      const idDeltaOff = startCountOff + segCount * 2;
      const idRangeOffsetOff = idDeltaOff + segCount * 2;
      // binary search segment by endCount/startCount
      let lo = 0, hi = segCount - 1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const end = readUInt16(buf, endCountOff + mid * 2);
        if (cp > end) lo = mid + 1; else hi = mid - 1;
      }
      const i = lo;
      if (i >= segCount) return false;
      const end = readUInt16(buf, endCountOff + i * 2);
      const start = readUInt16(buf, startCountOff + i * 2);
      if (cp < start || cp > end) return false;
      const idDelta = readUInt16(buf, idDeltaOff + i * 2);
      const idRangeOffset = readUInt16(buf, idRangeOffsetOff + i * 2);
      if (idRangeOffset === 0) {
        const gid = (cp + idDelta) & 0xFFFF;
        return gid !== 0;
      } else {
        const roff = idRangeOffsetOff + i * 2 + idRangeOffset;
        const idx = (cp - start) * 2;
        const glyphIndex = readUInt16(buf, roff + idx);
        if (glyphIndex === 0) return false;
        const gid = (glyphIndex + idDelta) & 0xFFFF;
        return gid !== 0;
      }
    }
    return false;
  }

  return { hasCP };
}

function codePointOf(str) {
  return str.codePointAt(0);
}

describe('font codepoint presence (sampling)', () => {
  const extFontPath = path.join(__dirname, '..', 'fonts', 'ipa-ivs-external.ttf');
  const baseFontPath = path.join(__dirname, '..', 'fonts', 'ipam.ttf');
  const extFont = loadFont(extFontPath);
  const baseFont = loadFont(baseFontPath);
  const extCmap = parseCmap(extFont);
  const baseCmap = parseCmap(baseFont);

  test('PUA chars from mapping exist in ipa-ivs-external.ttf (BMP + SMP, ~100 each)', () => {
    const values = Object.values(ivsToExternalCharMap);
    // dedupe and collect PUA codepoints
    const pua = [];
    for (const v of values) {
      const cp = v.codePointAt(0);
      pua.push(cp);
    }
    // Sort to have deterministic distribution (BMP first, then SMP)
    pua.sort((a, b) => a - b);
    const bmp = pua.filter(cp => cp >= 0xE000 && cp <= 0xF8FF).slice(0, 100);
    const smp = pua.filter(cp => cp >= 0xF0000 && cp <= 0x10FFFD).slice(0, 100);
    const samples = bmp.concat(smp);
    expect(samples.length).toBeGreaterThan(0);
    for (const cp of samples) {
      const ok = extCmap.hasCP(cp);
      if (!ok) {
        throw new Error('Missing PUA cp U+' + cp.toString(16).toUpperCase());
      }
    }
  });

  test('A few base CJK codepoints exist in ipam.ttf (~50)', () => {
    // Sample base characters from IVS keys (before the VS)
    const keys = Object.keys(ivsToExternalCharMap);
    const seen = new Set();
    const baseSamples = [];
    for (const ivs of keys) {
      const cp = ivs.codePointAt(0);
      if (!seen.has(cp) && cp >= 0x3400 && cp <= 0x9FFF) {
        seen.add(cp);
        baseSamples.push(cp);
        if (baseSamples.length >= 50) break;
      }
    }
    expect(baseSamples.length).toBeGreaterThan(0);
    for (const cp of baseSamples) {
      const ok = baseCmap.hasCP(cp);
      if (!ok) {
        throw new Error('Missing base cp in ipam.ttf U+' + cp.toString(16).toUpperCase());
      }
    }
  });
});

