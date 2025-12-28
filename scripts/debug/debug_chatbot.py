import json

with open('agrisense_app/backend/chatbot_qa_pairs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Total Q&A pairs: {len(data["questions"])}')

# Find soybean mentions
soy_q = [i for i, q in enumerate(data['questions']) if 'soybean' in q.lower()]
print(f'\nSoybean questions found: {len(soy_q)}')
if soy_q:
    idx = soy_q[0]
    print(f'\nExample soybean question at index {idx}:')
    print(f'Q: {data["questions"][idx]}')
    print(f'A: {data["answers"][idx][:300]}...')

# Find carrot mentions
carrot_q = [i for i, q in enumerate(data['questions']) if 'carrot' in q.lower()]
print(f'\nCarrot questions found: {len(carrot_q)}')
if carrot_q:
    for idx in carrot_q[:3]:
        print(f'\nCarrot question at index {idx}:')
        print(f'Q: {data["questions"][idx]}')
        print(f'A: {data["answers"][idx][:150]}')

# Check what's being returned as score 0.0 (likely first/default answer)
print(f'\nFirst answer in dataset (index 0):')
print(f'Q: {data["questions"][0]}')
print(f'A: {data["answers"][0][:300]}...')
