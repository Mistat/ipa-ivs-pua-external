#!/usr/bin/env python3
import json

def create_mj_based_extraction():
    """MJ文字図形名を使用したIVS文字抽出スクリプトを作成"""
    
    try:
        # JSON データを読み込み
        with open("../mji_analysis_f_to_c_mapping.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"データを読み込みました: {len(data)} エントリ")
        
        # 段階的PUA配置戦略をインポート
        try:
            from pua_allocation_strategy_staged import get_staged_pua_strategy
            pua_strategy = get_staged_pua_strategy()
            bmp_pua_start = pua_strategy['bmp_pua']['start']  # 0xE000
            smp_pua_start = pua_strategy['smp_pua']['start']  # 0xF0000
            print(f"✓ 段階的PUA戦略を使用: BMP=0x{bmp_pua_start:04X}, SMP=0x{smp_pua_start:05X}")
        except Exception as e:
            print(f"⚠ 段階的PUA戦略の読み込みに失敗、従来方式を使用: {e}")
            bmp_pua_start = 0xE000  # 修正: 0xE200 -> 0xE000
            smp_pua_start = 0xF0000
        
        # IVS文字列からMJ文字図形名へのマッピングを作成
        ivs_to_mj_mapping = {}
        ivs_mappings = {}
        current_pua = bmp_pua_start
        
        print("IVS文字列とMJ文字図形名のマッピングを生成中...")
        
        # 第1段階: 全てのIVS文字を収集してVS別にグループ化
        temp_chars = []
        vs_groups = {}
        
        # 各エントリからIVS文字列とMJ名のマッピングを生成
        for unicode_key, entry in data.items():
            if unicode_key.startswith('U+'):
                try:
                    unicode_code = int(unicode_key[2:], 16)
                    
                    # F列の値からIVS文字列を生成
                    if "C_values_with_F" in entry:
                        for f_value, c_value in entry["C_values_with_F"].items():
                            if '_' in f_value:
                                parts = f_value.split('_')
                                if len(parts) == 2:
                                    selector_hex = parts[1]  # E0100
                                    
                                    if selector_hex.startswith('E01'):
                                        selector_num = int(selector_hex[3:], 16)
                                        
                                        # VS17-VS256の範囲（E0100-E01EF）
                                        vs_code = 0xE0100 + selector_num
                                        vs_name = f"VS{17 + selector_num}"
                                        
                                        # IVS文字列を生成
                                        high_surrogate = ((vs_code - 0x10000) >> 10) + 0xD800
                                        low_surrogate = ((vs_code - 0x10000) & 0x3FF) + 0xDC00
                                        
                                        base_char = chr(unicode_code)
                                        vs_chars = chr(high_surrogate) + chr(low_surrogate)
                                        ivs_sequence = base_char + vs_chars
                                        
                                        # MJ名を小文字に変換
                                        mj_name = c_value.lower()
                                        
                                        # 一時データに保存（段階的配置のため）
                                        char_data = {
                                            'ivs_sequence': ivs_sequence,
                                            'mj_name': mj_name,
                                            'vs_name': vs_name,
                                            'unicode_code': unicode_code,
                                            'vs_code': vs_code
                                        }
                                        
                                        # VS別にグループ化
                                        if vs_name not in vs_groups:
                                            vs_groups[vs_name] = []
                                        vs_groups[vs_name].append(char_data)
                                        temp_chars.append(char_data)
                                    
                except ValueError:
                    continue
        
        print(f"✓ 収集完了: {len(temp_chars)}文字、{len(vs_groups)}種類のVS")
        
        # VS別の文字数を表示
        for vs_name in sorted(vs_groups.keys()):
            print(f"  {vs_name}: {len(vs_groups[vs_name])}文字")
        
        # 第2段階: 段階的PUA配置戦略に基づく配置
        print(f"\n第2段階: 段階的PUA配置...")
        
        # VS優先度リスト（使用頻度降順）
        vs_priority = ["VS19", "VS18", "VS20", "VS17", "VS21", "VS22", "VS23", "VS24", "VS25", "VS26", "VS27", "VS28", "VS29", "VS30", "VS31", "VS32"]
        
        bmp_pua_current = bmp_pua_start  # 0xE000
        smp_pua_current = smp_pua_start  # 0xF0000
        bmp_pua_end = 0xF8FF
        bmp_pua_allocated = 0
        smp_pua_allocated = 0
        
        # 優先度に基づく段階的配置
        for vs_name in vs_priority:
            if vs_name in vs_groups:
                chars_in_vs = vs_groups[vs_name]
                
                if vs_name in ["VS19", "VS18"]:
                    # 全てBMP PUAに配置
                    for char_data in chars_in_vs:
                        if bmp_pua_current <= bmp_pua_end:
                            pua_code = bmp_pua_current
                            ivs_to_mj_mapping[char_data['ivs_sequence']] = char_data['mj_name']
                            ivs_mappings[char_data['ivs_sequence']] = pua_code
                            bmp_pua_current += 1
                            bmp_pua_allocated += 1
                        else:
                            # BMP PUA領域が満杯の場合、SMP PUAに移行
                            pua_code = smp_pua_current
                            ivs_to_mj_mapping[char_data['ivs_sequence']] = char_data['mj_name']
                            ivs_mappings[char_data['ivs_sequence']] = pua_code
                            smp_pua_current += 1
                            smp_pua_allocated += 1
                    
                    print(f"✓ {vs_name}: {len(chars_in_vs):,}文字 → BMP PUA")
                    
                elif vs_name == "VS20":
                    # VS20は部分的配置
                    bmp_portion = min(len(chars_in_vs), bmp_pua_end - bmp_pua_current + 1)
                    
                    for i, char_data in enumerate(chars_in_vs):
                        if i < bmp_portion and bmp_pua_current <= bmp_pua_end:
                            # BMP PUAに配置
                            pua_code = bmp_pua_current
                            ivs_to_mj_mapping[char_data['ivs_sequence']] = char_data['mj_name']
                            ivs_mappings[char_data['ivs_sequence']] = pua_code
                            bmp_pua_current += 1
                            bmp_pua_allocated += 1
                        else:
                            # SMP PUAに配置
                            pua_code = smp_pua_current
                            ivs_to_mj_mapping[char_data['ivs_sequence']] = char_data['mj_name']
                            ivs_mappings[char_data['ivs_sequence']] = pua_code
                            smp_pua_current += 1
                            smp_pua_allocated += 1
                    
                    print(f"⚠ {vs_name}: {bmp_portion:,}文字 → BMP PUA, {len(chars_in_vs)-bmp_portion:,}文字 → SMP PUA")
                    
                else:
                    # VS17, VS21以降は全てSMP PUAに配置
                    for char_data in chars_in_vs:
                        pua_code = smp_pua_current
                        ivs_to_mj_mapping[char_data['ivs_sequence']] = char_data['mj_name']
                        ivs_mappings[char_data['ivs_sequence']] = pua_code
                        smp_pua_current += 1
                        smp_pua_allocated += 1
                    
                    print(f"→ {vs_name}: {len(chars_in_vs):,}文字 → SMP PUA")
        
        print(f"\n配置完了:")
        print(f"BMP PUA: {bmp_pua_allocated:,}文字 (0x{bmp_pua_start:04X}-0x{bmp_pua_current-1:04X})")
        print(f"SMP PUA: {smp_pua_allocated:,}文字 (0x{smp_pua_start:05X}-0x{smp_pua_current-1:05X})")
        print(f"総マッピング数: {len(ivs_to_mj_mapping):,}")
        
        print(f"IVS-MJマッピング生成完了: {len(ivs_to_mj_mapping)} エントリ")
        
        # 新しいPythonファイルを作成（MJベースの抽出）
        python_code = '''#!/usr/bin/env python3
"""
IVS文字をIPAm.ttfからMJ文字図形名を使用して抽出し、外字WebFontを作成するスクリプト
"""
import fontforge
import sys
import os
import json

def extract_ivs_glyphs():
    """MJ文字図形名を使用してIVS文字のグリフを抽出して外字フォントを作成"""
    
    # IPAm.ttfのパスを指定
    input_font_path = "../public/fonts/ipam.ttf"
    
    if not os.path.exists(input_font_path):
        print(f"エラー: {input_font_path} が見つかりません")
        return False
    
    try:
        # 元のフォントを開く
        print("IPAm.ttfを読み込み中...")
        original_font = fontforge.open(input_font_path)
        
        # フォント内のグリフ名を確認
        print("フォント内のグリフ名を確認中...")
        available_glyphs = []
        for glyph in original_font:
            glyph_name = original_font[glyph].glyphname
            if glyph_name and glyph_name.startswith('mj'):
                available_glyphs.append(glyph_name)
        
        print(f"MJ文字図形名のグリフ数: {len(available_glyphs)}")
        if available_glyphs:
            print(f"サンプル: {available_glyphs[:10]}")
        
        # 新しい外字フォントを作成
        print("外字フォントを作成中...")
        external_font = fontforge.font()
        external_font.fontname = "IPA-IVS-External"
        external_font.fullname = "IPA Mincho IVS External Characters"
        external_font.familyname = "IPA-IVS-External"
        external_font.weight = "Regular"
        external_font.copyright = "Based on IPA Font License Agreement v1.0"
        external_font.encoding = "unicode4"
        
        # 元フォントと同じメトリクスを設定
        external_font.em = original_font.em
        external_font.ascent = original_font.ascent
        external_font.descent = original_font.descent
        
        # 基本的な文字セットをコピー（ひらがな、カタカナ、基本漢字、記号など）
        print("基本文字セットをコピー中...")
        basic_ranges = [
            (0x0020, 0x007F),  # ASCII
            (0x3000, 0x303F),  # CJK記号・句読点（全角スペース含む）
            (0x3040, 0x309F),  # ひらがな
            (0x30A0, 0x30FF),  # カタカナ
            (0x4E00, 0x9FAF),  # CJK統合漢字
            (0xFF01, 0xFF60),  # 全角記号・英数字
        ]
        
        copied_basic_count = 0
        for start, end in basic_ranges:
            for code in range(start, end + 1):
                if code in original_font:
                    external_font.createChar(code)
                    external_font[code].clear()
                    
                    # スペース文字は特別処理
                    if code in [0x0020, 0x3000]:  # 半角スペース、全角スペース
                        external_font[code].width = original_font[code].width
                        if hasattr(original_font[code], 'vwidth'):
                            external_font[code].vwidth = original_font[code].vwidth
                    else:
                        # 通常の文字はグリフをコピー
                        original_font.selection.select(code)
                        original_font.copy()
                        external_font.selection.select(code)
                        external_font.paste()
                        external_font[code].width = original_font[code].width
                    
                    copied_basic_count += 1
        
        print(f"基本文字 {copied_basic_count}文字をコピーしました")
        
        # IVS文字列からMJ文字図形名へのマッピング
        ivs_to_mj_mapping = {
'''
        
        # ivs_to_mj_mappingの内容を追加
        mapping_lines = []
        for ivs_seq, mj_name in ivs_to_mj_mapping.items():
            key_repr = repr(ivs_seq)
            mapping_lines.append(f"            {key_repr}: '{mj_name}',")
        
        python_code += '\n'.join(mapping_lines)
        
        python_code += '''
        }
        
        # IVS文字列からPUAコードへのマッピング
        ivs_mappings = {
'''
        
        # ivs_mappingsの内容を追加
        mapping_lines = []
        for ivs_seq, pua_code in ivs_mappings.items():
            key_repr = repr(ivs_seq)
            mapping_lines.append(f"            {key_repr}: {hex(pua_code)},")
        
        python_code += '\n'.join(mapping_lines)
        
        python_code += '''
        }
        
        # MJ文字図形名を使用してIVS文字を抽出
        extracted_count = 0
        failed_count = 0
        
        for ivs_sequence, mj_name in ivs_to_mj_mapping.items():
            pua_code = ivs_mappings[ivs_sequence]
            
            # MJ文字図形名がフォントに存在するかチェック
            if mj_name in original_font:
                try:
                    # MJ文字図形のグリフを取得
                    original_glyph = original_font[mj_name]
                    print(f"  抽出中: {mj_name} ({repr(ivs_sequence)}) -> {hex(pua_code)}")
                    
                    # PUA領域に新しいグリフを作成
                    external_font.createChar(pua_code)
                    external_font[pua_code].clear()
                    
                    # グリフデータをコピー
                    original_font.selection.select(mj_name)
                    original_font.copy()
                    external_font.selection.select(pua_code)
                    external_font.paste()
                    external_font[pua_code].width = original_glyph.width
                    
                    extracted_count += 1
                except Exception as e:
                    print(f"  エラー: {mj_name} のコピーに失敗 - {e}")
                    failed_count += 1
            else:
                print(f"  警告: MJ文字図形名 '{mj_name}' がフォントに見つかりません")
                failed_count += 1
        
        print(f"抽出完了: {extracted_count}個成功, {failed_count}個失敗")
        
        # フォントディレクトリを作成
        os.makedirs("../public/fonts", exist_ok=True)
        
        # WebFont形式で保存
        output_woff2_path = "../public/fonts/ipa-ivs-external.woff2"
        output_ttf_path = "../public/fonts/ipa-ivs-external.ttf"
        
        print("WebFont形式で保存中...")
        external_font.generate(output_woff2_path)
        external_font.generate(output_ttf_path)
        
        print(f"外字フォントを作成しました:")
        print(f"  - {output_woff2_path}")
        print(f"  - {output_ttf_path}")
        
        # フォントを閉じる
        original_font.close()
        external_font.close()
        
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_mapping_file():
    """IVS文字マッピング定義ファイルを生成（段階的PUA配置対応）"""
    
    try:
        with open("../mji_analysis_f_to_c_mapping.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("IVS文字マッピングを段階的PUA戦略で生成中...")
        
        # 段階的PUA配置戦略をインポート
        try:
            from pua_allocation_strategy_staged import get_staged_pua_strategy
            pua_strategy = get_staged_pua_strategy()
            bmp_pua_start = pua_strategy['bmp_pua']['start']  # 0xE000
            smp_pua_start = pua_strategy['smp_pua']['start']  # 0xF0000
            print(f"✓ 段階的PUA戦略を使用: BMP=0x{bmp_pua_start:04X}, SMP=0x{smp_pua_start:05X}")
        except Exception as e:
            print(f"⚠ 段階的PUA戦略の読み込みに失敗、修正済み方式を使用: {e}")
            bmp_pua_start = 0xE000  # 修正: 0xE200 -> 0xE000
            smp_pua_start = 0xF0000
        
        # JavaScript用のマッピングを生成
        js_mappings = []
        
        # 第1段階: 全てのIVS文字を収集してVS別にグループ化
        temp_chars = []
        vs_groups = {}
        
        # 各エントリからIVS文字列を生成してVS別にグループ化
        for unicode_key, entry in data.items():
            if unicode_key.startswith('U+'):
                try:
                    unicode_code = int(unicode_key[2:], 16)
                    
                    # F列の値からIVS文字列を生成
                    if "C_values_with_F" in entry:
                        for f_value, c_value in entry["C_values_with_F"].items():
                            if '_' in f_value:
                                parts = f_value.split('_')
                                if len(parts) == 2:
                                    selector_hex = parts[1]  # E0100
                                    
                                    if selector_hex.startswith('E01'):
                                        selector_num = int(selector_hex[3:], 16)
                                        
                                        # VS17-VS256の範囲（E0100-E01EF）
                                        vs_code = 0xE0100 + selector_num
                                        vs_name = f"VS{17 + selector_num}"
                                        
                                        # JavaScript用文字列を生成（エスケープ形式、SMP対応）
                                        if unicode_code <= 0xFFFF:
                                            base_char_escaped = "\\\\u{:04X}".format(unicode_code)
                                        else:
                                            # SMP文字はサロゲートペアとして表現
                                            high = ((unicode_code - 0x10000) >> 10) + 0xD800
                                            low = ((unicode_code - 0x10000) & 0x3FF) + 0xDC00
                                            base_char_escaped = "\\\\u{:04X}\\\\u{:04X}".format(high, low)
                                        
                                        # サロゲートペアを計算
                                        high_surrogate = ((vs_code - 0x10000) >> 10) + 0xD800
                                        low_surrogate = ((vs_code - 0x10000) & 0x3FF) + 0xDC00
                                        
                                        vs_chars_escaped = "\\\\u{:04X}\\\\u{:04X}".format(high_surrogate, low_surrogate)
                                        
                                        # IVS文字データを一時保存
                                        char_data = {
                                            'ivs_sequence': base_char_escaped + vs_chars_escaped,
                                            'vs_name': vs_name,
                                            'c_value': c_value,
                                            'unicode_code': unicode_code,
                                            'vs_code': vs_code
                                        }
                                        
                                        # VS別にグループ化
                                        if vs_name not in vs_groups:
                                            vs_groups[vs_name] = []
                                        vs_groups[vs_name].append(char_data)
                                        temp_chars.append(char_data)
                                        
                except ValueError:
                    continue
        
        print(f"✓ 収集完了: {len(temp_chars)}文字、{len(vs_groups)}種類のVS")
        
        # 第2段階: 段階的PUA配置戦略に基づくJavaScript生成
        print(f"\\n第2段階: 段階的PUA配置...")
        
        # VS優先度リスト（使用頻度降順）
        vs_priority = ["VS19", "VS18", "VS20", "VS17", "VS21", "VS22", "VS23", "VS24", "VS25", "VS26", "VS27", "VS28", "VS29", "VS30", "VS31", "VS32"]
        
        bmp_pua_current = bmp_pua_start  # 0xE000
        smp_pua_current = smp_pua_start  # 0xF0000
        bmp_pua_end = 0xF8FF
        bmp_pua_allocated = 0
        smp_pua_allocated = 0
        
        # 段階的配置によるJavaScriptマッピング生成
        for vs_name in vs_priority:
            if vs_name in vs_groups:
                chars_in_vs = vs_groups[vs_name]
                
                if vs_name in ["VS19", "VS18"]:
                    # 全てBMP PUAに配置
                    for char_data in chars_in_vs:
                        if bmp_pua_current <= bmp_pua_end:
                            pua_char = "\\\\u{:04X}".format(bmp_pua_current)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            bmp_pua_current += 1
                            bmp_pua_allocated += 1
                        else:
                            # BMP PUA領域が満杯の場合、SMP PUAに移行（サロゲートペア）
                            high = ((smp_pua_current - 0x10000) >> 10) + 0xD800
                            low = ((smp_pua_current - 0x10000) & 0x3FF) + 0xDC00
                            pua_char = "\\\\u{:04X}\\\\u{:04X}".format(high, low)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            smp_pua_current += 1
                            smp_pua_allocated += 1
                    
                    print(f"✓ {vs_name}: {len(chars_in_vs):,}文字 → BMP PUA")
                    
                elif vs_name == "VS20":
                    # VS20は部分的配置
                    bmp_portion = min(len(chars_in_vs), bmp_pua_end - bmp_pua_current + 1)
                    
                    for i, char_data in enumerate(chars_in_vs):
                        if i < bmp_portion and bmp_pua_current <= bmp_pua_end:
                            # BMP PUAに配置
                            pua_char = "\\\\u{:04X}".format(bmp_pua_current)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            bmp_pua_current += 1
                            bmp_pua_allocated += 1
                        else:
                            # SMP PUAに配置（サロゲートペア）
                            high = ((smp_pua_current - 0x10000) >> 10) + 0xD800
                            low = ((smp_pua_current - 0x10000) & 0x3FF) + 0xDC00
                            pua_char = "\\\\u{:04X}\\\\u{:04X}".format(high, low)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            smp_pua_current += 1
                            smp_pua_allocated += 1
                    
                    print(f"⚠ {vs_name}: {bmp_portion:,}文字 → BMP PUA, {len(chars_in_vs)-bmp_portion:,}文字 → SMP PUA")
                    
                else:
                    # VS17, VS21以降は全てSMP PUAに配置（サロゲートペア）
                    for char_data in chars_in_vs:
                        high = ((smp_pua_current - 0x10000) >> 10) + 0xD800
                        low = ((smp_pua_current - 0x10000) & 0x3FF) + 0xDC00
                        pua_char = "\\\\u{:04X}\\\\u{:04X}".format(high, low)
                        js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                        smp_pua_current += 1
                        smp_pua_allocated += 1
                    
                    print(f"→ {vs_name}: {len(chars_in_vs):,}文字 → SMP PUA")
        
        print(f"\\nJavaScript配置完了:")
        print(f"BMP PUA: {bmp_pua_allocated:,}文字 (0x{bmp_pua_start:04X}-0x{bmp_pua_current-1:04X})")
        print(f"SMP PUA: {smp_pua_allocated:,}文字 (0x{smp_pua_start:05X}-0x{smp_pua_current-1:05X})")
        print(f"総マッピング数: {len(js_mappings):,}")
        
        # JavaScript内容を生成（SMP文字対応ユーティリティ付き）
        js_content = """// IVS文字マッピング定義（段階的PUA配置対応）
// BMP PUA: 0xE000-0xF8FF (6,400文字) - 高頻度VS優先
// SMP PUA: 0xF0000- (65,534文字) - 残りのVS

// SMP文字変換ユーティリティ
export function convertSMPToString(codePoint) {
    if (codePoint > 0xFFFF) {
        // サロゲートペアに変換
        const high = Math.floor((codePoint - 0x10000) / 0x400) + 0xD800;
        const low = ((codePoint - 0x10000) % 0x400) + 0xDC00;
        return String.fromCharCode(high, low);
    }
    return String.fromCharCode(codePoint);
}

// PUA文字の平面判定
export function getPUAPlane(puaChar) {
    const codePoint = puaChar.codePointAt(0);
    if (codePoint >= 0xE000 && codePoint <= 0xF8FF) {
        return 'BMP';
    } else if (codePoint >= 0xF0000 && codePoint <= 0xFFFFD) {
        return 'SMP_P15';
    } else if (codePoint >= 0x100000 && codePoint <= 0x10FFFD) {
        return 'SMP_P16';
    }
    return 'UNKNOWN';
}

// IVS→PUA変換（段階的配置対応）
export function convertIVSText(text) {
    return text.replace(/[\\\\u3400-\\\\u9fff][\\\\uDB40-\\\\uDB7F][\\\\uDC00-\\\\uDFFF]/g, 
        match => ivsToExternalCharMap[match] || match);
}

export const ivsToExternalCharMap = {
"""
        js_content += "\\n".join(js_mappings)
        js_content += "\\n};\\n"
        
        # 配置統計をJSに追加
        js_content += f"""
// 配置統計（段階的PUA戦略）
export const puaAllocationStats = {{
    strategy: 'staged_pua_allocation',
    bmpPUA: {{
        allocated: {bmp_pua_allocated},
        capacity: 6400,
        range: '0x{bmp_pua_start:04X}-0x{bmp_pua_current-1:04X}'
    }},
    smpPUA: {{
        allocated: {smp_pua_allocated},
        capacity: 65534,
        range: '0x{smp_pua_start:05X}-0x{smp_pua_current-1:05X}'
    }},
    totalCharacters: {len(js_mappings)}
}};
"""
        
        # ファイルに出力
        os.makedirs("../src/utils", exist_ok=True)
        with open("../src/utils/ivsCharacterMap.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        
        print(f"IVS文字マッピング定義ファイルを作成しました: src/utils/ivsCharacterMap.js")
        print(f"総マッピング数: {len(js_mappings)}")
        
    except Exception as e:
        print(f"マッピングファイル生成エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("MJ文字図形名ベースのIVS文字外字フォント作成スクリプト")
    print("=" * 50)
    
    # IVS文字を抽出
    if extract_ivs_glyphs():
        print("✓ IVS文字の抽出が完了しました")
    else:
        print("✗ IVS文字の抽出に失敗しました")
        sys.exit(1)
    
    # マッピングファイルを生成
    generate_mapping_file()
    print("✓ マッピングファイルの生成が完了しました")
    
    print("\\n完了! 次のステップ:")
    print("1. Vue.jsアプリケーションでIVS文字変換機能を実装")
    print("2. ActiveReportsJSで外字フォントを登録")
    print("3. PDF生成のテスト")
'''
        
        # ファイルに書き込み
        with open("extract_ivs_glyphs_mj_based.py", 'w', encoding='utf-8') as f:
            f.write(python_code)
        
        print(f"\\nMJベースの抽出スクリプトを作成しました: extract_ivs_glyphs_mj_based.py")
        
        # 統計情報を保存
        stats = {
            "total_ivs_to_mj_mappings": len(ivs_to_mj_mapping),
            "total_ivs_mappings": len(ivs_mappings),
            "bmp_pua_start": hex(bmp_pua_start),
            "bmp_pua_end": hex(bmp_pua_current-1),
            "smp_pua_start": hex(smp_pua_start),
            "smp_pua_end": hex(smp_pua_current-1),
            "bmp_pua_allocated": bmp_pua_allocated,
            "smp_pua_allocated": smp_pua_allocated,
            "allocation_strategy": "staged_pua_allocation",
            "sample_mappings": {
                repr(k): v for k, v in list(ivs_to_mj_mapping.items())[:10]
            }
        }
        
        with open("../mj_based_extraction_stats.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"統計情報を保存しました: mj_based_extraction_stats.json")
        
        return ivs_to_mj_mapping
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("MJ文字図形名ベースのIVS抽出スクリプト作成")
    print("=" * 50)
    
    result = create_mj_based_extraction()
    
    if result:
        print("\\n✓ MJベースの抽出スクリプトの作成が完了しました")
        print(f"総マッピング数: {len(result)}")
        print("\\n改善点:")
        print("- 基本文字ではなくMJ文字図形名を使用")
        print("- 各IVS文字の正しい字形を抽出")
        print("- フォント内のグリフ名を事前確認")
    else:
        print("\\n✗ MJベースの抽出スクリプトの作成に失敗しました")