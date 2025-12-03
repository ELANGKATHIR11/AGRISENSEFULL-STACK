import json

with open('agrisense_app/backend/chatbot_qa_pairs.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"Keys in file: {list(data.keys())}")
print(f"Questions: {len(data.get('questions', []))}")
print(f"Answers: {len(data.get('answers', []))}")

# Search for carrot
questions = data.get('questions', [])
answers = data.get('answers', [])

carrot_indices = [i for i, q in enumerate(questions) if 'carrot' in q.lower()]
print(f"\nCarrot-related pairs: {len(carrot_indices)}")

# Show first few carrot questions
print("\nFirst 5 carrot questions:")
for i, idx in enumerate(carrot_indices[:5], 1):
    print(f"{i}. {questions[idx][:80]}...")
    answer_preview = answers[idx][:150] if idx < len(answers) else "N/A"
    print(f"   Answer: {answer_preview}...")

# Check for comprehensive guide
for idx in carrot_indices:
    answer = answers[idx] if idx < len(answers) else ""
    if '🥕' in answer or len(answer) > 1000:
        print(f"\n✅ Found comprehensive guide at index {idx}")
        print(f"   Question: {questions[idx]}")
        print(f"   Answer length: {len(answer)} chars")
        break
