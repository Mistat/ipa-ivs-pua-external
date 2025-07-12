# IVS Font Processor Examples

このディレクトリには、`ivs-font-processor`パッケージの使用例とデモアプリケーションが含まれています。

## 📱 ライブデモ

**GitHub Pages**: https://mistat.github.io/ipa-ivs-pua-external/

## 🚀 Examples

### 1. Font Test Viewer (`font-test/`)

IVS文字とPUA文字のマッピング表示とフォント表示テストのための静的HTMLページです。

**特徴:**
- 🔤 11,362文字のIVS→PUAマッピング表示
- 🎨 IPA明朝とIVS外字フォントの比較表示
- 📊 VS別統計情報
- 🔍 文字検索機能

**アクセス:**
- **ライブデモ**: https://mistat.github.io/ipa-ivs-pua-external/font-test/
- **ローカル**: `font-test/font-test-static.html`をブラウザで開く

### 2. PDF Generation App (`pdf/`)

IVS文字を含むPDF生成機能を持つVue.jsアプリケーションです。

**特徴:**
- 🔄 IVS文字の自動検出とPUA文字への変換
- 📄 ActiveReportsJSを使用したPDF生成
- 🎨 IVS文字の詳細表示（変換前後の比較）
- 📱 レスポンシブWebアプリ

**⚠️ ライセンス要件:**
PDF生成機能には `@grapecity/activereports` の商用ライセンスが必要です。デモ版は開発・評価目的でのみ使用可能です。

**アクセス:**
- **ライブデモ**: https://mistat.github.io/ipa-ivs-pua-external/pdf/
- **ローカル開発**: `cd pdf && npm install && npm run serve`

## 🔧 使用技術

### Font Test Viewer
- 静的HTML/CSS/JavaScript
- IVS外字フォント (WOFF2/TTF)
- レスポンシブデザイン

### PDF Generation App
- Vue.js 2.6
- ActiveReports JS (商用ライセンス必要)
- IVS Font Processor
- Webpack 4 (Vue CLI 4)

## 📂 ディレクトリ構成

```
examples/
├── README.md              # このファイル
├── font-test/
│   ├── README.md          # フォントテストの詳細
│   └── font-test-static.html  # 静的テストページ
└── pdf/
    ├── README.md          # PDFアプリの詳細
    ├── package.json       # Vue.jsアプリの依存関係
    ├── src/               # Vueコンポーネント
    ├── public/            # 公開ファイル
    └── vue.config.js      # Vue CLI設定
```

## 🚀 クイックスタート

### Font Test Viewer を試す

```bash
# 静的ファイルを直接開く
open examples/font-test/font-test-static.html

# またはHTTPサーバーで配信
cd examples/font-test
python3 -m http.server 8000
# http://localhost:8000/font-test-static.html にアクセス
```

### PDF Generation App を試す

```bash
# 依存関係をインストール
cd examples/pdf
npm install

# 開発サーバーを起動
npm run serve
# http://localhost:8080 にアクセス
```

## 🌐 GitHub Pages デプロイ

このプロジェクトは GitHub Actions により自動デプロイされます：

1. **Font Test**: 静的ファイルをそのままコピー
2. **PDF App**: Vue.js アプリをビルドして配置
3. **Landing Page**: 両方へのリンクを含むトップページを生成

**デプロイURL**: https://mistat.github.io/ipa-ivs-pua-external/

## 📖 関連ドキュメント

- **メインREADME**: `../README.md` - パッケージ全体の概要
- **スクリプト**: `../scripts/README.md` - フォント生成手順
- **API仕様**: `../src/utils/` - ユーティリティ関数

## 🎯 使用例

### 基本的なIVS文字変換

```javascript
import { convertIVSToExternal } from 'ivs-font-processor';

const ivsText = "漢字󠄀";  // IVS文字
const puaText = convertIVSToExternal(ivsText);  // PUA文字に変換
```

### フォント適用

```css
@font-face {
  font-family: 'IVS-External';
  src: url('./fonts/ipa-ivs-external.woff2') format('woff2'),
       url('./fonts/ipa-ivs-external.ttf') format('truetype');
}

.ivs-text {
  font-family: 'IVS-External', serif;
}
```

## ⚠️ 注意事項

1. **フォントファイル**: examples実行前に親ディレクトリでフォント生成が必要
2. **ブラウザ対応**: モダンブラウザ（Chrome 60+, Firefox 60+, Safari 12+）
3. **ライセンス**: IPAフォントライセンスの条件に従って使用してください
4. **ActiveReports**: PDF生成機能の商用利用には適切なライセンスが必要です

## 🔗 外部リンク

- **IPA明朝フォント**: https://moji.or.jp/ipafont/
- **ActiveReports**: https://www.grapecity.co.jp/activereports-js/
- **Unicode IVS**: https://unicode.org/charts/PDF/UE0100.pdf