#!/usr/bin/env python3
"""
Clean backend integration test without Unicode characters
Tests all backend functionality including VLM integration
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from PIL import Image
import io
import numpy as np

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "agrisense_app" / "backend"
sys.path.insert(0, str(backend_dir))

def create_test_image():
    """Create a simple test image for analysis"""
    # Create a simple green field image with some brown spots
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    
    # Green background (healthy crop)
    img[:, :, 1] = 120  # Green channel
    img[:, :, 0] = 50   # Red channel
    img[:, :, 2] = 30   # Blue channel
    
    # Add some brown spots (potential disease/weed areas)
    for i in range(5):
        x, y = np.random.randint(20, 200, 2)
        size = np.random.randint(10, 30)
        img[y:y+size, x:x+size, 0] = 139  # Brown color
        img[y:y+size, x:x+size, 1] = 69
        img[y:y+size, x:x+size, 2] = 19
    
    # Convert to PIL Image
    pil_img = Image.fromarray(img)
    
    # Convert to base64
    buffer = io.BytesIO()
    pil_img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_base64

def test_basic_endpoints():
    """Test basic API endpoints"""
    base_url = "http://localhost:8004"
    
    print("Testing basic endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("  [SUCCESS] Health endpoint working")
        else:
            print(f"  [ERROR] Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] Health endpoint error: {e}")
    
    # Test ready endpoint
    try:
        response = requests.get(f"{base_url}/ready", timeout=5)
        if response.status_code == 200:
            print("  [SUCCESS] Ready endpoint working")
        else:
            print(f"  [ERROR] Ready endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] Ready endpoint error: {e}")
    
    # Test UI endpoint
    try:
        response = requests.get(f"{base_url}/ui", timeout=5)
        if response.status_code == 200:
            print("  [SUCCESS] UI endpoint working")
        else:
            print(f"  [ERROR] UI endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] UI endpoint error: {e}")

def test_weed_analysis():
    """Test weed analysis endpoint"""
    base_url = "http://localhost:8004"
    
    print("Testing weed analysis...")
    
    test_image = create_test_image()
    payload = {
        "image_data": test_image,
        "crop_type": "corn",
        "field_info": {
            "crop_type": "corn",
            "field_size_acres": 2.5
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/weed/analyze",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print("  [SUCCESS] Weed analysis working")
            print(f"     Coverage: {result.get('weed_coverage_percentage', 0):.1f}%")
            print(f"     Pressure: {result.get('weed_pressure', 'unknown')}")
            if 'vlm_analysis' in result:
                print(f"     VLM Enhanced: {result['vlm_analysis'].get('knowledge_matches', 0)} matches")
        else:
            print(f"  [ERROR] Weed analysis failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] Weed analysis error: {e}")

def test_disease_detection():
    """Test disease detection endpoint"""
    base_url = "http://localhost:8004"
    
    print("Testing disease detection...")
    
    test_image = create_test_image()
    payload = {
        "image_data": test_image,
        "crop_type": "tomato",
        "field_info": {
            "crop_type": "tomato",
            "field_size_acres": 1.5
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/disease/detect",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print("  [SUCCESS] Disease detection working")
            print(f"     Disease: {result.get('primary_disease', 'unknown')}")
            print(f"     Confidence: {result.get('confidence', 0):.2f}")
            if 'vlm_analysis' in result:
                print(f"     VLM Enhanced: {result['vlm_analysis'].get('knowledge_matches', 0)} matches")
        else:
            print(f"  [ERROR] Disease detection failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] Disease detection error: {e}")

def test_vlm_endpoints():
    """Test VLM specific endpoints"""
    base_url = "http://localhost:8004"
    
    print("Testing VLM endpoints...")
    
    # Test VLM status
    try:
        response = requests.get(f"{base_url}/api/vlm/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"  [SUCCESS] VLM Status: {status_data.get('status', 'unknown')}")
            print(f"     Available: {status_data.get('vlm_available', False)}")
            print(f"     Capabilities: {len(status_data.get('capabilities', []))}")
        else:
            print(f"  [ERROR] VLM status failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] VLM status error: {e}")
    
    # Test comprehensive VLM analysis
    test_image = create_test_image()
    payload = {
        "image_data": test_image,
        "crop_type": "tomato",
        "field_info": {
            "crop_type": "tomato",
            "field_size_acres": 2.0
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/vlm/analyze",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print("  [SUCCESS] Comprehensive VLM analysis working")
            print(f"     Overall Health Score: {result.get('overall_health_score', 0)}/100")
            print(f"     Priority Actions: {len(result.get('priority_actions', []))}")
        else:
            print(f"  [ERROR] VLM comprehensive analysis failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] VLM comprehensive analysis error: {e}")

def test_recommendation_system():
    """Test recommendation system"""
    base_url = "http://localhost:8004"
    
    print("Testing recommendation system...")
    
    # Test sensor reading and recommendation
    payload = {
        "zone_id": "Z1",
        "plant": "tomato",
        "soil_type": "loam",
        "area_m2": 100.0,
        "ph": 6.5,
        "moisture_pct": 45.0,
        "temperature_c": 25.0,
        "ec_dS_m": 1.2,
        "n_ppm": 150,
        "p_ppm": 50,
        "k_ppm": 200
    }
    
    try:
        response = requests.post(
            f"{base_url}/recommend",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print("  [SUCCESS] Recommendation system working")
            print(f"     Water needed: {result.get('water_liters', 0):.1f}L")
            print(f"     Fertilizer: {result.get('fertilizer_kg', 0):.2f}kg")
            print(f"     Water source: {result.get('water_source', 'unknown')}")
        else:
            print(f"  [ERROR] Recommendation failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] Recommendation error: {e}")

def test_chatbot():
    """Test chatbot functionality"""
    base_url = "http://localhost:8004"
    
    print("Testing chatbot...")
    
    payload = {
        "message": "What crops are good for tomatoes?",
        "zone_id": "Z1"
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            print("  [SUCCESS] Chatbot working")
            print(f"     Answer length: {len(result.get('answer', ''))}")
            print(f"     Sources: {len(result.get('sources', []))}")
        else:
            print(f"  [ERROR] Chatbot failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] Chatbot error: {e}")

def main():
    """Run all backend integration tests"""
    print("AgriSense Backend Integration Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    test_basic_endpoints()
    print()
    
    # Test core features
    test_recommendation_system()
    print()
    
    test_chatbot()
    print()
    
    # Test plant health features
    test_weed_analysis()
    print()
    
    test_disease_detection()
    print()
    
    # Test VLM integration
    test_vlm_endpoints()
    print()
    
    print("=" * 50)
    print("Backend integration testing completed!")
    print("Check the results above for any issues.")

if __name__ == "__main__":
    main()
