// Unit tests for IVS conversion utilities
// Run with: npm run test:unit

import { convertIVSToExternal } from '../src/utils/ivsUtils.js';

function cphex(str) {
  return Array.from(str).map(c => 'U+' + c.codePointAt(0).toString(16).toUpperCase());
}

describe('convertIVSToExternal', () => {
  test('󠄂㐄󠄁㜲󠄁邉󠄏 (IVS)', () => {
    const s = '㐄󠄂㐄󠄁㜲󠄁邉󠄏邉󠄖𩮺󠄁𩱿';
    const out = convertIVSToExternal(s);
    const arr = cphex(out);
    console.log(cphex(s))
    console.log(arr)
    expect(out).toEqual('󱍠󱍫󰓄󰽉');
  });

  test('󠄂(FALLBACK)', () => {
    const s = '𩮺󠄁𩱿';
    const out = convertIVSToExternal(s);
    const arr = cphex(out);
    console.log(cphex(s))
    console.log(arr)
    expect(out).toEqual('󰓄󰽉');
  });

  test('平全月 (fallback enabled)', () => {
    const s = '平全月󠄅';
    const out = convertIVSToExternal(s);
    const arr = cphex(out);
    expect(out).toEqual('平全月󠄅');
  });

  test('CJK Compatibility Ideograph U+F929 → U+6717 (朗)', () => {
    const s = '\uF929'; // 朗
    const out = convertIVSToExternal(s, { enableBaseFallback: false });
    expect(out).toEqual('朗');
  });


});
