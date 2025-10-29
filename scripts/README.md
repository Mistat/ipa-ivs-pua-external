# Font Generation & Mapping Scripts

このディレクトリには、IVS(表意文字異体字シーケンス)をPUA(私用領域)へ再配置した外字フォントの生成と、ブラウザ/JSで利用するIVS→PUAマッピングの生成に関わるスクリプト群が含まれます。

目的は次の2点です:
- 異体字をPUAに割り当てた外字フォント(ipa-ivs-external)を生成する
- そのフォントに対応するIVS→PUAのマッピングをJSとして配布する

---

## 前提条件(環境)

- Python 3.7+
- FontForge 本体 + Pythonバインディング
  - macOS: `brew install fontforge`
  - Ubuntu/Debian: `sudo apt-get install fontforge`
  - Windows: 公式サイト https://fontforge.org/en-US/downloads/
- Python パッケージ
  - `pip install openpyxl pandas numpy fonttools` (FontForgeのPythonバインディングは通常FontForge本体に付随)
- Node.js 14+

データ/フォントの配置:
- 入力Excel: `ipa/mji.00602.xlsx` (MJ文字情報)
- 入力フォント: `fonts/ipam.ttf` (IPA明朝)

---

## 生成物(アウトプット)

- マッピング(JS): `src/utils/ivsCharacterMap.js`
  - `ivsToExternalCharMap`, `baseCharFallbackToExternalMap`, `puaAllocationStats`
- 外字フォント: `fonts/ipa-ivs-external.ttf`, `fonts/ipa-ivs-external.woff2`
- 検証用HTML: `examples/font-test/font-test-static.html`
- 中間成果物(参考):
  - `mji_analysis_with_f_column.json`, `mji_analysis_f_to_c_mapping.json`, `c_to_f_mapping.json`, `tmp/converted.json`

---

## 実行フロー(パイプライン)

1) データ解析・準備（マッピングはこの後に一括生成）
- `parse_excel_with_f_column.py`
  - MJ文字情報Excelから、基本文字とIVS(例: U+xxxx U+E01xx)の対応行を抽出・正規化
  - 出力: 解析済みJSON(例: `mji_analysis_with_f_column.json`)

- `reverse_c_f_mapping.py`
  - C列(基本文字)⇔F列(IVS)の双方向検索がしやすい形式に整形
  - 出力: `c_to_f_mapping.json`, `mji_analysis_f_to_c_mapping.json`

- (任意) `derive_base_mj_from_font.py`
  - ソースフォント（fonts/ipam.ttf）の cmap / UVS を解析し、各文字の既定異体（base_f_tag/base_mj）をフォント実態に合わせて決定
  - 優先順位:
    1) UVSで既定グリフと一致するVS
    2) E0100 が候補にあれば採用
    3) B_value に含まれる VS
    4) 上記が無ければ最小のVS
  - fonttools が無い/フォントがUVSを持たない場合は 2–4 のヒューリスティック

2) マッピング・フォント生成（統合）
- `extract_ivs_glyphs_mj_based.py`
  - mji_analysis_f_to_c_mapping.json と derive の結果を元に、`src/utils/ivsCharacterMap.js`（ivsToExternalCharMap / baseCharFallbackToExternalMap / puaAllocationStats）を生成し、同時にフォント（ipa-ivs-external.ttf/woff2）を出力

4) テストアセット生成
- `generate_static_font_test.py`
  - マッピングのサンプルと生成フォントの描画確認用HTMLを出力
  - 出力: `examples/font-test/font-test-static.html`

---

## 実行方法

個別実行:
```bash
# 解析（Excel→JSON, 逆引き, 既定異体の導出）
python3 scripts/parse_excel_with_f_column.py
python3 scripts/reverse_c_f_mapping.py
python3 scripts/derive_base_mj_from_font.py

# マッピング + フォント生成
python3 scripts/extract_ivs_glyphs_mj_based.py

# テストページ生成
python3 scripts/generate_static_font_test.py
```

NPMスクリプト:
```bash
# 一括(解析→フォント＆マッピング)
npm run setup

# 段階実行
npm run parse
npm run generate:fonts
npm run generate:test
```

フォント生成(推奨シーケンス):
```bash
npm run parse:new && npm run generate:fonts
```

---

## スクリプト一覧(詳細)

- `parse_excel_with_f_column.py`
  - 入力: `ipa/mji.00602.xlsx`
  - 役割: ExcelからIVS列を含む行を抽出してJSON化。

- `reverse_c_f_mapping.py`
  - 役割: 基本文字(C列)→IVS(F列)、IVS→基本文字の両方向参照を生成。

- `derive_base_mj_from_font.py`
  - 役割: フォントの cmap/UVS を解析して既定異体（base_f_tag/base_mj）を導出

- `fix_mj_based_extraction.py`（非推奨）
  - 役割: 旧来の抽出スクリプト生成/一部マッピング生成（現在は実行しても何もしません）

- `extract_ivs_glyphs_mj_based.py`
  - 入力: `fonts/ipam.ttf`
  - 出力: `fonts/ipa-ivs-external.ttf`, `fonts/ipa-ivs-external.woff2`
  - 役割: IVSグリフのPUA再配置と書き出し。

- `generate_static_font_test.py`
  - 出力: `examples/font-test/font-test-static.html`
  - 役割: マッピングとフォントの可視確認用HTML生成。

- `install-fonts.cjs`
  - コマンド: `npx install-ivs-fonts [<targetDir>]`
  - 役割: `fonts/`配下のフォントを任意ディレクトリへコピー(既定: `./fonts`). 対応: TTF/WOFF/WOFF2/OTF。

- `fix_paths.py`
  - 役割: 生成物の参照パスを一括補正するときのユーティリティ。

- `test.js`
  - 役割: `convertIVSToExternal` を使った簡易動作確認サンプル。

---

## PUA配置戦略(概要)

- 段階的PUA配置(頻出VSをBMP PUAに優先配置、残りをSMP PUAへ)
  - BMP PUA(0xE000–0xF8FF): 6,400文字枠に頻度上位を収容
  - SMP PUA(0xF0000–): それ以外を収容
- 統計は `src/utils/ivsCharacterMap.js` の `puaAllocationStats` を参照

---

## 検証手順(任意)

```bash
# 1) JSマッピングの存在確認
node -e "import('./src/utils/ivsCharacterMap.js').then(m=>console.log(Object.keys(m).join(',')))"

# 2) 変換ユーティリティの単体テスト
npm run test:unit

# 3) 静的テストページの表示
open examples/font-test/font-test-static.html  # OSに応じて適宜
```

---

## トラブルシューティング

- FontForgeの認識確認
  ```bash
  fontforge -version
  python3 -c "import fontforge; print('FontForge Python bindings OK')"
  ```

- 権限エラー
  ```bash
  chmod +x scripts/*.py
  chmod +x scripts/install-fonts.cjs
  ```

- フォントファイルが見つからない
  ```bash
  ls -la ipa/
  ls -la fonts/
  ```

---

## ライセンス

- スクリプト: MIT (プロジェクトルートの `LICENSE` 参照)
- フォント/データ: IPAフォントライセンスおよび文字情報基盤の条件に従う
  - 具体はメイン `README.md` のライセンス節を参照
