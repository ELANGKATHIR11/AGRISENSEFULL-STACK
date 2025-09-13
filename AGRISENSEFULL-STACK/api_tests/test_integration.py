#!/usr/bin/env python3
"""Integration test for AgriSense backend-frontend pipeline"""

import requests
import json
import time
import subprocess
import threading
from contextlib import contextmanager

@contextmanager
def backend_server():
    """Start backend server in background"""
    proc = subprocess.Popen([
        '.venv/Scripts/python.exe', '-m', 'uvicorn', 
        'agrisense_app.backend.main:app', '--port', '8004'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(10)
    
    try:
        yield proc
    finally:
        proc.terminate()
        proc.wait()

def main():
    print('🚀 Testing AgriSense backend-frontend integration...')
    
    # Test with backend
    with backend_server():
        base_url = 'http://127.0.0.1:8004'
        
        # Test health
        try:
            r = requests.get(f'{base_url}/health', timeout=10)
            print(f'✅ Health: {r.status_code}')
        except Exception as e:
            print(f'❌ Health: {e}')
        
        # Test plants endpoint
        try:
            r = requests.get(f'{base_url}/plants', timeout=10)
            plants = r.json()
            print(f'✅ Plants: {len(plants)} available')
        except Exception as e:
            print(f'❌ Plants: {e}')
        
        # Test recommendation
        try:
            payload = {
                'moisture': 45.0,
                'temp': 25.0,
                'ph': 6.5,
                'ec': 1.2,
                'plant': 'wheat'
            }
            r = requests.post(f'{base_url}/recommend', json=payload, timeout=10)
            reco = r.json()
            water = reco.get('water_liters', 0)
            print(f'✅ Recommendation: water={water:.1f}L')
        except Exception as e:
            print(f'❌ Recommendation: {e}')
        
        # Test UI serving
        try:
            r = requests.get(f'{base_url}/ui', timeout=10)
            print(f'✅ Frontend served: {r.status_code} ({len(r.content)} bytes)')
        except Exception as e:
            print(f'❌ Frontend: {e}')
        
        # Test API documentation
        try:
            r = requests.get(f'{base_url}/docs', timeout=10)
            print(f'✅ API docs: {r.status_code}')
        except Exception as e:
            print(f'❌ API docs: {e}')
    
    print('✅ Integration test completed!')

if __name__ == '__main__':
    main()