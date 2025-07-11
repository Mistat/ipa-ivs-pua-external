#!/usr/bin/env python3
import json

def reverse_c_f_mapping(input_file, output_file):
    """Reverse the C_values_with_F mapping so F values become keys and C values become values"""
    
    try:
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} entries from {input_file}")
        
        # Reverse the mapping in each entry
        for key, value in data.items():
            if "C_values_with_F" in value:
                # Reverse the key-value pairs
                original_mapping = value["C_values_with_F"]
                reversed_mapping = {}
                
                for c_value, f_value in original_mapping.items():
                    reversed_mapping[f_value] = c_value
                
                # Update the mapping
                value["C_values_with_F"] = reversed_mapping
        
        # Save the modified data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Reversed mapping saved to {output_file}")
        
        # Show sample results
        print("\\nSample results with reversed mapping:")
        for i, (key, value) in enumerate(data.items()):
            if i >= 5:
                break
            print(f"  Key '{key}': B='{value['B_value']}', C array length={len(value['C_values'])}")
            if "C_values_with_F" in value:
                print(f"    F to C mapping: {value['C_values_with_F']}")
        
        return data
        
    except Exception as e:
        print(f"Error reversing mapping: {e}")
        return None

if __name__ == "__main__":
    input_file = "../mji_analysis_with_f_column.json"
    output_file = "../mji_analysis_f_to_c_mapping.json"
    
    result = reverse_c_f_mapping(input_file, output_file)
    
    if result:
        print(f"\\nSuccessfully created {output_file} with reversed F to C mapping")
        print(f"Total entries: {len(result)}")
    else:
        print("Failed to reverse mapping")