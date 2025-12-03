import requests
import json

print("="*80)
print("DETAILED RETRIEVAL ANALYSIS")
print("="*80)

# Test with explicit cultivation query
print("\nQuery: 'Tell me about carrot cultivation'")
response = requests.post(
    'http://localhost:8004/chatbot/ask',
    json={'question': 'Tell me about carrot cultivation', 'top_k': 5},
    timeout=15
)

if response.status_code == 200:
    data = response.json()
    print(f"\nNormalized question: {data.get('question')}")
    results = data.get('results', [])
    print(f"Number of results: {len(results)}\n")
    
    for i, result in enumerate(results, 1):
        answer = result.get('answer', '')
        original = result.get('original_answer', answer)
        score = result.get('score', 0)
        is_fallback = result.get('is_fallback', False)
        
        # Determine answer type
        answer_type = "Unknown"
        if is_fallback:
            answer_type = "FALLBACK RESPONSE"
        elif '🥕' in original or '**Carrot Cultivation Guide:**' in original:
            answer_type = "✅ COMPREHENSIVE GUIDE"
        elif 'Crop: Carrot' in original and 'Category: Vegetable' in original:
            answer_type = "⚠️  CROP FACTS"
        elif 'soybean' in original.lower():
            answer_type = "❌ WRONG CROP (Soybean)"
        elif len(original) > 500:
            answer_type = "Long answer"
        
        print(f"Result #{i}")
        print(f"  Type: {answer_type}")
        print(f"  Score: {score}")
        print(f"  Is Fallback: {is_fallback}")
        print(f"  Answer length: {len(original)} chars")
        print(f"  Preview: {original[:200]}...")
        print("-" * 80)

    # Summary
    print("\n" + "="*80)
    print("ANALYSIS:")
    if any('🥕' in r.get('answer', '') for r in results):
        print("✅ Comprehensive guide IS in results!")
    elif any('Crop: Carrot' in r.get('answer', '') for r in results):
        print("⚠️  Only crop facts found (no comprehensive guide)")
    else:
        print("❌ Neither comprehensive guide nor crop facts found")
    print("="*80)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
