import json

# Load chatbot artifacts
with open('agrisense_app/backend/chatbot_qa_pairs.json', encoding='utf-8') as f:
    data = json.load(f)

# Extract questions and answers
questions = data.get('questions', [])
answers = data.get('answers', [])

print(f'Total QA pairs loaded: {len(questions)}')
print(f'Questions: {len(questions)}, Answers: {len(answers)}')

# Find carrot-related items
carrot_indices = [i for i, q in enumerate(questions) if 'carrot' in q.lower()]

print(f'Carrot-related pairs: {len(carrot_indices)}\n')
print('='*80)

# Check for comprehensive guide
comprehensive_found = False
for idx in carrot_indices:
    question = questions[idx]
    answer = answers[idx] if idx < len(answers) else "N/A"
    
    if 'cultivation guide' in question.lower() or len(answer) > 500:
        comprehensive_found = True
        print(f'\n✓ COMPREHENSIVE GUIDE FOUND!')
        print(f'Question: {question}')
        print(f'Answer length: {len(answer)} chars')
        print(f'Answer preview:\n{answer[:400]}...\n')
        print('='*80)
        break

if not comprehensive_found:
    print('\n⚠ NO COMPREHENSIVE GUIDE FOUND')
    print('All carrot questions:')
    for i, idx in enumerate(carrot_indices, 1):
        question = questions[idx]
        answer = answers[idx] if idx < len(answers) else "N/A"
        print(f'\n{i}. Q: {question}')
        print(f'   A (first 150 chars): {answer[:150]}...')
