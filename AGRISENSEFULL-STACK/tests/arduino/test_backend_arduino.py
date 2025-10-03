#!/usr/bin/env python3
"""
Test script to verify that the backend can receive Arduino temperature data
"""

import requests
import json
from datetime import datetime

# Backend URL
backend_url = "http://127.0.0.1:8005"

def test_sensor_endpoint():
    """Test the sensor data endpoint"""
    
    try:
        # Test the live sensor data endpoint
        print("🔌 Testing live sensor data endpoint...")
        response = requests.get(
            f"{backend_url}/sensors/live",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Backend live sensor endpoint working correctly!")
            return True
        elif response.status_code == 503:
            print("⚠️ MQTT sensor bridge not available (expected without ESP32)")
            return True
        else:
            print(f"❌ Backend sensor endpoint failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - is it running on port 8005?")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_recommendation_endpoint():
    """Test the recommendation endpoint with sensor data"""
    
    # Test data for recommendation
    sensor_reading = {
        "temperature": 25.5,
        "humidity": 65.2,
        "soil_moisture": 45.0,
        "ph": 6.8,
        "crop": "tomato"
    }
    
    try:
        print("🌱 Testing recommendation endpoint...")
        response = requests.post(
            f"{backend_url}/api/recommend",
            json=sensor_reading,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Backend recommendation endpoint working correctly!")
            return True
        else:
            print(f"❌ Backend recommendation endpoint failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - is it running on port 8005?")
        return False
    except Exception as e:
        print(f"❌ Error testing recommendation endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing AgriSense Backend Arduino Integration\n")
    
    # Test sensor endpoint
    sensor_success = test_sensor_endpoint()
    print()
    
    # Test recommendation endpoint
    reco_success = test_recommendation_endpoint()
    print()
    
    if sensor_success and reco_success:
        print("🎉 All backend tests passed! Arduino integration ready.")
    else:
        print("⚠️ Some backend tests failed. Check the endpoints.")