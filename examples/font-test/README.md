# IVS Font Test Viewer

IVS文字とPUA文字のマッピング表示とフォント表示テストのための静的HTMLページです。

## 概要

このフォントテストビューワーは、IVS (Ideographic Variation Sequence) 文字の動作確認と、PUA (Private Use Area) マッピングの表示テストを行うためのツールです。

## 機能

- 🔤 **IVS文字一覧表示**: 11,362文字のIVS→PUAマッピング
- 🎨 **フォント比較**: IPA明朝とIVS外字フォントの表示比較
- 📊 **統計情報**: VS (Variation Selector) 別の文字数統計
- 🔍 **検索機能**: 文字やコードポイントでの検索
- 📱 **レスポンシブ対応**: デスクトップ・モバイル両対応

## ライブデモ

📱 **GitHub Pages**: https://mistat.github.io/ipa-ivs-pua-external/font-test/

## ローカル実行

静的HTMLファイルなので、Webサーバーで配信するだけで動作します：

```bash
# Python 3の場合
python3 -m http.server 8000

# Node.jsのhttp-serverを使用する場合
npx http-server .

# 直接ブラウザで開く場合
open font-test-static.html
```

## ファイル構成

```
examples/font-test/
├── README.md                    # このファイル
├── font-test-static.html       # メインのテストページ
└── (フォントファイルは../../public/fonts/から参照)
```

## 使用方法

1. **ページを開く**: ブラウザでHTMLファイルを開く
2. **フォント読み込み**: 自動でIVS外字フォントが読み込まれます
3. **文字確認**: 各IVS文字の表示を確認
4. **比較表示**: IPA明朝とIVS外字フォントの表示差を確認
5. **検索**: 上部の検索ボックスで特定の文字を検索

## 表示される情報

### IVS文字情報
- **Original**: 元のIVS文字（VS付き）
- **External**: PUA領域にマッピングされた外字
- **VS**: 使用されているVariation Selector
- **Unicode**: 文字のUnicodeコードポイント
- **PUA**: PUA領域のコードポイント

### 統計情報
- VS別の文字数
- BMP/SMP PUA領域の使用状況
- 総文字数

## フォント要件

このテストビューワーは以下のフォントを使用します：

- **IPA明朝** (`ipam.ttf`): ベースフォント
- **IVS外字フォント** (`ipa-ivs-external.woff2`): IVS文字のPUAマッピング版

フォントファイルは `../../public/fonts/` から自動で読み込まれます。

## トラブルシューティング

### フォントが表示されない場合

1. **フォントファイルの確認**: `../../public/fonts/` にフォントファイルが存在するか確認
2. **Webサーバー**: ローカルファイルではなく、HTTP(S)サーバー経由でアクセス
3. **CORS問題**: 一部のブラウザでローカルファイルアクセス時にCORS制限がかかる場合があります

### 文字が□で表示される場合

1. **フォント生成**: 親ディレクトリでフォント生成が完了しているか確認
2. **ブラウザ対応**: 使用ブラウザがWOFF2フォーマットに対応しているか確認
3. **文字対応**: 該当のIVS文字がフォントに含まれているか確認

## 関連ファイル

- **パッケージ**: `../../package.json` - ivs-font-processorメインパッケージ
- **フォント**: `../../public/fonts/` - 生成されたフォントファイル
- **スクリプト**: `../../scripts/` - フォント生成スクリプト

## ライセンス

フォントファイルおよび文字データについては、プロジェクトルートのREADMEのライセンスセクションを参照してください。