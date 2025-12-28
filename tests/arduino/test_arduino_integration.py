"""
Quick test script for Arduino endpoints
"""
import requests
import json

# Test Arduino endpoints
backend_url = "http://127.0.0.1:8004"

def test_arduino_status():
    try:
        response = requests.get(f"{backend_url}/arduino/status", timeout=5)
        print(f"Arduino Status Response ({response.status_code}): {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Arduino status test failed: {e}")
        return False

def test_arduino_ingest():
    test_data = {
        "device_id": "ARDUINO_NANO_01",
        "device_type": "arduino_nano",
        "timestamp": "2025-09-16T11:00:00Z",
        "sensor_data": {
            "temperatures": {"ds18b20": 25.4, "dht22": 24.8},
            "humidity": 65.2,
            "avg_temperature": 25.1,
            "sensor_status": {"ds18b20": True, "dht22": True}
        }
    }
    
    try:
        response = requests.post(
            f"{backend_url}/arduino/ingest",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"Arduino Ingest Response ({response.status_code}): {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Arduino ingest test failed: {e}")
        return False

def test_health():
    try:
        response = requests.get(f"{backend_url}/", timeout=5)
        print(f"Health Response ({response.status_code}): {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Arduino Integration...")
    
    # Test basic health first
    if test_health():
        print("✅ Backend is running")
        
        # Test Arduino endpoints
        if test_arduino_status():
            print("✅ Arduino status endpoint works")
        else:
            print("❌ Arduino status endpoint failed")
            
        if test_arduino_ingest():
            print("✅ Arduino ingest endpoint works")
        else:
            print("❌ Arduino ingest endpoint failed")
    else:
        print("❌ Backend is not responding")
        
    print("Arduino integration test complete!")