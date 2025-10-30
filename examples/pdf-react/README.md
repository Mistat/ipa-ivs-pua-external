# IVS Font Processor React + pdfme Example

このサンプルは、`ivs-font-processor`パッケージと**pdfme**ライブラリを使用してIVS文字をPDF出力するReact.jsアプリケーションです。

## ライブデモ

📱 **GitHub Pages**: https://mistat.github.io/ipa-ivs-pua-external/pdf-react/

## 特徴

- ⚡ **React.js 18**: モダンなReactフックを使用
- 📄 **pdfme**: オープンソースのPDFライブラリ（MITライセンス）
- 🔄 **IVS文字の自動検出**: PUA文字への変換
- 🎨 **IVS文字の詳細表示**: 変換前後の比較
- 🚀 **Vite**: 高速なビルドツール
- 📱 **レスポンシブ対応**: モバイル・デスクトップ両対応

## 🆚 ActiveReports版との比較

| 項目 | pdfme版（この例） | ActiveReports版 |
|------|------------------|-----------------|
| **ライセンス** | ✅ MITライセンス（無料） | ⚠️ 商用ライセンス必要 |
| **バンドルサイズ** | ✅ 軽量 | ❌ 大きい |
| **技術スタック** | React 18 + Vite | Vue 2 + Webpack 4 |
| **PDF機能** | 基本的なPDF生成 | 高度なレポート機能 |
| **学習コスト** | ✅ 低い | ❌ 高い |
| **商用利用** | ✅ 制限なし | ⚠️ ライセンス購入必要 |

## セットアップ

### 1. 依存関係のインストール

```bash
cd examples/pdf-react
npm install
```

### 2. 開発サーバーの起動

```bash
npm run dev
```

### 3. ブラウザでアクセス

`http://localhost:3000` にアクセス

## 使用方法

1. **テキスト入力**: IVS文字を含むテキストを入力フィールドに入力
2. **プレビュー**: 変換されたPUA文字がリアルタイムで表示
3. **IVS詳細**: 検出されたIVS文字の詳細情報（変換前後の文字コード）を確認
4. **PDF生成**: 「PDF生成 (pdfme)」ボタンでPDFファイルをダウンロード

## 技術仕様

### 主要な依存関係

```json
{
  "dependencies": {
    "@pdfme/generator": "^4.0.0",
    "@pdfme/ui": "^4.0.0", 
    "@pdfme/common": "^4.0.0",
    "@pdfme/schemas": "^4.0.0",
    "ivs-font-processor": "file:../../",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
```

### フォント参照

このアプリケーションは親ディレクトリの`fonts/`からフォントファイルを参照します：

- `./fonts/ipam.ttf` - IPA明朝フォント
- `./fonts/ipa-ivs-external.ttf` - IVS外字フォント

### パッケージ参照

`package.json`で親ディレクトリのivs-font-processorパッケージを直接参照：

```json
{
  "dependencies": {
    "ivs-font-processor": "file:../../"
  }
}
```

## 開発

### ビルド

```bash
npm run build
```

### リント

```bash
npm run lint
```

### プレビュー（ビルド後の確認）

```bash
npm run preview
```

## 使用例のコード

### フォント読み込み

```javascript
const loadFonts = async () => {
  const ipaResponse = await fetch('./fonts/ipam.ttf');
  const ipaBuffer = await ipaResponse.arrayBuffer();
  
  const ivsResponse = await fetch('./fonts/ipa-ivs-external.ttf');
  const ivsBuffer = await ivsResponse.arrayBuffer();
  
  setFonts({
    'IPA明朝': ipaBuffer,
    'IPA-IVS-External': ivsBuffer
  });
};
```

### PDF生成

```javascript
import { generate } from '@pdfme/generator';

const template = {
  schemas: [[
    {
      name: 'ivsText',
      type: 'text',
      position: { x: 50, y: 100 },
      width: 150,
      height: 30,
      fontSize: 18,
      fontName: 'IPA-IVS-External'
    }
  ]]
};

const pdf = await generate({
  template,
  inputs: [{ ivsText: convertedText }],
  options: { font: fonts }
});
```

## トラブルシューティング

### フォントが表示されない場合

1. 親ディレクトリに`fonts/`フォルダが存在することを確認
2. フォントファイルが正しく生成されていることを確認
3. ブラウザの開発者ツールでネットワークエラーがないか確認

### PDF生成エラーが発生する場合

1. フォントが正しく読み込まれていることを確認
2. pdfmeのバージョンが最新であることを確認
3. ブラウザコンソールでエラーメッセージを確認

### IVS文字が変換されない場合

1. 親ディレクトリの`src/utils/ivsCharacterMap.js`が最新であることを確認
2. `npm install`を再実行して依存関係を更新

## ライセンス

- **pdfme**: MITライセンス
- **React**: MITライセンス
- **IVS Font Processor**: MITライセンス
- **フォントファイル**: IPAフォントライセンス

詳細は、プロジェクトルートのREADMEのライセンスセクションを参照してください。
