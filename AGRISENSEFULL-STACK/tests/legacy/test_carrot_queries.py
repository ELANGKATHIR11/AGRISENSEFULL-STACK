import json
import requests

# Test different carrot queries
queries = [
    "carrot",
    "Tell me about carrot cultivation", 
    "carrot cultivation",
    "how to grow carrot",
    "carrot growing guide"
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Query: '{q}'")
    print('='*60)
    
    r = requests.post('http://localhost:8004/chatbot/ask', json={'question': q, 'top_k': 3})
    result = r.json()
    
    print(f"Expanded to: {result['question']}")
    print(f"\nTop result (score={result['results'][0]['score']}):")
    
    answer = result['results'][0]['answer']
    # Check if it's the comprehensive guide
    if '**Carrot Cultivation Guide:**' in answer or '🥕' in answer:
        print("✓ COMPREHENSIVE GUIDE FOUND!")
        print(answer[:300])
    elif 'Crop: Carrot' in answer:
        print("⚠ Using crop facts fallback")
        print(answer[:200])
    else:
        print("✗ Wrong answer")
        print(answer[:200])
