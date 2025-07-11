// IVS文字変換ユーティリティ関数（段階的PUA配置対応）
// BMP PUA: 0xE000-0xF8FF (6,400文字) - 高頻度VS優先
// SMP PUA: 0xF0000- (65,534文字) - 残りのVS

import { ivsToExternalCharMap, puaAllocationStats } from './ivsCharacterMap.js';


export function convertIVSToExternal(text) {
  let result = text;
  Object.entries(ivsToExternalCharMap).forEach(([ivs, external]) => {
    result = result.replace(new RegExp(ivs, 'g'), external);
  });
  return result;
}


export function hasIVSCharacters(text) {
  return Object.keys(ivsToExternalCharMap).some(ivs => text.includes(ivs));
}


export function countIVSCharacters(text) {
  let count = 0;
  Object.keys(ivsToExternalCharMap).forEach(ivs => {
    const matches = text.match(new RegExp(ivs, 'g'));
    if (matches) {
      count += matches.length;
    }
  });
  return count;
}

export function getIVSCharacterDetails(text) {
  const details = [];
  Object.entries(ivsToExternalCharMap).forEach(([ivs, external]) => {
    const matches = text.match(new RegExp(ivs, 'g'));
    if (matches) {
      // IVS文字の文字コードを取得
      const ivsCodePoints = [];
      for (let i = 0; i < ivs.length; i++) {
        const codePoint = ivs.codePointAt(i);
        if (codePoint) {
          ivsCodePoints.push(`U+${codePoint.toString(16).toUpperCase().padStart(4, '0')}`);
          // サロゲートペアの場合、次の文字をスキップ
          if (codePoint > 0xFFFF) {
            i++;
          }
        }
      }
      
      // 外字の文字コードを取得
      const externalCodePoint = external.codePointAt(0);
      const externalCode = `U+${externalCodePoint.toString(16).toUpperCase()}`;
      
      details.push({
        ivs: ivs,
        ivsCode: ivsCodePoints.join(','),
        external: external,
        externalCode: externalCode,
        count: matches.length
      });
    }
  });
  return details;
}



