# IVS Font Processor PDF Example

このサンプルは、`ivs-font-processor`パッケージを使用してIVS文字をPDF出力するVue.jsアプリケーションです。

## 特徴

- 🔄 IVS文字の自動検出とPUA文字への変換
- 📄 ActiveReportsJSを使用したPDF生成
- 🎨 IVS文字の詳細表示（変換前後の比較）
- 📚 親ディレクトリのivs-font-processorパッケージを直接参照

## セットアップ

### 1. 依存関係のインストール

```bash
cd examples/pdf
npm install
```

### 2. 開発サーバーの起動

```bash
npm run serve
```

または

```bash
npm run dev
```

### 3. ブラウザでアクセス

`http://localhost:8080` にアクセス

## ライブデモ

📱 **GitHub Pages**: https://mistat.github.io/ipa-ivs-pua-external/pdf/

## 使用方法

1. **テキスト入力**: IVS文字を含むテキストを入力フィールドに入力
2. **プレビュー**: 変換されたPUA文字がリアルタイムで表示
3. **IVS詳細**: 検出されたIVS文字の詳細情報（変換前後の文字コード）を確認
4. **PDF生成**: 「PDF生成」ボタンでPDFファイルをダウンロード

## 特記事項

### フォント参照

このアプリケーションは親ディレクトリの`public/fonts/`からフォントファイルを参照します：

- `../../public/fonts/ipam.ttf` - IPA明朝フォント
- `../../public/fonts/ipa-ivs-external.ttf` - IVS外字フォント

### パッケージ参照

`package.json`で親ディレクトリのivs-font-processorパッケージを直接参照：

```json
{
  "dependencies": {
    "ivs-font-processor": "file:../../"
  }
}
```

### テストサンプル文字

アプリケーションにはテスト用のIVS文字がプリセットされています：

- 㐄󠄀, 㐄󠄁, 㐄󠄂 (異なるバリエーション)
- 殧󠄇 (VS24)
- 搆󠄃 (VS20)
- など

## 開発

### ビルド

```bash
npm run build
```

### リント

```bash
npm run lint
```

### テスト

```bash
npm test
```

## トラブルシューティング

### フォントが表示されない場合

1. 親ディレクトリに`public/fonts/`フォルダが存在することを確認
2. フォントファイルが正しく生成されていることを確認
3. ブラウザの開発者ツールでネットワークエラーがないか確認

### IVS文字が変換されない場合

1. 親ディレクトリの`src/utils/ivsCharacterMap.js`が最新であることを確認
2. `npm install`を再実行して依存関係を更新

### PDF生成エラーが発生する場合

1. ActiveReportsのライセンスが正しく設定されていることを確認
2. ブラウザコンソールでエラーメッセージを確認
3. フォント登録が正常に完了していることを確認