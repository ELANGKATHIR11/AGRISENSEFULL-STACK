import requests
import json
import os

# Ensure environment variables are set
os.environ['CHATBOT_ENABLE_CROP_FACTS'] = '1'

url = "http://localhost:8004/chatbot/ask"

queries = [
    "Tell me about carrot cultivation",
    "carrot cultivation guide", 
    "how to grow carrots"
]

for q in queries:
    print(f"\n{'='*80}")
    print(f"Query: '{q}'")
    print(f"{'='*80}")
    
    response = requests.post(url, json={"question": q})
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get('answer', '')
        
        # Check if it's comprehensive guide
        is_comprehensive = '🥕 **Carrot Cultivation Guide:**' in answer
        is_fallback = 'Best Farming Practice' in answer or len(answer) < 300
        
        print(f"Status: {response.status_code}")
        print(f"Answer length: {len(answer)} chars")
        print(f"Is comprehensive guide: {is_comprehensive}")
        print(f"Is fallback: {is_fallback}")
        print(f"\nFirst 200 chars of answer:")
        print(f"{answer[:200]}...")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
