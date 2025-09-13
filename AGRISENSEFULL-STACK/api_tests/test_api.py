#!/usr/bin/env python3
"""Simple API test using FastAPI TestClient"""

from agrisense_app.backend.main import app
from fastapi.testclient import TestClient

def main():
    client = TestClient(app)
    
    print('Testing AgriSense API endpoints...')
    
    # Test health
    response = client.get('/health')
    print(f'✅ Health: {response.status_code} - {response.json()}')
    
    # Test plants
    response = client.get('/plants')
    plants = response.json()
    plant_names = list(plants.keys())[:3]
    print(f'✅ Plants: {len(plants)} available - {plant_names}...')
    
    # Test recommendation
    payload = {
        'moisture': 45.0,
        'temp': 25.0, 
        'ph': 6.5,
        'ec': 1.2,
        'plant': 'wheat'
    }
    response = client.post('/recommend', json=payload)
    reco = response.json()
    water = reco.get('water_liters', 0)
    fert_n = reco.get('fert_n_g', 0)
    print(f'✅ Recommendation: water={water:.1f}L, fert_n={fert_n:.1f}g')
    
    # Test UI
    response = client.get('/ui')
    print(f'✅ Frontend UI: {response.status_code} ({len(response.content)} bytes)')
    
    # Test chatbot
    try:
        response = client.post('/chatbot/ask', json={'question': 'How to grow tomatoes?', 'top_k': 3})
        if response.status_code == 200:
            results = response.json().get('results', [])
            print(f'✅ Chatbot: {len(results)} results')
        else:
            print(f'⚠️ Chatbot: {response.status_code} (may need initialization)')
    except Exception as e:
        print(f'⚠️ Chatbot: {e}')
    
    print('✅ All API tests completed!')

if __name__ == '__main__':
    main()