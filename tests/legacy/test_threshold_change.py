import requests
import json

print("="*80)
print("TESTING CARROT QUERY WITH LOWERED THRESHOLD (0.25)")
print("="*80)

# Test 1: Simple carrot query
print("\n1. Testing query: 'carrot'")
response = requests.post(
    'http://localhost:8004/chatbot/ask',
    json={'question': 'carrot', 'top_k': 3},
    timeout=15
)

if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    
    print(f"   Status: {response.status_code}")
    print(f"   Number of results: {len(results)}")
    
    if results:
        answer = results[0].get('answer', '')
        original = results[0].get('original_answer', answer)
        score = results[0].get('score', 0)
        
        # Check answer type
        if '🥕' in answer or '**Carrot Cultivation Guide:**' in answer:
            print(f"   ✅ SUCCESS! Got COMPREHENSIVE GUIDE")
            print(f"   Score: {score}")
            print(f"   Answer length: {len(original)} chars")
            print(f"   Preview: {original[:200]}...")
        elif 'Crop: Carrot' in answer or 'Category: Vegetable' in answer:
            print(f"   ⚠️  Got CROP FACTS fallback (not comprehensive guide)")
            print(f"   Score: {score}")
            print(f"   Answer: {original[:150]}...")
        else:
            print(f"   ❓ Got unexpected answer")
            print(f"   Score: {score}")
            print(f"   Answer: {original[:150]}...")
else:
    print(f"   ❌ Error: {response.status_code}")

# Test 2: Explicit cultivation query
print("\n2. Testing query: 'Tell me about carrot cultivation'")
response2 = requests.post(
    'http://localhost:8004/chatbot/ask',
    json={'question': 'Tell me about carrot cultivation', 'top_k': 3},
    timeout=15
)

if response2.status_code == 200:
    data2 = response2.json()
    results2 = data2.get('results', [])
    
    print(f"   Status: {response2.status_code}")
    print(f"   Number of results: {len(results2)}")
    
    if results2:
        answer2 = results2[0].get('answer', '')
        original2 = results2[0].get('original_answer', answer2)
        score2 = results2[0].get('score', 0)
        
        if '🥕' in answer2 or '**Carrot Cultivation Guide:**' in answer2:
            print(f"   ✅ SUCCESS! Got COMPREHENSIVE GUIDE")
            print(f"   Score: {score2}")
            print(f"   Answer length: {len(original2)} chars")
        elif 'Crop: Carrot' in answer2:
            print(f"   ⚠️  Got CROP FACTS fallback")
            print(f"   Score: {score2}")
        else:
            print(f"   ❓ Got unexpected answer")
            print(f"   Score: {score2}")
else:
    print(f"   ❌ Error: {response2.status_code}")

print("\n" + "="*80)
print("CONCLUSION:")
if '🥕' in (results[0].get('answer', '') if results else ''):
    print("✅ Threshold change SUCCESSFUL - comprehensive guide is now retrieved!")
elif 'Crop: Carrot' in (results[0].get('answer', '') if results else ''):
    print("⚠️  Still using crop facts fallback - may need lower threshold or better embeddings")
else:
    print("❓ Unexpected result - needs investigation")
print("="*80)
