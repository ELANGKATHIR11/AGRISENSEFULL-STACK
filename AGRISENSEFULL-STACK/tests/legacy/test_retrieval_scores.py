import requests
import json

# Test query
query = "Tell me about carrot cultivation"

print(f"Testing query: '{query}'")
print("="*80)

response = requests.post(
    'http://localhost:8004/chatbot/ask',
    json={'question': query, 'top_k': 5},
    timeout=10
)

print(f"Status: {response.status_code}\n")

data = response.json()

print(f"Normalized question: {data.get('question', 'N/A')}\n")
print("Results:")
print("="*80)

for result in data.get('results', []):
    rank = result.get('rank', 'N/A')
    score = result.get('score', 'N/A')
    answer = result.get('original_answer', result.get('answer', ''))
    
    print(f"\nRank {rank} | Score: {score}")
    print("-" * 80)
    
    # Check which type of answer this is
    if '🥕' in answer or '**Carrot Cultivation Guide:**' in answer:
        print("✓ COMPREHENSIVE GUIDE FOUND!")
    elif 'Crop: Carrot' in answer:
        print("⚠ Crop Facts Fallback")
    
    # Show answer preview
    preview_len = 300
    print(f"Answer preview ({len(answer)} chars total):")
    print(answer[:preview_len])
    if len(answer) > preview_len:
        print("...")
    print("-" * 80)
