#!/usr/bin/env python3
"""
Test the Arduino ingest endpoint directly
"""

import requests
import json
from datetime import datetime

# Backend URL
backend_url = "http://127.0.0.1:8005"

def test_arduino_ingest():
    """Test the Arduino ingest endpoint"""
    
    # Simulate data from Arduino bridge
    arduino_data = {
        "device_id": "ARDUINO_NANO_01",
        "device_type": "arduino_nano",
        "timestamp": datetime.now().isoformat(),
        "sensor_data": {
            "temperature": 25.35,
            "humidity": 65.0,
            "device_id": "ARDUINO_NANO_01",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        print("🌡️ Testing Arduino ingest endpoint...")
        response = requests.post(
            f"{backend_url}/arduino/ingest",
            json=arduino_data,
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": "your-admin-token-here"
            }
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Arduino ingest endpoint working correctly!")
            return True
        else:
            print(f"❌ Arduino ingest failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - is it running on port 8005?")
        return False
    except Exception as e:
        print(f"❌ Error testing Arduino ingest: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Arduino Ingest Endpoint\n")
    success = test_arduino_ingest()
    
    if success:
        print("\n🎉 Arduino ingest endpoint ready for live temperature data!")
    else:
        print("\n⚠️ Arduino ingest endpoint needs fixing.")