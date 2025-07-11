#!/usr/bin/env python3
"""
静的なfont-test.htmlを生成するスクリプト
ivsCharacterMap.jsを解析してHTMLに直接データを埋め込み
"""
import json
import re
import os

def generate_static_font_test():
    """静的なfont-test.htmlを生成"""
    
    print("静的Font Test HTMLページを生成中...")
    print("=" * 50)
    
    # ivsCharacterMap.jsを読み込んで解析
    ivs_mapping_file = "../src/utils/ivsCharacterMap.js"
    
    if not os.path.exists(ivs_mapping_file):
        print(f"✗ エラー: {ivs_mapping_file} が見つかりません")
        return False
    
    try:
        with open(ivs_mapping_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        print(f"✓ {ivs_mapping_file} を読み込みました")
        
        # JavaScript形式のマッピングを解析
        character_data = []
        
        # 新しいJavaScriptファイル形式に対応
        # ivsToExternalCharMapオブジェクトのみを抽出
        import_start = js_content.find("export const ivsToExternalCharMap = {")
        if import_start == -1:
            print("✗ エラー: ivsToExternalCharMapが見つかりません")
            return False
        
        import_end = js_content.find("\n};", import_start)
        if import_end == -1:
            print("✗ エラー: ivsToExternalCharMapの終端が見つかりません")
            return False
        
        # ivsToExternalCharMapの中身のみを抽出
        mapping_content = js_content[import_start:import_end + 3]
        
        # 正規表現でマッピングエントリを抽出
        # 形式: '\\u3404\\uDB40\\uDD01': '\\uE200',  // MJ000007
        pattern = r"'([^']+)':\s*'([^']+)',\s*//\s*(.*)"
        matches = re.findall(pattern, mapping_content)
        
        print(f"✓ {len(matches)} 個のマッピングエントリを発見")
        
        for i, (ivs_sequence, pua_char, comment) in enumerate(matches):
            # Unicode エスケープ文字列を実際の文字に変換
            try:
                # \\uXXXX 形式を実際のUnicode文字に変換
                ivs_actual = ivs_sequence.encode().decode('unicode-escape')
                pua_actual = pua_char.encode().decode('unicode-escape')
                
                base_char = ivs_actual[0] if ivs_actual else '?'
                base_unicode = ord(base_char)
                
                # PUA文字のコードポイントを取得（SMP文字対応）
                if len(pua_actual) == 1:
                    # BMP文字
                    pua_code = ord(pua_actual)
                elif len(pua_actual) == 2:
                    # サロゲートペア（SMP文字）
                    high = ord(pua_actual[0])
                    low = ord(pua_actual[1])
                    if 0xD800 <= high <= 0xDBFF and 0xDC00 <= low <= 0xDFFF:
                        pua_code = ((high - 0xD800) << 10) + (low - 0xDC00) + 0x10000
                    else:
                        pua_code = ord(pua_actual[0])  # フォールバック
                else:
                    pua_code = ord(pua_actual[0])  # フォールバック
                    
            except Exception as e:
                print(f"  警告: 文字変換エラー - {ivs_sequence} -> {e}")
                continue
            
            # VSを判定（サロゲートペアから）
            vs_name = 'VS?'
            if len(ivs_actual) >= 3:
                try:
                    # UTF-16サロゲートペアをデコード
                    high = ord(ivs_actual[1])
                    low = ord(ivs_actual[2])
                    if 0xDB40 <= high <= 0xDB40 and 0xDD00 <= low <= 0xDDEF:
                        vs_code = ((high - 0xDB40) << 10) + (low - 0xDD00) + 0xE0100
                        vs_num = vs_code - 0xE0100 + 17
                        vs_name = f"VS{vs_num}"
                except:
                    pass
            
            # MJ番号をコメントから抽出
            mj_match = re.search(r'(MJ\d+)', comment)
            mj_number = mj_match.group(1) if mj_match else 'MJ??????'
            
            character_data.append({
                'ivs_sequence': ivs_actual,
                'pua_char': pua_actual,
                'base_char': base_char,
                'base_unicode': f"U+{base_unicode:04X}",
                'vs_name': vs_name,
                'mj_number': mj_number,
                'pua_code': f"U+{pua_code:04X}",
                'comment': comment.strip()
            })
            
            if i < 10:  # 最初の10個をサンプル表示
                print(f"  {base_char} {vs_name} -> {pua_actual} ({mj_number})")
        
        print(f"✓ {len(character_data)} 個の文字データを処理しました")
        
        # 統計情報を計算
        total_count = len(character_data)
        unique_base_chars = len(set(item['base_char'] for item in character_data))
        vs_counts = {}
        for item in character_data:
            vs = item['vs_name']
            vs_counts[vs] = vs_counts.get(vs, 0) + 1
        
        print(f"✓ 統計: 総数={total_count}, 基本文字数={unique_base_chars}")
        
    except Exception as e:
        print(f"✗ エラー: {ivs_mapping_file} の解析に失敗 - {e}")
        return False
    
    # HTMLテンプレートを生成
    html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IVS外字フォントテストビュー（静的版）</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        
        .header p {{
            margin: 10px 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .control-group label {{
            font-weight: 500;
            color: #495057;
        }}
        
        select, input {{
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .stats {{
            background: #e3f2fd;
            padding: 15px 30px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            flex-wrap: wrap;
            gap: 30px;
        }}
        
        .stat-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .stat-number {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #1976d2;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
        }}
        
        .table-container {{
            padding: 30px;
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .character-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        .character-table th {{
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .character-table td {{
            padding: 12px 8px;
            border-bottom: 1px solid #e9ecef;
            vertical-align: middle;
        }}
        
        .character-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .char-display {{
            font-size: 24px;
            text-align: center;
            min-width: 40px;
        }}
        
        .ivs-char {{
            font-family: 'IPAMincho';
            color: #28a745;
            font-weight: 500;
        }}
        
        .pua-char {{
            font-family: 'IPA-IVS-External';
            color: #dc3545;
            font-weight: 500;
        }}
        
        .mj-code {{
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }}
        
        .unicode-code {{
            font-family: 'Courier New', monospace;
            color: #6c757d;
            font-size: 12px;
        }}
        
        .vs-badge {{
            background: #17a2b8;
            color: white;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        .font-notice {{
            background: #fff3cd;
            color: #856404;
            padding: 15px 30px;
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
        }}
        
        .generation-info {{
            background: #d1ecf1;
            color: #0c5460;
            padding: 15px 30px;
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
        }}

        @font-face {{
          font-family: 'IPAMincho';
          src: url('./fonts/ipam.ttf') format('truetype');
          font-weight: normal;
          font-style: normal;
        }}
        
        @font-face {{
            font-family: 'IPA-IVS-External';
            src: url('./fonts/ipa-ivs-external.woff2') format('woff2'),
                 url('./fonts/ipa-ivs-external.ttf') format('truetype');
            font-display: swap;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .controls {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .stats {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .table-container {{
                padding: 15px;
                overflow-x: auto;
            }}
            
            .character-table {{
                min-width: 600px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>IVS外字フォントテストビュー</h1>
        </header>
        
        <div class="controls">
            <div class="control-group">
                <label for="fontSizeSelect">フォントサイズ:</label>
                <select id="fontSizeSelect">
                    <option value="16">16px</option>
                    <option value="20">20px</option>
                    <option value="24" selected>24px</option>
                    <option value="28">28px</option>
                    <option value="32">32px</option>
                </select>
            </div>
            
            <div class="control-group">
                <label for="filterInput">フィルタ (MJ番号/Unicode):</label>
                <input type="text" id="filterInput" placeholder="mj000007, U+3404, など">
            </div>
            
            <div class="control-group">
                <label for="vsFilter">バリエーションセレクタ:</label>
                <select id="vsFilter">
                    <option value="">全て</option>'''
    
    # VSフィルタオプションを動的生成
    vs_options = sorted(set(item['vs_name'] for item in character_data if item['vs_name'] != 'VS?'))
    for vs in vs_options:
        html_content += f'\n                    <option value="{vs}">{vs}</option>'
    
    html_content += f'''
                </select>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="totalCount">{total_count:,}</div>
                <div class="stat-label">総文字数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="filteredCount">{total_count:,}</div>
                <div class="stat-label">表示中</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="uniqueBaseCount">{unique_base_chars:,}</div>
                <div class="stat-label">基本文字数</div>
            </div>
        </div>
        
        <div class="table-container">
            <table class="character-table" id="characterTable">
                <thead>
                    <tr>
                        <th>IVS文字</th>
                        <th>PUA文字</th>
                        <th>基本文字</th>
                        <th>VS</th>
                        <th>MJ番号</th>
                        <th>Unicode</th>
                        <th>PUAコード</th>
                    </tr>
                </thead>
                <tbody id="characterTableBody">'''
    
    # テーブル行は空でスタート（JavaScriptで動的生成）
    
    html_content += '''
                </tbody>
            </table>
        </div>
    </div>

    <script>'''
    
    # JavaScriptデータを安全にエスケープして埋め込み
    js_character_data = []
    for item in character_data:
        # Unicode文字をJavaScript形式でエスケープ
        ivs_js = repr(item['ivs_sequence'])
        pua_js = repr(item['pua_char'])
        base_js = repr(item['base_char'])
        
        js_item = f'{{ivsSequence: {ivs_js}, puaChar: {pua_js}, baseChar: {base_js}, baseUnicode: "{item["base_unicode"]}", vsName: "{item["vs_name"]}", mjNumber: "{item["mj_number"]}", puaCode: "{item["pua_code"]}"}}'
        js_character_data.append(js_item)
    
    js_data_str = ', '.join(js_character_data)
    
    html_content += f'''
        // 静的データ（Pythonから生成）
        const characterData = [
            {js_data_str}
        ];
        
        let allRows = [];
        let filteredRows = [];

        function updateStats() {{
            const totalCount = characterData.length;
            const filteredCount = filteredRows.length;
            const uniqueBaseChars = new Set(filteredRows.map(item => item.baseChar)).size;
            
            document.getElementById('totalCount').textContent = totalCount.toLocaleString();
            document.getElementById('filteredCount').textContent = filteredCount.toLocaleString();
            document.getElementById('uniqueBaseCount').textContent = uniqueBaseChars.toLocaleString();
        }}

        function applyFilter() {{
            const filterText = document.getElementById('filterInput').value.toLowerCase();
            const vsFilter = document.getElementById('vsFilter').value;
            
            filteredRows = characterData.filter(item => {{
                // テキストフィルタ
                const textMatch = !filterText || 
                    item.mjNumber.toLowerCase().includes(filterText) ||
                    item.baseUnicode.toLowerCase().includes(filterText) ||
                    item.baseChar.includes(filterText);
                
                // VSフィルタ
                const vsMatch = !vsFilter || item.vsName === vsFilter;
                
                return textMatch && vsMatch;
            }});
            
            renderTable();
            updateStats();
        }}

        function renderTable() {{
            const tbody = document.getElementById('characterTableBody');
            const fontSize = document.getElementById('fontSizeSelect').value;
            
            tbody.innerHTML = '';
            
            filteredRows.forEach(item => {{
                const row = document.createElement('tr');
                row.innerHTML = 
                    '<td><div class="char-display ivs-char" style="font-size: ' + fontSize + 'px;">' + item.ivsSequence + '</div></td>' +
                    '<td><div class="char-display pua-char" style="font-size: ' + fontSize + 'px;">' + item.puaChar + '</div></td>' +
                    '<td><div class="char-display" style="font-size: ' + fontSize + 'px;">' + item.baseChar + '</div></td>' +
                    '<td><span class="vs-badge">' + item.vsName + '</span></td>' +
                    '<td><span class="mj-code">' + item.mjNumber + '</span></td>' +
                    '<td><span class="unicode-code">' + item.baseUnicode + '</span></td>' +
                    '<td><span class="unicode-code">' + item.puaCode + '</span></td>';
                tbody.appendChild(row);
            }});
        }}

        // イベントリスナーを設定
        function setupEventListeners() {{
            document.getElementById('fontSizeSelect').addEventListener('change', renderTable);
            document.getElementById('filterInput').addEventListener('input', applyFilter);
            document.getElementById('vsFilter').addEventListener('change', applyFilter);
        }}

        // 初期化
        function initialize() {{
            setupEventListeners();
            filteredRows = [...characterData];
            updateStats();
            renderTable();
        }}

        // ページ読み込み完了後に初期化
        document.addEventListener('DOMContentLoaded', initialize);
    </script>
</body>
</html>'''
    
    # 静的HTMLファイルを保存
    output_file = "../public/font-test-static.html"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ 静的HTMLファイルを生成しました: {output_file}")
        print(f"  - 総文字数: {total_count:,}")
        print(f"  - 基本文字数: {unique_base_chars:,}")
        print(f"  - ファイルサイズ: {len(html_content)/1024/1024:.1f}MB")
        
        # 統計情報も保存
        stats = {
            "generation_timestamp": "2025-07-12",
            "source_file": ivs_mapping_file,
            "output_file": output_file,
            "total_characters": total_count,
            "unique_base_characters": unique_base_chars,
            "vs_distribution": vs_counts,
            "file_size_mb": round(len(html_content)/1024/1024, 2)
        }
        
        with open("../static_font_test_stats.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 統計情報を保存しました: static_font_test_stats.json")
        
        return True
        
    except Exception as e:
        print(f"✗ エラー: HTMLファイルの保存に失敗 - {e}")
        return False

if __name__ == "__main__":
    print("静的Font Test HTMLページ生成スクリプト")
    print("=" * 50)
    
    success = generate_static_font_test()
    
    if success:
        print("\n✓ 静的HTMLページの生成が完了しました")
        print("\n使用方法:")
        print("1. ブラウザで public/font-test-static.html を開く")
        print("2. フィルタ機能を使って文字を検索")
        print("3. フォントサイズを調整して表示確認")
    else:
        print("\n✗ 静的HTMLページの生成に失敗しました")
        exit(1)