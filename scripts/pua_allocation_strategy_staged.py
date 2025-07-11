#!/usr/bin/env python3
"""
段階的PUA配置戦略の実装
BMP PUA (0xE000-0xF8FF) と SMP PUA (0xF0000-) の二段階配置
"""

def get_staged_pua_strategy():
    """段階的PUA配置戦略の定義"""
    return {
        "bmp_pua": {
            "start": 0xE000,
            "end": 0xF8FF,
            "capacity": 6400,
            "description": "BMP Private Use Area - 高頻度VS文字優先",
            "priority_vs": ["VS19", "VS18", "VS20_partial"]
        },
        "smp_pua": {
            "start": 0xF0000,
            "end": 0xFFFFD,
            "capacity": 65534,
            "description": "SMP Plane 15 Private Use Area - 残りの文字",
            "contains_vs": ["VS20_remaining", "VS17", "VS21", "VS22", "VS23", "VS24+"]
        }
    }

def analyze_vs_distribution(stats_file="static_font_test_stats.json"):
    """VS分布を分析してBMP PUA配置計画を作成"""
    import json
    
    try:
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        vs_distribution = stats.get('vs_distribution', {})
        total_chars = stats.get('total_characters', 0)
        
        print("VS分布分析:")
        print("=" * 50)
        
        # VS別の文字数を降順でソート
        sorted_vs = sorted(vs_distribution.items(), key=lambda x: x[1], reverse=True)
        
        bmp_pua_capacity = 6400
        bmp_allocation = []
        smp_allocation = []
        
        current_bmp_used = 0
        
        for vs_name, count in sorted_vs:
            if vs_name == "VS?":  # 不明なVSはスキップ
                smp_allocation.append((vs_name, count, "unknown"))
                continue
                
            if current_bmp_used + count <= bmp_pua_capacity:
                # BMP PUAに全て配置可能
                bmp_allocation.append((vs_name, count, "full"))
                current_bmp_used += count
                print(f"✓ {vs_name}: {count:,}文字 → BMP PUA (全て)")
            elif current_bmp_used < bmp_pua_capacity:
                # 部分的にBMP PUAに配置
                bmp_portion = bmp_pua_capacity - current_bmp_used
                smp_portion = count - bmp_portion
                bmp_allocation.append((vs_name, bmp_portion, "partial"))
                smp_allocation.append((vs_name, smp_portion, "remaining"))
                current_bmp_used = bmp_pua_capacity
                print(f"⚠ {vs_name}: {bmp_portion:,}文字 → BMP PUA, {smp_portion:,}文字 → SMP PUA")
            else:
                # SMP PUAに配置
                smp_allocation.append((vs_name, count, "full"))
                print(f"→ {vs_name}: {count:,}文字 → SMP PUA")
        
        print(f"\n配置結果:")
        print(f"BMP PUA使用: {current_bmp_used:,}/{bmp_pua_capacity:,}文字")
        print(f"SMP PUA使用: {sum(count for _, count, _ in smp_allocation):,}文字")
        
        return {
            "bmp_allocation": bmp_allocation,
            "smp_allocation": smp_allocation,
            "bmp_used": current_bmp_used,
            "smp_used": sum(count for _, count, _ in smp_allocation),
            "total_chars": total_chars
        }
        
    except Exception as e:
        print(f"エラー: VS分布分析に失敗 - {e}")
        return None

def generate_pua_allocation_map(ivs_characters):
    """IVS文字に段階的PUAコードを割り当て"""
    
    # VS分布分析
    analysis = analyze_vs_distribution()
    if not analysis:
        return None
    
    # PUA配置の初期設定
    bmp_pua_current = 0xE000
    smp_pua_current = 0xF0000
    
    pua_allocation_map = {}
    
    print(f"\nPUAコード割り当て開始:")
    print("=" * 50)
    
    # BMP PUA優先配置
    for vs_name, count, allocation_type in analysis['bmp_allocation']:
        vs_chars = [char for char in ivs_characters if char.get('vs_name') == vs_name]
        
        if allocation_type == "full":
            # 全てBMP PUAに配置
            for char in vs_chars:
                pua_allocation_map[char['ivs_sequence']] = {
                    'pua_code': bmp_pua_current,
                    'pua_hex': f"U+{bmp_pua_current:04X}",
                    'pua_plane': 'BMP',
                    'vs_name': vs_name,
                    'base_char': char['base_char'],
                    'mj_number': char['mj_number']
                }
                bmp_pua_current += 1
            print(f"✓ {vs_name}: {len(vs_chars):,}文字 → BMP PUA")
            
        elif allocation_type == "partial":
            # 部分的にBMP PUAに配置
            for i, char in enumerate(vs_chars):
                if i < count:  # count分だけBMP PUAに配置
                    pua_allocation_map[char['ivs_sequence']] = {
                        'pua_code': bmp_pua_current,
                        'pua_hex': f"U+{bmp_pua_current:04X}",
                        'pua_plane': 'BMP',
                        'vs_name': vs_name,
                        'base_char': char['base_char'],
                        'mj_number': char['mj_number']
                    }
                    bmp_pua_current += 1
            print(f"⚠ {vs_name}: {count:,}文字 → BMP PUA (部分)")
    
    # SMP PUA配置
    for vs_name, count, allocation_type in analysis['smp_allocation']:
        if allocation_type == "remaining":
            # VS20の残り分
            vs_chars = [char for char in ivs_characters if char.get('vs_name') == vs_name]
            allocated_count = len([seq for seq in pua_allocation_map if pua_allocation_map[seq]['vs_name'] == vs_name])
            remaining_chars = vs_chars[allocated_count:]
            
            for char in remaining_chars:
                pua_allocation_map[char['ivs_sequence']] = {
                    'pua_code': smp_pua_current,
                    'pua_hex': f"U+{smp_pua_current:05X}",
                    'pua_plane': 'SMP_P15',
                    'vs_name': vs_name,
                    'base_char': char['base_char'],
                    'mj_number': char['mj_number']
                }
                smp_pua_current += 1
            print(f"→ {vs_name}: {len(remaining_chars):,}文字 → SMP PUA (残り)")
            
        else:
            # 全てSMP PUAに配置
            vs_chars = [char for char in ivs_characters if char.get('vs_name') == vs_name]
            for char in vs_chars:
                pua_allocation_map[char['ivs_sequence']] = {
                    'pua_code': smp_pua_current,
                    'pua_hex': f"U+{smp_pua_current:05X}",
                    'pua_plane': 'SMP_P15',
                    'vs_name': vs_name,
                    'base_char': char['base_char'],
                    'mj_number': char['mj_number']
                }
                smp_pua_current += 1
            print(f"→ {vs_name}: {len(vs_chars):,}文字 → SMP PUA")
    
    print(f"\n配置完了:")
    print(f"BMP PUA: {bmp_pua_current - 0xE000:,}文字 (0xE000-0x{bmp_pua_current-1:04X})")
    print(f"SMP PUA: {smp_pua_current - 0xF0000:,}文字 (0xF0000-0x{smp_pua_current-1:05X})")
    print(f"総文字数: {len(pua_allocation_map):,}文字")
    
    return pua_allocation_map

def save_staged_pua_mapping(pua_allocation_map, output_file="staged_pua_mappings.json"):
    """段階的PUAマッピングをJSONファイルに保存"""
    import json
    
    try:
        # 統計情報を計算
        bmp_count = len([x for x in pua_allocation_map.values() if x['pua_plane'] == 'BMP'])
        smp_count = len([x for x in pua_allocation_map.values() if x['pua_plane'] == 'SMP_P15'])
        
        output_data = {
            "mapping_strategy": "staged_pua_allocation",
            "generation_timestamp": "2025-07-12",
            "statistics": {
                "total_characters": len(pua_allocation_map),
                "bmp_pua_characters": bmp_count,
                "smp_pua_characters": smp_count,
                "bmp_pua_range": "0xE000-0xF8FF",
                "smp_pua_range": "0xF0000-0xFFFFD"
            },
            "mappings": pua_allocation_map
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 段階的PUAマッピングを保存: {output_file}")
        return True
        
    except Exception as e:
        print(f"✗ エラー: マッピング保存に失敗 - {e}")
        return False

if __name__ == "__main__":
    print("段階的PUA配置戦略分析")
    print("=" * 50)
    
    # VS分布分析の実行
    analysis = analyze_vs_distribution()
    
    if analysis:
        print(f"\n✓ 分析完了: BMP PUA {analysis['bmp_used']:,}文字, SMP PUA {analysis['smp_used']:,}文字")
    else:
        print("✗ 分析に失敗しました")