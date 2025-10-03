#!/usr/bin/env python
"""Test disease detection endpoint and debug UI issues"""
import requests
import json
import base64

# Create a simple test image (1x1 transparent PNG)
test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Test disease detection endpoint
def test_disease_detection():
    url = "http://127.0.0.1:8004/disease/detect"
    
    # Test 1: Basic POST with minimal data
    payload = {
        "image_data": test_image_b64,
        "crop_type": "tomato"
    }
    
    print("🧪 Testing Disease Detection Endpoint...")
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Disease: {result.get('disease', 'Unknown')}")
            print(f"Confidence: {result.get('confidence', 0)}")
            print(f"Severity: {result.get('severity', 'Unknown')}")
        else:
            print("❌ Failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

# Test CORS headers
def test_cors():
    print("\n🌐 Testing CORS Configuration...")
    try:
        # Preflight request
        response = requests.options("http://127.0.0.1:8004/disease/detect", 
                                  headers={
                                      "Origin": "http://localhost:8080",
                                      "Access-Control-Request-Method": "POST",
                                      "Access-Control-Request-Headers": "Content-Type"
                                  })
        print(f"Preflight Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        
    except Exception as e:
        print(f"❌ CORS Test Exception: {e}")

# Test if UI assets are accessible
def test_ui_assets():
    print("\n🎨 Testing UI Assets...")
    assets = [
        "/ui/assets/index-DYgKWUjf.js",
        "/ui/assets/index-Cqa0Y9Wm.css",
        "/ui/logo-agrisense-mark-v2.svg"
    ]
    
    for asset in assets:
        try:
            response = requests.get(f"http://127.0.0.1:8004{asset}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {asset} - {response.status_code}")
        except Exception as e:
            print(f"❌ {asset} - Error: {e}")

if __name__ == "__main__":
    test_disease_detection()
    test_cors() 
    test_ui_assets()