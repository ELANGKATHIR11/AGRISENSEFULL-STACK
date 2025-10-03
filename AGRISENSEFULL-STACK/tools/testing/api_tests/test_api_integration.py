#!/usr/bin/env python3
"""
Test the plant health endpoints via the FastAPI backend
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8004"

def test_disease_detection_api():
    """Test the disease detection API endpoint"""
    print("🦠 Testing Disease Detection API")
    print("-" * 40)
    
    # Test data
    test_data = {
        "crop_type": "Tomato",
        "environmental_data": {
            "humidity_pct": 75.0,
            "leaf_wetness_duration_hours": 8.0,
            "rainfall_mm": 12.0,
            "min_temperature_c": 18.0,
            "max_temperature_c": 28.0,
            "avg_temperature_c": 23.0
        }
    }
    
    try:
        # Send POST request (assuming this endpoint exists)
        response = requests.post(
            f"{BASE_URL}/plant-health/disease-detection",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Disease Detection API Success!")
            print(f"   Disease: {result.get('disease_type', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Model Type: {result.get('model_info', {}).get('type', 'N/A')}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_weed_management_api():
    """Test the weed management API endpoint"""
    print("\n🌿 Testing Weed Management API")
    print("-" * 40)
    
    # Test data
    test_data = {
        "crop_type": "Wheat",
        "environmental_data": {
            "soil_moisture_pct": 35.0,
            "ndvi": 0.7,
            "canopy_cover_pct": 60.0,
            "weed_density_plants_per_m2": 30.0
        }
    }
    
    try:
        # Send POST request (assuming this endpoint exists)
        response = requests.post(
            f"{BASE_URL}/plant-health/weed-management",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Weed Management API Success!")
            print(f"   Dominant Species: {result.get('dominant_weed_species', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Model Type: {result.get('model_info', {}).get('type', 'N/A')}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_health_endpoint():
    """Test if the backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def main():
    """Run API integration tests"""
    print("🌱 AgriSense Plant Health API Integration Test")
    print("=" * 55)
    
    # Check if backend is running
    if not test_health_endpoint():
        print("\n💡 To start the backend, run:")
        print("   uvicorn agrisense_app.backend.main:app --reload --port 8004")
        return
    
    # Test APIs (these may not exist yet, but we can test)
    disease_success = test_disease_detection_api()
    weed_success = test_weed_management_api()
    
    print(f"\n📊 Test Summary")
    print("-" * 20)
    print(f"Backend Health: ✅")
    print(f"Disease API: {'✅' if disease_success else '❌'}")
    print(f"Weed API: {'✅' if weed_success else '❌'}")
    
    if disease_success and weed_success:
        print("\n🎉 All API tests passed!")
    else:
        print("\n⚠️  Some APIs may not be implemented yet.")
        print("   The engines are ready for integration!")

if __name__ == "__main__":
    main()