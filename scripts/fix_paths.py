#!/usr/bin/env python3
"""
スクリプト移動後のパス修正
"""
import os
import re

def fix_file_paths(file_path):
    """ファイル内のパスを修正"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # JSON ファイルのパスを修正
    content = re.sub(r'"mji_analysis_f_to_c_mapping\.json"', '"../mji_analysis_f_to_c_mapping.json"', content)
    content = re.sub(r'"mji_analysis_with_f_column\.json"', '"../mji_analysis_with_f_column.json"', content)
    content = re.sub(r'"c_to_f_mapping\.json"', '"../c_to_f_mapping.json"', content)
    content = re.sub(r'"mj_based_extraction_stats\.json"', '"../mj_based_extraction_stats.json"', content)
    content = re.sub(r'"static_font_test_stats\.json"', '"../static_font_test_stats.json"', content)
    content = re.sub(r'"staged_allocation_stats\.json"', '"../staged_allocation_stats.json"', content)
    
    # src/utils パスを修正
    content = re.sub(r'"src/utils', '"../src/utils', content)
    content = re.sub(r"'src/utils", "'../src/utils", content)
    
    # public パスを修正
    content = re.sub(r'"public/', '"../public/', content)
    content = re.sub(r"'public/", "'../public/", content)
    
    # Excel ファイルのパスを修正
    content = re.sub(r'"mji\.00602\.xlsx"', '"../ipa/mji.00602.xlsx"', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed paths in: {file_path}")

def main():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    python_files = [
        'parse_excel_with_f_column.py',
        'reverse_c_f_mapping.py', 
        'fix_mj_based_extraction.py',
        'generate_js_mapping_only.py',
        'extract_ivs_glyphs_mj_based.py',
        'generate_static_font_test.py'
    ]
    
    for py_file in python_files:
        file_path = os.path.join(scripts_dir, py_file)
        if os.path.exists(file_path):
            fix_file_paths(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()