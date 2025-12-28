"""
Arduino Integration Test Script
Simulates Arduino sensor data and tests the complete integration pipeline
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8004"
ADMIN_TOKEN = "your-admin-token-here"  # Update with your token

def test_arduino_endpoint():
    """Test the Arduino data ingestion endpoint"""
    print("Testing Arduino data ingestion endpoint...")
    
    # Simulate Arduino sensor data
    test_data = {
        "device_id": "ARDUINO_NANO_TEST",
        "device_type": "arduino_nano",
        "timestamp": datetime.now().isoformat(),
        "sensor_data": {
            "temperatures": {
                "ds18b20": round(20 + random.uniform(-5, 15), 1),
                "dht22": round(22 + random.uniform(-3, 12), 1)
            },
            "humidity": round(50 + random.uniform(-20, 30), 1),
            "avg_temperature": round(21 + random.uniform(-4, 13), 1),
            "sensor_status": {
                "ds18b20": True,
                "dht22": True
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Token": ADMIN_TOKEN
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/arduino/ingest",
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Arduino data ingestion successful!")
            print(f"   Zone ID: {result.get('zone_id')}")
            print(f"   Temperature recorded: {result.get('temperature_recorded')}°C")
            print(f"   Device ID: {result.get('device_id')}")
            return True
        else:
            print(f"❌ Arduino ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Arduino ingestion error: {e}")
        return False

def test_arduino_status():
    """Test the Arduino status endpoint"""
    print("\nTesting Arduino status endpoint...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/arduino/status", timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Arduino status endpoint working!")
            print(f"   Status: {status.get('status')}")
            print(f"   Total devices: {status.get('total_devices')}")
            print(f"   Recent readings: {len(status.get('recent_readings', []))}")
            
            if status.get('recent_readings'):
                latest = status['recent_readings'][0]
                print(f"   Latest reading: {latest['temperature']}°C from {latest['zone_id']}")
            
            return True
        else:
            print(f"❌ Arduino status failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Arduino status error: {e}")
        return False

def test_backend_connection():
    """Test basic backend connectivity"""
    print("Testing backend connection...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend connection successful!")
            return True
        else:
            print(f"❌ Backend connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return False

def simulate_serial_data():
    """Simulate the JSON data format sent by Arduino"""
    print("\nSimulating Arduino serial data format...")
    
    # This is what the Arduino sends via serial
    arduino_json = {
        "device_id": "ARDUINO_NANO_01",
        "device_type": "arduino_nano",
        "timestamp": int(time.time() * 1000),  # Arduino millis()
        "temperatures": {
            "ds18b20": round(24.5 + random.uniform(-2, 4), 1),
            "dht22": round(25.1 + random.uniform(-1.5, 3.5), 1)
        },
        "humidity": round(62.3 + random.uniform(-10, 15), 1),
        "sensor_status": {
            "ds18b20": True,
            "dht22": True
        },
        "avg_temperature": round(24.8 + random.uniform(-1.8, 3.8), 1)
    }
    
    print("Arduino would send:")
    print(f"DATA:{json.dumps(arduino_json)}")
    
    return arduino_json

def run_integration_test():
    """Run complete integration test"""
    print("🔧 Arduino AgriSense Integration Test")
    print("=" * 50)
    
    # Test backend connection
    if not test_backend_connection():
        print("❌ Cannot connect to backend. Please ensure AgriSense backend is running.")
        return
    
    # Simulate multiple data points
    success_count = 0
    for i in range(3):
        print(f"\n📊 Test {i+1}/3: Sending Arduino data...")
        
        if test_arduino_endpoint():
            success_count += 1
        
        time.sleep(2)  # Wait between tests
    
    # Test status endpoint
    test_arduino_status()
    
    # Show serial simulation
    simulate_serial_data()
    
    # Results
    print(f"\n📈 Test Results:")
    print(f"   Successful ingestions: {success_count}/3")
    print(f"   Success rate: {(success_count/3)*100:.1f}%")
    
    if success_count == 3:
        print("✅ Arduino integration test PASSED!")
        print("\n🚀 Next steps:")
        print("   1. Upload firmware to your Arduino Nano")
        print("   2. Connect temperature sensors (DS18B20/DHT22)")
        print("   3. Run the Python serial bridge")
        print("   4. Check the Dashboard for live Arduino data")
    else:
        print("❌ Arduino integration test FAILED!")
        print("\n🔍 Troubleshooting:")
        print("   1. Check backend is running on port 8004")
        print("   2. Verify ADMIN_TOKEN is correct")
        print("   3. Check network connectivity")

if __name__ == "__main__":
    run_integration_test()