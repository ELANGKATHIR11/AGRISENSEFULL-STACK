import json

with open('agrisense_app/backend/chatbot_qa_pairs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Questions: {len(data["questions"])}')
print(f'Answers: {len(data["answers"])}')
print(f'Sources: {len(data["sources"])}')

print('\nLast 20 questions:')
for i, q in enumerate(data['questions'][-20:], len(data['questions'])-20):
    print(f'{i}: {q[:100]}...' if len(q) > 100 else f'{i}: {q}')

print('\n\nLast 10 answers (first 100 chars):')
for i, a in enumerate(data['answers'][-10:], len(data['answers'])-10):
    print(f'{i}: {a[:100]}...' if len(a) > 100 else f'{i}: {a}')

# Check for cultivation guide pattern
cultivation_guides = []
for i, (q, a) in enumerate(zip(data['questions'], data['answers'])):
    if 'Cultivation Guide' in str(a):
        cultivation_guides.append((i, q, a[:200]))

print(f'\n\nFound {len(cultivation_guides)} cultivation guides')
if cultivation_guides:
    print('\nFirst 5 cultivation guides:')
    for i, q, a_snippet in cultivation_guides[:5]:
        print(f'\nIndex {i}:')
        print(f'  Question: {q}')
        print(f'  Answer snippet: {a_snippet}...')
