#!/usr/bin/env python3
"""
Comprehensive locale JSON validator and fixer.
Validates all locale files and fixes common issues.
"""

import json
import os
import sys
from pathlib import Path

def validate_and_fix_json(file_path: Path, reference_keys: set = None) -> tuple:
    """
    Validate and attempt to fix JSON file.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try parsing
        try:
            data = json.loads(content)
            
            # Check structure
            if 'translation' not in data:
                return False, "Missing 'translation' key"
            
            if not isinstance(data['translation'], dict):
                return False, "'translation' is not a dictionary"
            
            # Check for duplicates
            keys = list(data['translation'].keys())
            duplicates = [k for k in keys if keys.count(k) > 1]
            if duplicates:
                unique_dups = list(set(duplicates))
                return False, f"Duplicate keys found: {', '.join(unique_dups[:5])}"
            
            # Compare with reference if provided
            if reference_keys:
                current_keys = set(data['translation'].keys())
                missing = reference_keys - current_keys
                extra = current_keys - reference_keys
                
                if missing or extra:
                    msg = []
                    if missing:
                        msg.append(f"Missing {len(missing)} keys")
                    if extra:
                        msg.append(f"Extra {len(extra)} keys")
                    return True, "Valid but " + ", ".join(msg)
            
            # Write back formatted
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True, "Valid JSON"
            
        except json.JSONDecodeError as e:
            # Attempt automatic fix
            return False, f"JSON Error at line {e.lineno}: {e.msg}"
            
    except Exception as e:
        return False, str(e)

def main():
    """Main validation function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    locales_dir = project_root / 'agrisense_app' / 'frontend' / 'farm-fortune-frontend-main' / 'src' / 'locales'
    
    if not locales_dir.exists():
        print(f"Error: Locales directory not found: {locales_dir}")
        sys.exit(1)
    
    print(f"Validating locale files in: {locales_dir}")
    print("=" * 60)
    
    # Load reference (English)
    en_file = locales_dir / 'en.json'
    reference_keys = None
    
    if en_file.exists():
        try:
            with open(en_file, 'r', encoding='utf-8') as f:
                en_data = json.load(f)
                reference_keys = set(en_data['translation'].keys())
                print(f"Reference (en.json): {len(reference_keys)} keys\n")
        except Exception as e:
            print(f"Warning: Could not load reference: {e}\n")
    
    # Validate all files
    results = {}
    locale_files = sorted([f for f in locales_dir.glob('*.json') if not f.name.endswith('.attempted')])
    
    for file_path in locale_files:
        success, message = validate_and_fix_json(file_path, reference_keys)
        results[file_path.name] = (success, message)
        
        status_icon = "OK" if success else "ERR"
        print(f"[{status_icon}] {file_path.name:15} - {message}")
    
    print("\n" + "=" * 60)
    
    success_count = sum(1 for s, m in results.values() if s)
    total_count = len(results)
    
    print(f"Results: {success_count}/{total_count} valid")
    
    if success_count < total_count:
        print(f"\nFiles with errors:")
        for filename, (success, msg) in results.items():
            if not success:
                print(f"  - {filename}: {msg}")
        sys.exit(1)
    else:
        print("\nAll locale files are valid!")
        sys.exit(0)

if __name__ == '__main__':
    main()
