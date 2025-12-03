import requests
import json
import os

# Temporarily disable crop facts to see real retrieval scores
print("Testing WITHOUT crop facts fallback...")
print("="*80)

response = requests.post(
    'http://localhost:8004/chatbot/ask',
    json={'question': 'Tell me about carrot cultivation', 'top_k': 10},
    timeout=10
)

data = response.json()
results = data.get('results', [])

print(f"Query: {data.get('question')}")
print(f"Number of results: {len(results)}\n")

# Check each result
for result in results:
    rank = result.get('rank')
    score = result.get('score')
    answer = result.get('original_answer', result.get('answer', ''))
    
    # Identify answer type
    answer_type = "Unknown"
    if '🥕' in answer or '**Carrot Cultivation Guide:**' in answer:
        answer_type = "✓ COMPREHENSIVE GUIDE"
    elif 'Crop: Carrot' in answer:
        answer_type = "⚠ Crop Facts"
    elif len(answer) > 500:
        answer_type = "Long answer"
    
    print(f"Rank {rank} | Score: {score:.4f} | Type: {answer_type}")
    print(f"Answer preview: {answer[:150]}...")
    print("-" * 80)

print("\n\nNow testing WITH crop facts fallback (current setting)...")
print("="*80)

response2 = requests.post(
    'http://localhost:8004/chatbot/ask',
    json={'question': 'Tell me about carrot cultivation', 'top_k': 5},
    timeout=10
)

data2 = response2.json()
results2 = data2.get('results', [])

print(f"Number of results: {len(results2)}")
for result in results2:
    answer = result.get('original_answer', result.get('answer', ''))
    if '🥕' in answer:
        print("✓ Got comprehensive guide!")
    elif 'Crop: Carrot' in answer:
        print("⚠ Got crop facts fallback")
        print(f"Score: {result.get('score')}")
