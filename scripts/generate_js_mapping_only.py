#!/usr/bin/env python3
"""
段階的PUA配置に対応したJavaScriptマッピングファイルのみを生成
"""
import json
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, '..'))


def _escape_js_codepoint(cp: int) -> str:
    """Return JS escaped string for a single Unicode code point (handles BMP/SMP)."""
    if cp <= 0xFFFF:
        return "\\u{:04X}".format(cp)
    high = ((cp - 0x10000) >> 10) + 0xD800
    low = ((cp - 0x10000) & 0x3FF) + 0xDC00
    return "\\u{:04X}\\u{:04X}".format(high, low)


def generate_mapping_file():
    """IVS文字マッピング定義ファイルを生成（段階的PUA配置対応）"""
    
    try:
        with open(os.path.join(_ROOT_DIR, "mji_analysis_f_to_c_mapping.json"), 'r', encoding='utf-8') as f:
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
        # 生成後に参照するための辞書: (base_cp, vs_cp) -> escaped PUA string
        ivs_to_pua = {}
        
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
                                            base_char_escaped = "\\u{:04X}".format(unicode_code)
                                        else:
                                            # SMP文字はサロゲートペアとして表現
                                            high = ((unicode_code - 0x10000) >> 10) + 0xD800
                                            low = ((unicode_code - 0x10000) & 0x3FF) + 0xDC00
                                            base_char_escaped = "\\u{:04X}\\u{:04X}".format(high, low)
                                        
                                        # サロゲートペアを計算
                                        high_surrogate = ((vs_code - 0x10000) >> 10) + 0xD800
                                        low_surrogate = ((vs_code - 0x10000) & 0x3FF) + 0xDC00
                                        
                                        vs_chars_escaped = "\\u{:04X}\\u{:04X}".format(high_surrogate, low_surrogate)
                                        
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
        print(f"\n第2段階: 段階的PUA配置...")
        
        # VS優先度リスト（使用頻度降順）
        # 既定で VS19, VS18 を最優先、次に VS20、残りは VS番号昇順で網羅（VS33+を含む）
        known_priority = ["VS19", "VS18", "VS20"]
        others = sorted([vn for vn in vs_groups.keys() if vn not in known_priority], key=lambda x: int(x[2:]))
        vs_priority = known_priority + others
        
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
                            pua_char = "\\u{:04X}".format(bmp_pua_current)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            ivs_to_pua[(char_data['unicode_code'], char_data['vs_code'])] = pua_char
                            bmp_pua_current += 1
                            bmp_pua_allocated += 1
                        else:
                            # BMP PUA領域が満杯の場合、SMP PUAに移行（サロゲートペア）
                            high = ((smp_pua_current - 0x10000) >> 10) + 0xD800
                            low = ((smp_pua_current - 0x10000) & 0x3FF) + 0xDC00
                            pua_char = "\\u{:04X}\\u{:04X}".format(high, low)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            ivs_to_pua[(char_data['unicode_code'], char_data['vs_code'])] = pua_char
                            smp_pua_current += 1
                            smp_pua_allocated += 1
                    
                    print(f"✓ {vs_name}: {len(chars_in_vs):,}文字 → BMP PUA")
                    
                elif vs_name == "VS20":
                    # VS20は部分的配置
                    bmp_portion = min(len(chars_in_vs), bmp_pua_end - bmp_pua_current + 1)
                    
                    for i, char_data in enumerate(chars_in_vs):
                        if i < bmp_portion and bmp_pua_current <= bmp_pua_end:
                            # BMP PUAに配置
                            pua_char = "\\u{:04X}".format(bmp_pua_current)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            ivs_to_pua[(char_data['unicode_code'], char_data['vs_code'])] = pua_char
                            bmp_pua_current += 1
                            bmp_pua_allocated += 1
                        else:
                            # SMP PUAに配置（サロゲートペア）
                            high = ((smp_pua_current - 0x10000) >> 10) + 0xD800
                            low = ((smp_pua_current - 0x10000) & 0x3FF) + 0xDC00
                            pua_char = "\\u{:04X}\\u{:04X}".format(high, low)
                            js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                            ivs_to_pua[(char_data['unicode_code'], char_data['vs_code'])] = pua_char
                            smp_pua_current += 1
                            smp_pua_allocated += 1
                    
                    print(f"⚠ {vs_name}: {bmp_portion:,}文字 → BMP PUA, {len(chars_in_vs)-bmp_portion:,}文字 → SMP PUA")
                    
                else:
                    # VS17, VS21以降は全てSMP PUAに配置（サロゲートペア）
                    for char_data in chars_in_vs:
                        high = ((smp_pua_current - 0x10000) >> 10) + 0xD800
                        low = ((smp_pua_current - 0x10000) & 0x3FF) + 0xDC00
                        pua_char = "\\u{:04X}\\u{:04X}".format(high, low)
                        js_mappings.append(f"  '{char_data['ivs_sequence']}': '{pua_char}',  // {char_data['c_value']}")
                        ivs_to_pua[(char_data['unicode_code'], char_data['vs_code'])] = pua_char
                        smp_pua_current += 1
                        smp_pua_allocated += 1
                    
                    print(f"→ {vs_name}: {len(chars_in_vs):,}文字 → SMP PUA")
        
        print(f"\nJavaScript配置完了:")
        print(f"BMP PUA: {bmp_pua_allocated:,}文字 (0x{bmp_pua_start:04X}-0x{bmp_pua_current-1:04X})")
        print(f"SMP PUA: {smp_pua_allocated:,}文字 (0x{smp_pua_start:05X}-0x{smp_pua_current-1:05X})")
        print(f"総マッピング数: {len(js_mappings):,}")
        
        # JavaScript内容を生成（マッピングデータ + フォールバック + 統計）
        js_content = """// IVS文字マッピング定義（段階的PUA配置対応）
// BMP PUA: 0xE000-0xF8FF (6,400文字) - 高頻度VS優先
// SMP PUA: 0xF0000- (65,534文字) - 残りのVS

export const ivsToExternalCharMap = {
"""
        js_content += "\n".join(js_mappings)
        js_content += "\n};\n"

        # 既定異体（B_value）フォールバック: base_char -> 対応する既定異体PUA
        # data[*]['base_f_tag'] 例) '9089_E010F' を (base, vs) に分解し、ivs_to_pua からPUAを引く
        fallback_entries = []
        for unicode_key, entry in data.items():
            try:
                if not unicode_key.startswith('U+'):
                    continue
                base_cp = int(unicode_key[2:], 16)
                ftag = entry.get('base_f_tag')
                if not ftag or ';' in ftag:
                    continue  # 複合タグは対象外
                base_hex, vs_hex = ftag.split('_', 1)
                # 安全確認
                if int(base_hex, 16) != base_cp:
                    continue
                vs_cp = int(vs_hex, 16)
                pua = ivs_to_pua.get((base_cp, vs_cp))
                if not pua:
                    continue
                base_escaped = _escape_js_codepoint(base_cp)
                fallback_entries.append(f"  '{base_escaped}': '{pua}'")
            except Exception:
                continue

        js_content += "\nexport const baseCharFallbackToExternalMap = {\n"
        js_content += ",\n".join(fallback_entries)
        js_content += "\n};\n"
        
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
        os.makedirs(os.path.join(_ROOT_DIR, "src", "utils"), exist_ok=True)
        with open(os.path.join(_ROOT_DIR, "src", "utils", "ivsCharacterMap.js"), "w", encoding="utf-8") as f:
            f.write(js_content)
        
        print(f"IVS文字マッピング定義ファイルを作成しました: src/utils/ivsCharacterMap.js")
        print(f"総マッピング数: {len(js_mappings)}")
        
        return True
        
    except Exception as e:
        print(f"マッピングファイル生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("段階的PUA配置対応 JavaScriptマッピング生成")
    print("=" * 50)
    
    if generate_mapping_file():
        print("\n✅ JavaScriptマッピングファイルの生成が完了しました")
    else:
        print("\n❌ JavaScriptマッピングファイルの生成に失敗しました")
