#!/usr/bin/env python3
"""
Test script for plant health management API endpoints
"""

import requests
import json
import base64
from io import BytesIO
from PIL import Image
import time

# Test configuration
BASE_URL = "http://127.0.0.1:8004"

def create_test_image():
    """Create a test image for API testing"""
    # Create a simple test image
    img = Image.new('RGB', (224, 224), color=(100, 150, 200))
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

def test_health_status():
    """Test the health system status endpoint"""
    print("🔍 Testing health system status...")
    try:
        response = requests.get(f"{BASE_URL}/health/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Status Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Request failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_disease_detection():
    """Test disease detection endpoint"""
    print("\n🦠 Testing disease detection...")
    try:
        image_data = create_test_image()
        
        payload = {
            "image_data": image_data,
            "field_info": {
                "crop_type": "tomato",
                "growth_stage": "flowering"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/disease/detect",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Disease Detection Response:")
            print(f"Primary Disease: {data.get('primary_disease', 'N/A')}")
            print(f"Confidence: {data.get('confidence', 'N/A')}")
            print(f"Severity: {data.get('severity', 'N/A')}")
        else:
            print(f"❌ Request failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_weed_analysis():
    """Test weed analysis endpoint"""
    print("\n🌾 Testing weed analysis...")
    try:
        image_data = create_test_image()
        
        payload = {
            "image_data": image_data,
            "field_info": {
                "crop_type": "corn",
                "field_size_acres": 5.2
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/weed/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Weed Analysis Response:")
            print(f"Coverage: {data.get('weed_coverage_percentage', 'N/A')}%")
            print(f"Pressure: {data.get('weed_pressure', 'N/A')}")
            print(f"Regions: {len(data.get('weed_regions', []))}")
        else:
            print(f"❌ Request failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_comprehensive_assessment():
    """Test comprehensive health assessment endpoint"""
    print("\n🌿 Testing comprehensive health assessment...")
    try:
        image_data = create_test_image()
        
        payload = {
            "image_data": image_data,
            "field_info": {
                "crop_type": "tomato",
                "growth_stage": "vegetative",
                "field_size_acres": 2.5,
                "weather": {
                    "temperature": 25,
                    "humidity": 70
                }
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/health/assess",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Comprehensive Assessment Response:")
            print(f"Assessment ID: {data.get('assessment_id', 'N/A')}")
            print(f"Health Score: {data.get('overall_health_score', 'N/A')}/100")
            print(f"Alert Level: {data.get('alert_level', 'N/A')}")
            
            integrated = data.get('integrated_assessment', {})
            print(f"Primary Concern: {integrated.get('primary_health_concern', 'N/A')}")
            print(f"Field Condition: {integrated.get('field_condition', 'N/A')}")
        else:
            print(f"❌ Request failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🧪 AgriSense Plant Health API Testing")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test all endpoints
    test_health_status()
    test_disease_detection()
    test_weed_analysis()
    test_comprehensive_assessment()
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    main()