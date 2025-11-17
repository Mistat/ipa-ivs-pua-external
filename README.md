# IVS Font Processor

[![npm version](https://badge.fury.io/js/ivs-font-processor.svg)](https://badge.fury.io/js/ivs-font-processor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A JavaScript library for processing IVS (Ideographic Variation Sequence) characters with PUA (Private Use Area) mapped fonts for reliable web display.

## 概要

PDF生成ライブラリやその他の文書生成ライブラリでは、異体字（IVS文字）の表示がサポートされていないケースが多くあります。本ライブラリは、そうしたライブラリに対して異体字を確実に表示するため、異体字をPUA（Private Use Area）領域にマッピングした専用フォントと、IVS文字をPUA文字コードに変換するJavaScriptライブラリを提供します。

## Features

- 🚀 **簡単インストール**: `npx install-ivs-fonts`でフォント配置
<!-- TypeScriptの型定義は同梱していないため、記述を削除 -->
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

### 3. JavaScriptでの使用

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

#### `convertIVSToExternal(text: string, options?: { enableBaseFallback?: boolean }): string`
IVS文字をPUA文字に変換します。`options.enableBaseFallback` を `true` にすると、直後にVSが続かない基底文字を既定異体のPUAへフォールバックします。

```javascript
const result = convertIVSToExternal("漢字󠄀");  // IVS文字 → PUA文字

// 基本文字フォールバックを有効化（直後にVSが続く箇所は除外）
const resultWithFallback = convertIVSToExternal("邉", { enableBaseFallback: true });
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

## Advanced Usage

### カスタムフォント生成

独自のフォント生成の詳細は、プロジェクト内の `scripts/` を参照してください（開発者向け）。

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

PUA配置の詳細は、生成スクリプト（`scripts/`）のコメントを参照してください。

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

## FontForge Setup（開発者向け）

開発時にフォント生成スクリプト（`scripts/generate.py`）を使う場合のみ、FontForge の導入が必要です。ライブラリ利用者は不要です。

- macOS
  - Homebrew: `brew install fontforge`
  - 動作確認: `fontforge -version`

- Ubuntu/Debian
  - APT: `sudo apt-get update && sudo apt-get install -y fontforge`
  - 動作確認: `fontforge -version`

- Fedora/RHEL
  - DNF: `sudo dnf install -y fontforge`
  - 動作確認: `fontforge -version`

- Arch Linux
  - Pacman: `sudo pacman -Syu fontforge`
  - 動作確認: `fontforge -version`

- Windows
  - winget: `winget install --id FontForge.FontForge -e`
  - もしくは公式インストーラから導入（https://fontforge.org/ 参照）
  - 動作確認: PowerShell で `fontforge -version`

導入後、フォント生成は以下で実行できます（開発者のみ）。

```bash
npm run setup  # = fontforge -script scripts/generate.py
```

<!-- 互換漢字の正規化（NFKC）や compatMapOverride の説明は、現行実装では未対応のため削除しました。必要に応じて外部でNFKC正規化を実施してください。 -->

<!-- 互換漢字マップ（Excel取り込み）の説明は削除しました -->

## CI（GitHub Actions）

本リポジトリのCI（`.github/workflows/ci.yml`）は現在、最小限の no-op ジョブのみを実行します（テストはCIでは実行しません）。

- トリガー: push / pull_request
- ジョブ: `noop`（チェックアウトのみ）
- 備考: 自動テストが必要になった段階でワークフローに手順を追加してください。

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
