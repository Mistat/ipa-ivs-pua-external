# Font Generation Scripts

このディレクトリには、IVSフォントの生成と処理に関するスクリプトが含まれています。

## スクリプト一覧

### フォントインストール

#### `install-fonts.js`
IVSフォントをプロジェクトにインストールするスクリプトです。

```bash
# コマンドとして実行
npx install-ivs-fonts

# カスタムディレクトリにインストール
npx install-ivs-fonts ./assets/fonts/

# npm scriptとして実行
npm run install-fonts
```

**機能:**
- `public/fonts/`のフォントファイルを指定ディレクトリにコピー
- 対応フォーマット: TTF, WOFF, WOFF2, OTF
- エラーハンドリングと進行状況表示

### フォント生成パイプライン

カスタムフォントを生成する場合は、以下の順序でスクリプトを実行してください：

#### 1. データ解析・準備

```bash
# 1. Excelデータの解析
python3 scripts/parse_excel_with_f_column.py

# 2. マッピングの生成
python3 scripts/reverse_c_f_mapping.py
python3 scripts/fix_mj_based_extraction.py
```

#### 2. マッピング・フォント生成

```bash
# 3. JSマッピングの生成
python3 scripts/generate_js_mapping_only.py

# 4. フォント生成
python3 scripts/extract_ivs_glyphs_mj_based.py

# 5. テストページ生成
python3 scripts/generate_static_font_test.py
```

#### NPMスクリプトを使用

```bash
# 全体の実行
npm run setup

# 個別実行
npm run parse
npm run generate:mapping
npm run generate:fonts
npm run generate:test
```

## 必要な依存関係

### Python環境

- Python 3.7+
- FontForge

```bash
# FontForgeのインストール（macOS）
brew install fontforge

# FontForgeのインストール（Ubuntu/Debian）
sudo apt-get install fontforge

# FontForgeのインストール（Windows）
# https://fontforge.org/en-US/downloads/ からダウンロード
```

### Python パッケージ

```bash
pip install openpyxl pandas numpy fontforge-python
```

## スクリプト詳細

### `parse_excel_with_f_column.py`
MJ文字情報Excelファイルを解析し、IVS文字とPUA文字のマッピングデータを生成します。

**入力:** `ipa/mji.00602.xlsx`  
**出力:** 中間マッピングファイル

### `reverse_c_f_mapping.py`
C列（文字）とF列（IVS）のマッピングを逆引きできる形式に変換します。

### `fix_mj_based_extraction.py`
マッピングデータの不整合を修正し、最終的なマッピングを確定します。

### `generate_js_mapping_only.py`
JavaScriptで使用可能なマッピングオブジェクトを生成します。

**出力:** `src/utils/ivsCharacterMap.js`

### `extract_ivs_glyphs_mj_based.py`
IPA明朝フォントからIVS文字のグリフを抽出し、PUA領域にマッピングした新しいフォントを生成します。

**入力:** IPA明朝フォント  
**出力:** 
- `public/fonts/ipa-ivs-external.ttf`
- `public/fonts/ipa-ivs-external.woff2`

### `generate_static_font_test.py`
生成されたフォントをテストするためのHTMLページを生成します。

**出力:** `examples/font-test/font-test-static.html`

## PUA配置戦略

### BMP PUA (0xE000-0xF8FF): 6,400文字
- **VS19**: 3,830文字（最高頻度）
- **VS18**: 2,570文字（2番目）

### SMP PUA (0xF0000-0xF1361): 4,962文字  
- **VS20**: 1,511文字（部分配置）
- **VS17**: 1,169文字
- **VS21-VS32**: その他1,282文字

## トラブルシューティング

### FontForgeエラー

```bash
# FontForgeのバージョン確認
fontforge -version

# Python bindings確認
python3 -c "import fontforge; print('FontForge Python bindings OK')"
```

### パーミッションエラー

```bash
# スクリプトに実行権限を付与
chmod +x scripts/*.py
chmod +x scripts/install-fonts.js
```

### フォントファイルが見つからない

```bash
# ソースフォントの確認
ls -la ipa/
ls -la public/fonts/
```

## ライセンス

### スクリプトのライセンス
MIT License（プロジェクトルートのLICENSEファイルを参照）

### フォント・データのライセンス
- **IPA明朝フォント**: IPAフォントライセンス v1.0
- **MJ文字情報**: IPA文字情報基盤事業の利用条件に従う

詳細はメインREADMEのライセンスセクションを参照してください。