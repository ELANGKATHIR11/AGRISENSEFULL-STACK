#!/usr/bin/env python3
"""
Test script for disease detection and weed management endpoints
"""
import requests
import json
import base64

# Create a simple test image (1x1 pixel PNG in base64)
test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFJOhXqXgAAAABJRU5ErkJggg=="

def test_disease_detection():
    """Test the disease detection endpoint"""
    url = "http://localhost:8004/disease/detect"
    
    payload = {
        "image_data": test_image_base64,
        "crop_type": "tomato",
        "environmental_data": {
            "temperature": 25.0,
            "humidity": 60.0,
            "soil_ph": 6.5
        }
    }
    
    try:
        print("Testing disease detection endpoint...")
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error testing disease detection: {e}")
        return None

def test_weed_analysis():
    """Test the weed analysis endpoint"""
    url = "http://localhost:8004/weed/analyze"
    
    payload = {
        "image_data": test_image_base64,
        "crop_type": "wheat",
        "environmental_data": {
            "temperature": 22.0,
            "humidity": 55.0,
            "soil_ph": 7.0
        }
    }
    
    try:
        print("\nTesting weed analysis endpoint...")
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error testing weed analysis: {e}")
        return None

if __name__ == "__main__":
    print("Starting image analysis endpoint tests...")
    
    # Test disease detection
    disease_response = test_disease_detection()
    
    # Test weed analysis  
    weed_response = test_weed_analysis()
    
    print("\nTest completed.")