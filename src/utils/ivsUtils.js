// IVS文字変換ユーティリティ関数（段階的PUA配置対応）
// BMP PUA: 0xE000-0xF8FF (6,400文字) - 高頻度VS優先
// SMP PUA: 0xF0000- (65,534文字) - 残りのVS
import * as ivsMap from './ivsCharacterMap.js';

// Merge maps with overrides taking precedence
const ivsToExternalCharMap = ivsMap.ivsToExternalCharMap;
// Merge generated fallback with overrides (overrides take precedence)
const baseCharFallbackToExternalMap = ivsMap.baseCharFallbackToExternalMap;

// VS ranges (for negative lookahead when applying base fallback)
const VS_ASTRAL_RANGE = '\\u{E0100}-\\u{E01EF}';
const VS_BMP_RANGE = '\\uFE00-\\uFE0F';

// Quick presence check: VS17+ high surrogate
const hasVS = (s) => s.includes('\uDB40');

// Safe regex escape for dynamic literals
const escapeRegExp = (str) => str.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&');

export function convertIVSToExternal(text, { enableBaseFallback = false } = {}) {
  let result = text;

  // 1) IVS → PUA（VSが無ければスキップ）
  if (hasVS(result)) {
    for (const [ivs, external] of Object.entries(ivsToExternalCharMap)) {
      const re = new RegExp(escapeRegExp(ivs), 'gu');
      result = result.replace(re, external);
    }
  }

  // 2) 任意: 基本文字フォールバック（直後がVSのときは除外）
  if (enableBaseFallback) {
    for (const [baseChar, external] of Object.entries(baseCharFallbackToExternalMap)) {
      const re = new RegExp(
        escapeRegExp(baseChar) + `(?![${VS_BMP_RANGE}${VS_ASTRAL_RANGE}])`,
        'gu'
      );
      result = result.replace(re, external);
    }
  }

  return result;
}

export function hasIVSCharacters(text) {
  return hasVS(text) && Object.keys(ivsToExternalCharMap).some(ivs => text.includes(ivs));
}

export function countIVSCharacters(text) {
  let count = 0;
  Object.keys(ivsToExternalCharMap).forEach(ivs => {
    const matches = text.match(new RegExp(escapeRegExp(ivs), 'gu'));
    if (matches) {
      count += matches.length;
    }
  });
  return count;
}

export function getIVSCharacterDetails(text) {
  const details = [];
  Object.entries(ivsToExternalCharMap).forEach(([ivs, external]) => {
    const matches = text.match(new RegExp(escapeRegExp(ivs), 'gu'));
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
    result = result.replace(new RegExp(escapeRegExp(baseChar), 'gu'), external);
  });
  return result;
}

