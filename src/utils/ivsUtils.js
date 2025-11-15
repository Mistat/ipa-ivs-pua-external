// IVS文字変換ユーティリティ関数（段階的PUA配置対応）
// BMP PUA: 0xE000-0xF8FF (6,400文字) - 高頻度VS優先
// SMP PUA: 0xF0000- (65,534文字) - 残りのVS
import * as ivsMap from './ivsCharacterMap.js';

// Merge maps with overrides taking precedence
const ivsToExternalCharMap = ivsMap.ivsToExternalCharMap;
// Merge generated fallback with overrides (overrides take precedence)
const baseCharFallbackToExternalMap = ivsMap.baseCharFallbackToExternalMap;

export function convertIVSToExternal(text, { enableBaseFallback = false } = {}) {
  let result = text;
  // 1) IVS → PUA
  Object.entries(ivsToExternalCharMap).forEach(([ivs, external]) => {
    result = result.replace(new RegExp(ivs, 'g'), external);
  });
  // 2) 任意: 基本文字フォールバック
  if (enableBaseFallback) {
    Object.entries(baseCharFallbackToExternalMap).forEach(([baseChar, external]) => {
      // 負荷の低い防御: 直後に VS (U+DB40..DB7F + U+DC00..DFFF) が続く場合は置換しない
      const pattern = new RegExp(`${baseChar}(?![\uDB40-\uDB7F][\uDC00-\uDFFF])`, 'g');
      result = result.replace(pattern, external);
    });
  }
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

// 基本文字フォールバック（B_value 既定異体）を個別に適用したい場合のユーティリティ
export function applyBaseCharFallback(text) {
  let result = text;
  Object.entries(baseCharFallbackToExternalMap).forEach(([baseChar, external]) => {
    result = result.replace(new RegExp(baseChar, 'g'), external);
  });
  return result;
}
