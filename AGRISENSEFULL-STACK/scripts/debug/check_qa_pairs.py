#!/usr/bin/env python3
"""Check chatbot_qa_pairs.json structure and content."""

import json
import sys

try:
    with open('agrisense_app/backend/chatbot_qa_pairs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Questions: {len(data.get('questions', []))}")
    print(f"Answers: {len(data.get('answers', []))}")
    print(f"Sources: {len(data.get('sources', []))}")
    
    # Check for carrot guide
    carrot_idx = None
    for i, answer in enumerate(data.get('answers', [])):
        if '🥕 **Carrot Cultivation Guide:**' in answer:
            carrot_idx = i
            break
    
    if carrot_idx is not None:
        print(f"\n✅ Carrot guide found at index: {carrot_idx}")
        print(f"   Length: {len(data['answers'][carrot_idx])} chars")
        print(f"   Question: {data['questions'][carrot_idx][:100]}...")
    else:
        print("\n❌ Carrot guide NOT found in answers!")
        
        # Search for partial matches
        carrot_matches = []
        for i, answer in enumerate(data.get('answers', [])):
            if 'carrot' in answer.lower():
                carrot_matches.append(i)
        
        if carrot_matches:
            print(f"   Found {len(carrot_matches)} answers containing 'carrot':")
            for idx in carrot_matches[:5]:  # Show first 5
                print(f"   - Index {idx}: {data['answers'][idx][:80]}...")
    
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
