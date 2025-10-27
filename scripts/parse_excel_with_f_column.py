#!/usr/bin/env python3
import zipfile
import xml.etree.ElementTree as ET
import json
from collections import defaultdict

def parse_excel_with_f_column(filename):
    """Parse Excel file including F column mapping"""
    
    # First, create a mapping from C values to F values
    c_to_f_mapping = {}
    result = defaultdict(lambda: {"B_value": None, "C_values": []})
    
    try:
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            # Read shared strings
            shared_strings = []
            try:
                shared_strings_xml = zip_ref.read('xl/sharedStrings.xml')
                ss_root = ET.fromstring(shared_strings_xml)
                
                # Extract shared strings
                for si in ss_root.iter():
                    if si.tag.endswith('si'):
                        for t in si.iter():
                            if t.tag.endswith('t') and t.text:
                                shared_strings.append(t.text)
                                break
                        else:
                            shared_strings.append("")
                            
                print(f"Found {len(shared_strings)} shared strings")
                
            except Exception as e:
                print(f"Error reading shared strings: {e}")
                return None
            
            # Read worksheet data
            sheet_xml = zip_ref.read('xl/worksheets/sheet1.xml')
            sheet_root = ET.fromstring(sheet_xml)
            
            # Parse rows
            rows_processed = 0
            
            # Find all row elements
            all_rows = []
            for elem in sheet_root.iter():
                if elem.tag.endswith('row'):
                    all_rows.append(elem)
            
            print(f"Found {len(all_rows)} rows in worksheet")
            
            for row_elem in all_rows:
                row_num = int(row_elem.get('r', 0))
                
                # Skip header row
                if row_num <= 1:
                    continue
                
                # Get cell values for this row
                row_data = {}
                
                # Find all cells in this row
                for cell_elem in row_elem.iter():
                    if cell_elem.tag.endswith('c'):
                        cell_ref = cell_elem.get('r', '')
                        cell_type = cell_elem.get('t', '')
                        
                        # Extract column letter from cell reference
                        col_letter = ''.join(c for c in cell_ref if c.isalpha())
                        
                        # Get cell value
                        for value_elem in cell_elem.iter():
                            if value_elem.tag.endswith('v') and value_elem.text:
                                cell_value = value_elem.text
                                
                                # If it's a shared string, look up the actual value
                                if cell_type == 's' and cell_value.isdigit():
                                    string_index = int(cell_value)
                                    if 0 <= string_index < len(shared_strings):
                                        cell_value = shared_strings[string_index]
                                
                                row_data[col_letter] = cell_value
                                break
                
                # Process this row if we have data for columns B, C, D, F
                if 'B' in row_data and 'C' in row_data and 'D' in row_data and 'F' in row_data:
                    b_value = row_data['B']
                    c_value = row_data['C']
                    d_value = row_data['D']
                    f_value = row_data['F']
                    
                    # Create mapping from C to F
                    if c_value:
                        c_to_f_mapping[c_value] = f_value
                    
                    # Use D as key
                    d_key = str(d_value)
                    
                    # Set B value (assuming it's consistent for same D key)
                    if result[d_key]["B_value"] is None:
                        result[d_key]["B_value"] = b_value
                    
                    # Add C value to array if it's not already there
                    if c_value and c_value not in result[d_key]["C_values"]:
                        result[d_key]["C_values"].append(c_value)
                    
                    rows_processed += 1
                    
                    # Print progress every 5000 rows
                    if rows_processed % 5000 == 0:
                        print(f"Processed {rows_processed} rows...")
                        
                    # Show first few rows for debugging
                    if rows_processed <= 5:
                        print(f"Row {row_num}: B='{b_value}', C='{c_value}', D='{d_value}', F='{f_value}'")
            
            print(f"Total rows processed: {rows_processed}")
            print(f"Unique D keys found: {len(result)}")
            print(f"C to F mappings created: {len(c_to_f_mapping)}")
            
            # Convert to regular dict
            final_result = dict(result)
            
            # Now update the result to include F column mapping for C values
            for key, value in final_result.items():
                c_with_f = {}
                for c_value in value["C_values"]:
                    f_value = c_to_f_mapping.get(c_value, None)
                    c_with_f[c_value] = f_value
                
                # Replace C_values array with C_values mapping
                value["C_values_with_F"] = c_with_f
                # Keep original array for backward compatibility
                # value["C_values"] = list(c_with_f.keys())

            # Derive base (default) MJ per code point using B_value's VS when present, else prefer E0101
            def _vs_from_bvalue(s: str):
                if not isinstance(s, str):
                    return None
                for ch in s:
                    cp = ord(ch)
                    if 0xE0100 <= cp <= 0xE01EF:
                        return f"E0{cp - 0xE0000:03X}"
                return None

            def _vs_rank(vs_tag: str):
                try:
                    if isinstance(vs_tag, str) and vs_tag.upper().startswith('E'):
                        return int(vs_tag[1:], 16)
                except Exception:
                    pass
                return 0x7FFFFFFF

            for key, value in final_result.items():
                # key example: "U+5E73"
                try:
                    hexcode = key[2:]
                except Exception:
                    hexcode = None

                b_vs = _vs_from_bvalue(value.get("B_value"))
                if b_vs is None:
                    b_vs = 'E0101'

                # Prefer the MJ whose F tag matches "<hexcode>_<b_vs>"
                base_f_tag = None
                base_mj = None
                if hexcode:
                    expected_f = f"{hexcode}_{b_vs}"
                    for mj, ftag in value.get("C_values_with_F", {}).items():
                        if ftag == expected_f:
                            base_f_tag = ftag
                            base_mj = mj
                            break

                # If not found, fall back to the smallest VS among candidates
                if base_mj is None:
                    best = (0x7FFFFFFF, None, None)
                    for mj, ftag in value.get("C_values_with_F", {}).items():
                        if isinstance(ftag, str) and '_' in ftag:
                            vs = ftag.split('_', 1)[1]
                            r = _vs_rank(vs)
                            if r < best[0]:
                                best = (r, ftag, mj)
                    if best[2] is not None:
                        base_f_tag, base_mj = best[1], best[2]

                # Store for downstream consumers
                if base_mj is not None:
                    value["base_f_tag"] = base_f_tag
                    value["base_mj"] = base_mj
            
            # Show sample
            print("\\nSample results:")
            for i, (key, value) in enumerate(final_result.items()):
                if i >= 5:
                    break
                print(f"  Key '{key}': B='{value['B_value']}', C array length={len(value['C_values'])}")
                print(f"    C values with F mapping: {value['C_values_with_F']}")
            
            return final_result, c_to_f_mapping
            
    except Exception as e:
        print(f"Error parsing Excel XML: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def save_result(result, c_to_f_mapping, output_file, mapping_file):
    """Save result to JSON files"""
    try:
        # Save main result
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Result saved to {output_file}")
        
        # Save C to F mapping
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(c_to_f_mapping, f, ensure_ascii=False, indent=2)
        print(f"C to F mapping saved to {mapping_file}")
        
    except Exception as e:
        print(f"Error saving result: {e}")

if __name__ == "__main__":
    filename = "../ipa/mji.00602.xlsx"
    result, c_to_f_mapping = parse_excel_with_f_column(filename)
    
    if result:
        # Save to JSON files
        save_result(result, c_to_f_mapping, "../mji_analysis_with_f_column.json", "../c_to_f_mapping.json")
        
        # Print summary
        print(f"\\nFinal Summary:")
        print(f"Total unique D column keys: {len(result)}")
        print(f"Total C values across all keys: {sum(len(v['C_values']) for v in result.values())}")
        print(f"Total C to F mappings: {len(c_to_f_mapping)}")
        
        # Show sample mappings
        print(f"\\nSample C to F mappings:")
        for i, (c_val, f_val) in enumerate(c_to_f_mapping.items()):
            if i >= 10:
                break
            print(f"  {c_val} -> {f_val}")
    else:
        print("Failed to parse Excel file")
