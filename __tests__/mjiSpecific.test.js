// Verify specific MJI expectation:
// U+2B9E4 should correspond to MJ059401, i.e. the IVS tag 2B9E4_E0102
// and map to the expected PUA in ivsToExternalCharMap.

import { convertIVSToExternal } from '../src/utils/ivsUtils.js';
import { ivsToExternalCharMap } from '../src/utils/ivsCharacterMap.js';

function ivsLiteral(baseHex, vsHex) {
  const base = String.fromCodePoint(parseInt(baseHex, 16));
  const vsIdx = parseInt(vsHex.slice(1), 16) - 0xE0100; // E0100 -> 0
  const vs = String.fromCharCode(0xDB40, 0xDD00 + vsIdx);
  return base + vs;
}

describe('MJI specific mapping', () => {
  test('U+2B9E4_E0102 maps to MJ059401 PUA (\uEEF2)', () => {
    const key = ivsLiteral('2B9E4', 'E0102');
    // Expected PUA for MJ059401 as per mapping comments in ivsCharacterMap.js
    const expectedPUA = '\uEEF2';

    // 1) Direct table lookup
    expect(ivsToExternalCharMap[key]).toBe(expectedPUA);

    // 2) Conversion API result
    const out = convertIVSToExternal(key);
    expect(out).toBe(expectedPUA);
  });
});

