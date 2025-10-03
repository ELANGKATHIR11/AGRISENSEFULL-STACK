#!/usr/bin/env python3
"""
Simulate Arduino temperature data for testing the dashboard
"""

import requests
import json
import time
import random
from datetime import datetime

# Backend URL
backend_url = "http://127.0.0.1:8005"

def simulate_arduino_data():
    """Simulate Arduino temperature readings and send to backend"""
    
    base_temp = 25.0  # Base temperature around 25°C
    
    for i in range(5):
        # Generate realistic temperature variation
        temp_variation = random.uniform(-2.0, 3.0)
        current_temp = base_temp + temp_variation
        
        # Simulate Arduino data format (matching expected backend structure)
        arduino_data = {
            "device_id": "ARDUINO_NANO_01",
            "device_type": "arduino_nano",
            "timestamp": datetime.now().isoformat(),
            "sensor_data": {
                "temperatures": {
                    "ds18b20": current_temp,
                    "dht22": current_temp + random.uniform(-0.5, 0.5)
                },
                "avg_temperature": current_temp,
                "humidity": 65.0 + random.uniform(-5, 5),
                "sensor_status": {
                    "ds18b20": True,
                    "dht22": True
                }
            }
        }
        
        try:
            print(f"📡 Sending Arduino data - Temperature: {current_temp:.1f}°C")
            response = requests.post(
                f"{backend_url}/arduino/ingest",
                json=arduino_data,
                headers={
                    "Content-Type": "application/json",
                    "X-Admin-Token": "your-admin-token-here"
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Data sent successfully - Response: {response.json()}")
            else:
                print(f"❌ Failed to send data - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending data: {e}")
        
        # Wait between readings
        time.sleep(2)
    
    # Check Arduino status
    try:
        print("\n🔍 Checking Arduino status...")
        status_response = requests.get(f"{backend_url}/arduino/status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"📊 Arduino Status: {status_data['status']}")
            print(f"🔢 Total Devices: {status_data['total_devices']}")
            print(f"📈 Recent Readings: {len(status_data['recent_readings'])}")
            if status_data['recent_readings']:
                latest = status_data['recent_readings'][0]
                print(f"🌡️ Latest Temperature: {latest['temperature']}°C at {latest['timestamp']}")
        else:
            print(f"❌ Failed to get status - Status: {status_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    print("🚀 Starting Arduino Temperature Simulation\n")
    simulate_arduino_data()
    print("\n🏁 Simulation complete! Check the dashboard for live temperature data.")