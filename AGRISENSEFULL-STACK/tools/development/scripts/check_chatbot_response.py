import requests
import json

url = 'http://127.0.0.1:8004/chatbot/ask'
payload = {'question': 'What is the best watering schedule for tomatoes?', 'top_k': 3}

try:
    r = requests.post(url, json=payload, timeout=10)
    print('status_code:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print('raw body:', r.text)
except Exception as e:
    print('Request failed:', type(e).__name__, e)
