# Font Metrics Check (width → autosize → render)

このミニツールは、計測と描画で同一フォントが使われているかを確認するための簡易デモです。次を可視化します：

- Canvasでの文字列幅計測（指定フォント）
- DOM要素の実描画幅（同じフォント指定）
- フォールバック検知（指定フォントと汎用フォントの幅差）
- IVS→PUA変換（convertIVSToExternal）を用いた入力テキストの整形

## 使い方

1) ローカルHTTPサーバで配信

```bash
cd examples/metrics-check
python3 -m http.server 8000
# ブラウザで http://localhost:8000/ にアクセス
```

2) フォントの場所
- プロジェクトルートの `fonts/ipa-ivs-external.(woff2|ttf)` と `fonts/ipam.ttf` を参照します。
- 未生成の場合は、プロジェクトルートで `npm run generate:fonts` を実行してください。

3) 操作手順
- 入力欄に代表テキスト（IVSやPUAを含む）を入力
- 「IVS→PUAして計測/描画」ボタンで幅計測と描画を更新
- 「比較」ボタンで、指定フォント（IPA-IVS-External）と比較フォント（IPAmOriginal=ipam.ttf）の幅差を比較
- DevToolsの“Rendered Fonts”で実際に使用されたフォントを確認（複数フォントが出ていないか）

## 代表テキストの例
- 邉󠄖 を含む: `邉󠄖 ABC 123`
- 既にPUAに変換済みの文字列（PUAコードポイント）

## 備考
- ブラウザは同一オリジンでESMを読み込むため、HTTPで配信してください（file://直開き不可）。
- 変換は `../../src/utils/ivsUtils.js` を直接importします（ESM）。比較フォントは `fonts/ipam.ttf` を `IPAmOriginal` 名で読み込みます。
