#!/usr/bin/env python3
"""
Rebuild broken locale JSON files by extracting valid translations
and reconstructing them with proper structure.
"""
import json
import re
from pathlib import Path

def extract_translations_from_broken_json(file_path):
    """Extract all key-value pairs from a broken JSON file."""
    translations = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match JSON key-value pairs
    # Matches: "key": "value" (handles Unicode properly)
    pattern = r'"([^"]+)":\s*"([^"]*(?:\\.[^"]*)*)"'
    
    matches = re.findall(pattern, content)
    
    for key, value in matches:
        # Skip structural keys
        if key in ['translation', 'chatbot']:
            continue
        translations[key] = value
    
    return translations

def rebuild_locale_file(broken_file, english_file, output_file):
    """Rebuild a locale file using English structure as template."""
    # Load English structure
    with open(english_file, 'r', encoding='utf-8') as f:
        english_data = json.load(f)
    
    # Extract translations from broken file
    translations = extract_translations_from_broken_json(broken_file)
    
    # Separate chatbot translations
    chatbot_translations = {}
    main_translations = {}
    
    for key, value in translations.items():
        if any(chatbot_key in key for chatbot_key in [
            'title', 'welcome', 'you', 'assistant', 'placeholder', 
            'input_placeholder', 'send', 'thinking', 'loading', 
            'no_answer', 'suggested_questions', 'show_original', 
            'hide_original', 'original_answer', 'footer'
        ]):
            chatbot_translations[key] = value
        else:
            main_translations[key] = value
    
    # Build new structure
    new_structure = {
        "translation": {}
    }
    
    # Add all main-level keys from English structure
    for key in english_data['translation'].keys():
        if key == 'chatbot':
            # Handle chatbot section
            new_structure['translation']['chatbot'] = {}
            for chatbot_key in english_data['translation']['chatbot'].keys():
                if chatbot_key in chatbot_translations:
                    new_structure['translation']['chatbot'][chatbot_key] = chatbot_translations[chatbot_key]
                else:
                    # Fallback to English if translation missing
                    new_structure['translation']['chatbot'][chatbot_key] = english_data['translation']['chatbot'][chatbot_key]
        else:
            # Handle main-level keys
            if key in main_translations:
                new_structure['translation'][key] = main_translations[key]
            else:
                # Fallback to English if translation missing
                new_structure['translation'][key] = english_data['translation'][key]
    
    # Write reconstructed file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_structure, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Rebuilt {output_file.name}")
    return True

def main():
    base_path = Path(__file__).parent.parent / 'agrisense_app' / 'frontend' / 'farm-fortune-frontend-main' / 'src' / 'locales'
    
    english_file = base_path / 'en.json'
    
    # Files to rebuild
    files_to_fix = [
        ('hi.json', 'Hindi'),
        ('te.json', 'Telugu'),
        ('kn.json', 'Kannada')
    ]
    
    print("🔧 Rebuilding broken locale files...\n")
    
    for filename, language in files_to_fix:
        broken_file = base_path / filename
        output_file = base_path / filename
        
        try:
            rebuild_locale_file(broken_file, english_file, output_file)
            
            # Validate the output
            with open(output_file, 'r', encoding='utf-8') as f:
                json.load(f)  # Will raise exception if invalid
            
            print(f"   ✓ {language} validated successfully\n")
            
        except Exception as e:
            print(f"   ✗ {language} failed: {e}\n")
    
    print("\n🎉 Locale rebuild complete!")
    print("\nValidating all locale files...")
    
    # Final validation
    all_valid = True
    for locale in ['en', 'hi', 'ta', 'te', 'kn']:
        locale_file = base_path / f'{locale}.json'
        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                key_count = len(data['translation'])
                print(f"✅ {locale}.json - {key_count} keys")
        except Exception as e:
            print(f"❌ {locale}.json - {e}")
            all_valid = False
    
    if all_valid:
        print("\n✅ All locale files are valid!")
    else:
        print("\n⚠️ Some locale files still have issues")

if __name__ == '__main__':
    main()
