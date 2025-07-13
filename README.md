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
- 🎯 **11,362文字対応**: 包括的なIVS→PUAマッピング

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
# デフォルト（./public/fonts/にインストール）
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
  src: url('./public/fonts/ipa-ivs-external.woff2') format('woff2'),
       url('./public/fonts/ipa-ivs-external.ttf') format('truetype');
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

このライブラリは段階的PUA配置戦略を採用し、11,362文字のIVS→PUAマッピングを提供します。

詳細な配置戦略については、[scripts/README.md](scripts/README.md)を参照してください。

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