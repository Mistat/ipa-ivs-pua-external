#!/usr/bin/env python3
"""
静的なfont-test.htmlを生成するスクリプト
ivsCharacterMap.jsを解析してHTMLに直接データを埋め込み
"""
import json
import re
import os
import datetime
import struct

def _read_u16(b, off):
    return struct.unpack_from('>H', b, off)[0]

def _read_u24(b, off):
    a, c = struct.unpack_from('>HB', b, off)
    return (a << 8) | c

def _read_u32(b, off):
    return struct.unpack_from('>I', b, off)[0]

def _find_table(buf, tag):
    # sfnt header: scaler type(4), numTables(2), searchRange(2), entrySelector(2), rangeShift(2)
    num = _read_u16(buf, 4)
    off = 12
    tag_val = tag.encode('ascii')
    if len(tag_val) != 4:
        return None, 0
    tag_u32 = struct.unpack('>I', tag_val)[0]
    for _ in range(num):
        tTag = _read_u32(buf, off)
        tOffset = _read_u32(buf, off + 8)
        tLength = _read_u32(buf, off + 12)
        if tTag == tag_u32:
            return tOffset, tLength
        off += 16
    return None, 0

def _build_has_cp_checker(font_path):
    try:
        with open(font_path, 'rb') as f:
            buf = f.read()
    except Exception:
        return lambda cp: False
    cmap_off, _ = _find_table(buf, 'cmap')
    if not cmap_off:
        return lambda cp: False
    numTables = _read_u16(buf, cmap_off + 2)
    format4 = None
    format12 = None
    for i in range(numTables):
        rec = cmap_off + 4 + i * 8
        platformID = _read_u16(buf, rec)
        subOffset = _read_u32(buf, rec + 4)
        subBase = cmap_off + subOffset
        fmt = _read_u16(buf, subBase)
        if fmt == 12 or (fmt == 0 and _read_u16(buf, subBase + 2) == 12):
            format12 = {'base': subBase}
        elif fmt == 4 and platformID == 3:
            format4 = {'base': subBase}
    def has_cp(cp: int) -> bool:
        # Try format 12 for SMP
        if cp > 0xFFFF and format12:
            b = format12['base']
            nGroups = _read_u32(buf, b + 12)
            lo, hi = 0, nGroups - 1
            off = b + 16
            while lo <= hi:
                mid = (lo + hi) >> 1
                m = off + mid * 12
                start = _read_u32(buf, m)
                end = _read_u32(buf, m + 4)
                if cp < start:
                    hi = mid - 1
                elif cp > end:
                    lo = mid + 1
                else:
                    startGlyphID = _read_u32(buf, m + 8)
                    gid = startGlyphID + (cp - start)
                    return gid != 0
        # Try format 4 for BMP
        if cp <= 0xFFFF and format4:
            b = format4['base']
            segCount = _read_u16(buf, b + 6) // 2
            endOff = b + 14
            startOff = endOff + segCount * 2 + 2
            idDeltaOff = startOff + segCount * 2
            idRangeOffsetOff = idDeltaOff + segCount * 2
            lo, hi = 0, segCount - 1
            while lo <= hi:
                mid = (lo + hi) >> 1
                endv = _read_u16(buf, endOff + mid * 2)
                if cp > endv:
                    lo = mid + 1
                else:
                    hi = mid - 1
            i = lo
            if i >= segCount:
                return False
            endv = _read_u16(buf, endOff + i * 2)
            startv = _read_u16(buf, startOff + i * 2)
            if cp < startv or cp > endv:
                return False
            idDelta = _read_u16(buf, idDeltaOff + i * 2)
            idRangeOffset = _read_u16(buf, idRangeOffsetOff + i * 2)
            if idRangeOffset == 0:
                gid = (cp + idDelta) & 0xFFFF
                return gid != 0
            roff = idRangeOffsetOff + i * 2 + idRangeOffset
            idx = (cp - startv) * 2
            glyphIndex = _read_u16(buf, roff + idx)
            if glyphIndex == 0:
                return False
            gid = (glyphIndex + idDelta) & 0xFFFF
            return gid != 0
        return False
    return has_cp

def generate_static_font_test():
    """静的なfont-test.htmlを生成"""
    
    print("静的Font Test HTMLページを生成中...")
    print("=" * 50)
    
    # 実行ディレクトリに依存せず、スクリプト位置からパスを解決
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.normpath(os.path.join(script_dir, '..'))

    # ivsCharacterMap.jsを読み込んで解析
    ivs_mapping_file = os.path.join(root_dir, 'src', 'utils', 'ivsCharacterMap.js')
    
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
        
        # 概念上の「基本文字があるか」を MJI の JSON から判定
        # U+XXXX → entry.F_to_C に ftag(XXXX_E01YY) が存在し値があれば「基本文字あり」
        mji_json_path = os.path.join(root_dir, 'mji_analysis_f_to_c_mapping.json')
        mji_data = {}
        try:
            with open(mji_json_path, 'r', encoding='utf-8') as jf:
                mji_data = json.load(jf)
        except Exception:
            mji_data = {}

        # 実際に ipam.ttf にグリフがあるか（描画可能か）も併せてチェック
        base_font_path = os.path.join(root_dir, 'fonts', 'ipam.ttf')
        has_base_cp = _build_has_cp_checker(base_font_path)

        for i, (ivs_sequence, pua_char, comment) in enumerate(matches):
            # Unicode エスケープ文字列を実際の文字に変換
            try:
                # \\uXXXX 形式を実際のUnicode文字に変換
                ivs_actual = ivs_sequence.encode().decode('unicode-escape')
                pua_actual = pua_char.encode().decode('unicode-escape')

                # 基本文字（SMPはサロゲート2文字連結で表示）とコードポイント
                base_text = '?'
                base_cp = None
                idx = 0
                if ivs_actual:
                    c0 = ord(ivs_actual[0])
                    if len(ivs_actual) >= 2 and 0xD800 <= c0 <= 0xDBFF and 0xDC00 <= ord(ivs_actual[1]) <= 0xDFFF:
                        c1 = ord(ivs_actual[1])
                        base_text = ivs_actual[0] + ivs_actual[1]
                        base_cp = ((c0 - 0xD800) << 10) + (c1 - 0xDC00) + 0x10000
                        idx = 2
                    else:
                        base_text = ivs_actual[0]
                        base_cp = c0
                        idx = 1

                # VSを判定（DB40/DDxx: E0100系, FE00..FE0F: VS1..VS16）
                vs_name = 'VS?'
                vs_code = None
                if len(ivs_actual) >= idx + 2:
                    h = ord(ivs_actual[idx])
                    l = ord(ivs_actual[idx + 1])
                    if 0xDB40 <= h <= 0xDB40 and 0xDD00 <= l <= 0xDDEF:
                        vs_code = 0xE0100 + (l - 0xDD00)
                        vs_num = (vs_code - 0xE0100) + 17
                        vs_name = f"VS{vs_num}"
                if vs_code is None and len(ivs_actual) >= idx + 1:
                    v = ord(ivs_actual[idx])
                    if 0xFE00 <= v <= 0xFE0F:
                        vs_code = v
                        vs_num = (v - 0xFE00) + 1
                        vs_name = f"VS{vs_num}"

                # MJI由来の論理的な有無（F_to_C があれば基本文字あり）
                base_exists_mji = False
                try:
                    ukey = f"U+{base_cp:X}" if base_cp is not None else None
                    entry = mji_data.get(ukey) or {}
                    f_to_c = entry.get('F_to_C') or {}
                    if vs_code and 0xE0100 <= vs_code <= 0xE01EF:
                        ftag = f"{base_cp:X}_{vs_code:X}"  # 例: 2B9E4_E0102
                        base_exists_mji = bool(f_to_c.get(ftag))
                    else:
                        base_exists_mji = False
                except Exception:
                    base_exists_mji = False

                # 実フォント収録の有無（cmap）
                base_exists_font = bool(base_cp is not None and has_base_cp(base_cp))

                # 最終的に「基本文字あり」とするのは双方満たす場合のみ
                base_exists = bool(base_exists_mji and base_exists_font)

                # PUA文字のコードポイントを取得（SMP文字対応）
                if len(pua_actual) == 1:
                    pua_code = ord(pua_actual)
                elif len(pua_actual) == 2:
                    high = ord(pua_actual[0]); low = ord(pua_actual[1])
                    if 0xD800 <= high <= 0xDBFF and 0xDC00 <= low <= 0xDFFF:
                        pua_code = ((high - 0xD800) << 10) + (low - 0xDC00) + 0x10000
                    else:
                        pua_code = ord(pua_actual[0])
                else:
                    pua_code = ord(pua_actual[0])

            except Exception as e:
                print(f"  警告: 文字変換エラー - {ivs_sequence} -> {e}")
                continue
            
            # MJ番号をコメントから抽出
            mj_match = re.search(r'(MJ\d+)', comment)
            mj_number = mj_match.group(1) if mj_match else 'MJ??????'
            
            # VS? の場合は強制的に基本文字なし扱い
            if vs_name == 'VS?':
                base_exists = False

            # 基本文字のUnicode表示（サロゲートや不明は '—' にする）
            if base_cp is None or (0xD800 <= (base_cp or 0) <= 0xDFFF) or vs_name == 'VS?':
                base_unicode_str = '—'
            else:
                base_unicode_str = f"U+{base_cp:X}"

            character_data.append({
                'ivs_sequence': ivs_actual,
                'pua_char': pua_actual,
                'base_char': base_text if base_exists else 'なし',
                'base_unicode': base_unicode_str,
                'vs_name': vs_name,
                'mj_number': mj_number,
                'pua_code': f"U+{pua_code:04X}",
                'comment': comment.strip(),
                'base_exists': base_exists,
            })
            
            if i < 10:  # 最初の10個をサンプル表示
                print(f"  {base_text} {vs_name} -> {pua_actual} ({mj_number})")
        
        print(f"✓ {len(character_data)} 個の文字データを処理しました")
        
        # 統計情報を計算
        total_count = len(character_data)
        unique_base_chars = len(set(item['base_char'] for item in character_data if item.get('base_exists')))
        vs_counts = {}
        for item in character_data:
            vs = item['vs_name']
            vs_counts[vs] = vs_counts.get(vs, 0) + 1
        
        print(f"✓ 統計: 総数={total_count}, 基本文字数={unique_base_chars}")
        
    except Exception as e:
        print(f"✗ エラー: {ivs_mapping_file} の解析に失敗 - {e}")
        return False
    
    # 生成時刻（最終更新）
    generated_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
        
        .base-char {{
            font-family: 'IPAMincho';
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
          src: url('../../fonts/ipam.ttf') format('truetype');
          font-weight: normal;
          font-style: normal;
        }}
        
        @font-face {{
            font-family: 'IPA-IVS-External';
            src: url('../../fonts/ipa-ivs-external.woff2') format('woff2'),
                 url('../../fonts/ipa-ivs-external.ttf') format('truetype');
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

        <div class="generation-info">
            最終更新: {generated_at}
        </div>
        
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
        base_exists_js = 'true' if item.get('base_exists') else 'false'
        
        js_item = f'{{ivsSequence: {ivs_js}, puaChar: {pua_js}, baseChar: {base_js}, baseExists: {base_exists_js}, baseUnicode: "{item["base_unicode"]}", vsName: "{item["vs_name"]}", mjNumber: "{item["mj_number"]}", puaCode: "{item["pua_code"]}"}}'
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
            const uniqueBaseChars = new Set(filteredRows.filter(i=>i.baseExists).map(item => item.baseChar)).size;
            
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
                    '<td><div class="char-display base-char" style="font-size: ' + fontSize + 'px;">' + ((item.baseExists && item.vsName !== 'VS?') ? item.baseChar : 'なし') + '</div></td>' +
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
    output_file = os.path.join(root_dir, 'examples', 'font-test', 'font-test-static.html')
    
    try:
        # 出力先ディレクトリを作成
        out_dir = os.path.dirname(output_file)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ 静的HTMLファイルを生成しました: {output_file}")
        print(f"  - 総文字数: {total_count:,}")
        print(f"  - 基本文字数: {unique_base_chars:,}")
        print(f"  - ファイルサイズ: {len(html_content)/1024/1024:.1f}MB")
        
        # 統計情報も保存
        stats = {
            "generation_timestamp": generated_at,
            "source_file": os.path.relpath(ivs_mapping_file, root_dir),
            "output_file": os.path.relpath(output_file, root_dir),
            "total_characters": total_count,
            "unique_base_characters": unique_base_chars,
            "vs_distribution": vs_counts,
            "file_size_mb": round(len(html_content)/1024/1024, 2)
        }
        
        with open(os.path.join(root_dir, "static_font_test_stats.json"), 'w', encoding='utf-8') as f:
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
