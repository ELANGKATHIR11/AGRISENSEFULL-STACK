#!/usr/bin/env python3
"""
Fix malformed JSON in locale files.
This script validates and fixes JSON syntax errors in all locale files.
"""

import json
import os
import sys
from pathlib import Path

def fix_locale_file(file_path: Path) -> bool:
    """
    Fix malformed JSON in a locale file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        True if fixed successfully, False otherwise
    """
    print(f"Processing: {file_path}")
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            print(f"  ✅ Already valid JSON")
            return True
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON Error at line {e.lineno}, col {e.colno}: {e.msg}")
            
        # Common fixes
        # 1. Fix closing brace placement (}}"key": should be },\n"key":)
        if '}}' in content and '"' in content[content.find('}}')+2:content.find('}}')+10]:
            print("  🔧 Fixing closing brace placement...")
            content = content.replace('}}', '},\n  ')
            # Remove the extra closing brace at end
            lines = content.split('\n')
            # Find last line with just }
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip() == '}':
                    lines[i] = '  }\n}'
                    break
            content = '\n'.join(lines)
        
        # 2. Fix double keys on same line (e.g., "nav_home": "...",    "fertilizer": "...")
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # Count quotes to detect multiple keys
            if line.count('"') >= 6:  # At least 3 key-value pairs worth
                # Split by comma and reformat
                parts = []
                current = ""
                in_string = False
                for char in line:
                    if char == '"':
                        in_string = not in_string
                    current += char
                    if char == ',' and not in_string:
                        parts.append(current.strip())
                        current = ""
                
                if current.strip():
                    parts.append(current.strip())
                
                # Add each part as a separate line
                for i, part in enumerate(parts):
                    if i == 0:
                        fixed_lines.append(part)
                    else:
                        # Get indentation from first part
                        indent = len(part) - len(part.lstrip())
                        if not part.strip().endswith(','):
                            part = part.strip() + ','
                        fixed_lines.append(' ' * indent + part.strip())
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # 3. Try to parse again
        try:
            data = json.loads(content)
            
            # Write back formatted JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ Fixed and validated!")
            return True
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Still invalid after fixes: {e.msg}")
            print(f"     Line {e.lineno}, col {e.colno}")
            
            # Save the attempted fix for manual review
            backup_path = file_path.with_suffix('.json.attempted')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📝 Attempted fix saved to: {backup_path}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Main function to fix all locale files."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    locales_dir = project_root / 'agrisense_app' / 'frontend' / 'farm-fortune-frontend-main' / 'src' / 'locales'
    
    if not locales_dir.exists():
        print(f"❌ Locales directory not found: {locales_dir}")
        sys.exit(1)
    
    print(f"🔍 Scanning locale files in: {locales_dir}\n")
    
    locale_files = list(locales_dir.glob('*.json'))
    
    if not locale_files:
        print("❌ No JSON files found!")
        sys.exit(1)
    
    results = {}
    for file_path in sorted(locale_files):
        results[file_path.name] = fix_locale_file(file_path)
        print()
    
    # Summary
    print("=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for filename, success in sorted(results.items()):
        status = "✅" if success else "❌"
        print(f"  {status} {filename}")
    
    print(f"\n✅ Success: {success_count}/{total_count}")
    
    if success_count < total_count:
        print(f"❌ Failed: {total_count - success_count}/{total_count}")
        sys.exit(1)
    else:
        print("\n🎉 All locale files are now valid JSON!")
        sys.exit(0)

if __name__ == '__main__':
    main()
