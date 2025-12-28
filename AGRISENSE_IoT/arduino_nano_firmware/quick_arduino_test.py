#!/usr/bin/env python3
"""
Quick test to send Arduino data and immediately check status
"""

import requests
import json
from datetime import datetime

# Backend URL
backend_url = "http://127.0.0.1:8005"

def quick_test():
    current_temp = 26.5
    
    # Send Arduino data
    arduino_data = {
        "device_id": "ARDUINO_NANO_01",
        "device_type": "arduino_nano",
        "timestamp": datetime.now().isoformat(),
        "sensor_data": {
            "temperatures": {
                "ds18b20": current_temp,
                "dht22": current_temp + 0.3
            },
            "avg_temperature": current_temp,
            "humidity": 60.0,
            "sensor_status": {
                "ds18b20": True,
                "dht22": True
            }
        }
    }
    
    # Send data
    response = requests.post(
        f"{backend_url}/arduino/ingest",
        json=arduino_data,
        headers={
            "Content-Type": "application/json",
            "X-Admin-Token": "your-admin-token-here"
        }
    )
    
    print(f"Data sent: {response.status_code} - {response.json()}")
    
    # Immediately check status
    status_response = requests.get(f"{backend_url}/arduino/status")
    status_data = status_response.json()
    print(f"Arduino status: {status_data}")

if __name__ == "__main__":
    quick_test()