# IVS Font Processor

[![npm version](https://badge.fury.io/js/ivs-font-processor.svg)](https://badge.fury.io/js/ivs-font-processor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A JavaScript/TypeScript library for processing IVS (Ideographic Variation Sequence) characters with PUA (Private Use Area) mapped fonts for reliable web display.

## 概要

PDF生成ライブラリやその他の文書生成ライブラリでは、異体字（IVS文字）の表示がサポートされていないケースが多くあります。本ライブラリは、そうしたライブラリに対して異体字を確実に表示するため、異体字をPUA（Private Use Area）領域にマッピングした専用フォントと、IVS文字をPUA文字コードに変換するJavaScript/TypeScriptライブラリを提供します。

## Features

- 🚀 **簡単インストール**: `npx install-ivs-fonts`でフォント配置
- 🔧 **TypeScript対応**: 完全な型定義
- 📱 **クロスブラウザ対応**: Chrome, Firefox, Safari, Edge
- ⚡ **軽量**: 必要な機能のみを提供
- 🎯 **11,380文字対応**: 包括的なIVS→PUAマッピング

## Installation

```bash
npm install ivs-font-processor
```

## Quick Start

### 1. パッケージのインストール

```bash
npm install ivs-font-processor
```

### 2. フォントのインストール

パッケージインストール後、フォントファイルをプロジェクトにコピーします：

```bash
# デフォルト（./fonts/にインストール）
npx install-ivs-fonts

# カスタムディレクトリにインストール
npx install-ivs-fonts ./assets/fonts/
```

### 3. JavaScript/TypeScriptでの使用

```javascript
import { 
  convertIVSToExternal, 
  hasIVSCharacters, 
  countIVSCharacters 
} from 'ivs-font-processor';

import { ivsToExternalCharMap } from 'ivs-font-processor/mapping';

// IVS文字をPUA文字に変換
const text = "IVS文字を含むテキスト";
const converted = convertIVSToExternal(text);

// IVS文字の存在確認
const hasIVS = hasIVSCharacters(text);

// IVS文字数をカウント
const count = countIVSCharacters(text);
```

### 4. CSSでフォントを適用

```css
@font-face {
  font-family: 'IVS-External';
  src: url('./fonts/ipa-ivs-external.woff2') format('woff2'),
       url('./fonts/ipa-ivs-external.ttf') format('truetype');
  font-display: swap;
}

.ivs-text {
  font-family: 'IVS-External', serif;
}
```

## API Reference

### Core Functions

#### `convertIVSToExternal(text: string): string`
IVS文字をPUA文字に変換します。

```javascript
const result = convertIVSToExternal("漢字󠄀");  // IVS文字 → PUA文字
```

#### `hasIVSCharacters(text: string): boolean`
テキストにIVS文字が含まれているかを確認します。

#### `countIVSCharacters(text: string): number`
テキスト内のIVS文字数をカウントします。

#### `getIVSCharacterDetails(text: string): Array`
IVS文字の詳細情報を取得します。

### Mapping Data

#### `ivsToExternalCharMap: Object`
IVS文字からPUA文字へのマッピングオブジェクト

#### `puaAllocationStats: Object`
PUA配置統計情報

## Advanced Usage

### カスタムフォント生成

独自のフォントを生成する場合は、[scripts/README.md](scripts/README.md)を参照してください。

## IVS と Variation Selector (VS)

IVS（Ideographic Variation Sequence）は「基底のCJK漢字」+「バリエーションセレクタ（VS）」で特定の字形を指定します。VSはゼロ幅で「既定無視（Default Ignorable）」のため、未対応環境ではVSが無視され既定字形で描画されます。

### VS17–VS32（基本）

これらは Variation Selectors Supplement（U+E0100–U+E01EF）に属し、主にCJKのIVS指定に用いられます。UTF-16ではサロゲートペアで表現されます。

- VS17: U+E0100（`\uDB40\uDD00`）
- VS18: U+E0101（`\uDB40\uDD01`）
- VS19: U+E0102（`\uDB40\uDD02`）
- VS20: U+E0103（`\uDB40\uDD03`）
- VS21: U+E0104（`\uDB40\uDD04`）
- VS22: U+E0105（`\uDB40\uDD05`）
- VS23: U+E0106（`\uDB40\uDD06`）
- VS24: U+E0107（`\uDB40\uDD07`）
- VS25: U+E0108（`\uDB40\uDD08`）
- VS26: U+E0109（`\uDB40\uDD09`）
- VS27: U+E010A（`\uDB40\uDD0A`）
- VS28: U+E010B（`\uDB40\uDD0B`）
- VS29: U+E010C（`\uDB40\uDD0C`）
- VS30: U+E010D（`\uDB40\uDD0D`）
- VS31: U+E010E（`\uDB40\uDD0E`）
- VS32: U+E010F（`\uDB40\uDD0F`）

本ライブラリに同梱のマッピング（`src/utils/ivsCharacterMap.js`）は VS17–VS32 を含みます。

### VS33 以降（VS256まで収録）

VS33–VS256（U+E0110–U+E01EF）もIVSで利用され、本パッケージの同梱マッピングに収録されています（段階的PUA配置により、VS19/VS18はBMP優先、その他はSMP中心）。

ヒント:
- VSは目に見えないため、デバッグ時はコードポイント（例: `U+9089 U+E0116`）やエスケープ（例: `\uDB40\uDD16`）で確認します。
- 変換後のPUAは同梱フォント（`fonts/ipa-ivs-external.*`）で描画されます。マッピング拡張時はフォントも必ず再生成してください。

## Examples

### React Example

```jsx
import React from 'react';
import { convertIVSToExternal } from 'ivs-font-processor';

function IVSText({ children }) {
  return (
    <span className="ivs-text">
      {convertIVSToExternal(children)}
    </span>
  );
}

export default IVSText;
```

### Vue.js Example

```vue
<template>
  <span class="ivs-text">{{ convertedText }}</span>
</template>

<script>
import { convertIVSToExternal } from 'ivs-font-processor';

export default {
  props: ['text'],
  computed: {
    convertedText() {
      return convertIVSToExternal(this.text);
    }
  }
}
</script>
```

## PUA Allocation Strategy

このライブラリは段階的PUA配置戦略を採用し、11,380文字のIVS→PUAマッピングを提供します。

詳細な配置戦略については、[scripts/README.md](scripts/README.md)を参照してください。

## Font Metrics Strategy

PDFや複数行レイアウトでの見切れ・行間過多を避けるため、フォント生成時に以下のメトリクスを調整・継承します。

- 基本コピー
  - OS/2: win/typo 系（Ascent/Descent/LineGap）、Panose、FamilyClass、Vendor、Weight/Width、UnicodeRange/CodePageRange
  - hhea/vhea: Ascent/Descent/LineGap、縦組メトリクスの有効化（hasvmetrics）
  - 下線: underlinePosition（upos）、underlineThickness（uwidth）
  - gasp: 元フォントのテーブルを継承
- クリッピング回避（Win系を安全側に）
  - 全グリフの外接矩形（boundingBox）から yMax/-yMin を取得し、OS/2 の WinAscent/WinDescent を少なくともそれ以上に引き上げ
  - 目的: PDF等でクリッピングにWin系が用いられる場合の見切れ防止
- 行間の正規化（Typo基準に）
  - fsSelection.UseTypoMetrics を有効化
  - hhea_ascent/desc を OS/2 TypoAscent/TypoDescent に合わせる
  - hhea_linegap は 0（不要な行間を足さない）
  - OS/2 TypoLineGap は元フォントの値に揃える
- 縦組/PUAグリフ
  - 基本文字/PUAの vwidth をコピー（無い場合は em を既定値）

備考
- 元フォント（IPA明朝）と収録グリフが異なるため、Win系を厳密一致にするとPUA追加分で見切れが発生する可能性があります。本プロジェクトでは「Win系は安全側」「行間はTypo基準でタイト」にすることで、PDFの見切れと複数行の行間過多を同時に避ける方針としています。
- 必要に応じて、Win系/Typo系の調整（よりタイト/より安全側）へ切り替え可能です。

## Browser Support

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## E2Eテスト（Headless）: examples/metrics-check

`examples/metrics-check` をヘッドレス環境で自動検証する E2E テストを追加しています。Puppeteer でサンプルページを起動し、Canvas 計測値と DOM 実描画の幅が近似しているかをチェックします。

- 目的: 計測用フォントと描画用フォントが一致しており、フォールバック混在が起きていないかの簡易検証
- 仕組み: ルート直下を静的配信 → `examples/metrics-check/index.html` を自動操作 → 幅の差分を閾値（±2px）以内で検証

実行手順:

```bash
# 1) Puppeteer を開発依存に追加
npm i -D puppeteer

# 2) フォントが未生成の場合は用意
npm run generate:fonts

# 3) Headless E2E を実行
npm run test:e2e
```

補足:
- Puppeteer が未導入の場合、このテストは自動スキップされます。
- 通常の `npm test` はユニットテストのみを実行し、この E2E は走りません。
- テスト内容は `__tests__/metrics-check.e2e.test.js` を参照してください。

## 互換漢字の正規化（PDF対策）

PDF出力などで CJK 互換漢字（U+F900–U+FAFF など）がそのままでは表示されない場合に備え、`convertIVSToExternal()` はデフォルトで互換漢字を統合漢字へ正規化（NFKCベース）します。

- 例: `U+F929 (朗)` → `U+6717 (朗)` に変換された上で、IVSやフォールバック処理が適用されます。
- オプション: `normalizeCJKCompat: false` を指定すると、互換漢字の正規化を無効化できます。

使用例:

```js
import { convertIVSToExternal } from './src/utils/ivsUtils.js';

// 既定: 互換漢字を統合漢字へ正規化 → IVS→PUA → 既定異体フォールバック
const out = convertIVSToExternal('\uF929'); // => '朗'（さらに必要ならPUA化）

// PDF用途で“正規化のみ”にしたい場合（基底フォールバックを無効化）
const outPdf = convertIVSToExternal('\uF929', { enableBaseFallback: false }); // => '朗'

// PDF用途で、特定の互換漢字の置換を強制したい場合（Excel/NFKCで導出できないとき）
// compatMapOverride に最小限の置換表を渡せます。
// 例（置換先は環境要件に合わせて設定してください）:
// const outPdf2 = convertIVSToExternal(text, {
//   enableBaseFallback: false,
//   compatMapOverride: {
//     '\\uFA11': '崎', // 﨑 → 崎（例）
//     // ... 必要な最小限のみ
//   }
// });
```

## 互換漢字マップ（Excel取り込み）

`npm run setup`（= `npm run parse && npm run generate:fonts`）の中で、`ipa/mji.00602.xlsx` を読み取り、CJK互換漢字（U+F900–U+FAFF, U+2F800–U+2FA1F）から統合漢字へのマッピングを自動生成し、`src/utils/ivsCharacterMap.js` に `cjkCompatibilityMap` として同梱します。ランタイムでは `ivsUtils` がこのマップを優先的に参照し、未収録のものはNFKCで折り畳みます（例: `U+F929(朗)`→`朗`）。

## CI（GitHub Actions）

本リポジトリには、ユニットテストと headless E2E を自動実行する GitHub Actions ワークフローを含めています（`.github/workflows/ci.yml`）。

- トリガー: push / pull_request
- ジョブ:
  - `unit-tests`: `npm ci` → `npm test`
  - `e2e-metrics-check`: `npm ci` → `npm i -D puppeteer` → `npm run test:e2e`
- 備考:
  - Puppeteer は CI 用に動的に導入します（リポジトリの依存には固定しません）。
  - E2E 実行時は `CI=true` を付与し、Puppeteer を `--no-sandbox` で起動するようにしています。

## License

### ソフトウェアライセンス

このプロジェクトのソフトウェア部分（フォント変換プログラム、JavaScript ライブラリ、スクリプト等）は MIT License の下でライセンスされています。詳細は [LICENSE](LICENSE) ファイルをご確認ください。

### フォント・データのライセンス

**重要**: このライブラリは以下の外部リソースを利用しており、それぞれ独自のライセンスが適用されます：

#### IPA明朝フォント
- **著作権者**: 独立行政法人情報処理推進機構（IPA）
- **ライセンス**: IPAフォントライセンス v1.0
- **ライセンス詳細**: https://moji.or.jp/ipafont/license/
- **利用条件**: IPAフォントライセンスの条件に従って利用してください

#### MJ文字情報一覧表
- **著作権者**: 独立行政法人情報処理推進機構（IPA）
- **出典**: 文字情報基盤事業
- **利用条件**: IPAが定める利用条件に従って利用してください

### ライセンス適用範囲の明確化

- **MIT License適用範囲**: 本ソフトウェアのプログラムコード、スクリプト、JavaScript ライブラリ、変換アルゴリズム等
- **IPA著作権範囲**: IPA明朝フォントファイル（ipam.ttf）、MJ文字情報データ、文字情報基盤データ
- **生成フォント**: IPA明朝フォントから生成された外字フォントについては、元のIPAフォントライセンスが適用されます

### 利用時の注意事項

1. **IPAフォントの利用**: IPA明朝フォントを利用する際は、必ずIPAフォントライセンスの条件を確認し、遵守してください
2. **著作権表示**: IPAフォントを利用したアプリケーションでは、適切な著作権表示を行ってください
3. **商用利用**: IPAフォントライセンスに従って商用利用の可否を判断してください
4. **再配布**: フォントファイルの再配布時は、IPAフォントライセンスの条件に従ってください

## Acknowledgments

- **IPA明朝フォント**: 独立行政法人情報処理推進機構（IPA）
- **文字情報基盤データ**: 独立行政法人情報処理推進機構（IPA）
- **FontForgeプロジェクト**: フォント処理エンジン
- **Unicode Consortium**: IVS (Ideographic Variation Sequence) 仕様

## Support

バグ報告や機能リクエストは [GitHub Issues](https://github.com/your-username/ivs-font-processor/issues) でお願いします。

**注意**: ライセンスに関するお問い合わせは、それぞれの著作権者に直接お問い合わせください。
