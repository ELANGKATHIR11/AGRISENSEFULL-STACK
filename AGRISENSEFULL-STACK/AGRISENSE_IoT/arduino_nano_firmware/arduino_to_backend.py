#!/usr/bin/env python3
"""
Arduino to AgriSense Backend Integration
Live temperature data capture with backend API forwarding
"""

import serial
import json
import time
import datetime
import requests
import csv
from typing import Optional

class ArduinoBackendBridge:
    def __init__(self, 
                 serial_port: str = 'COM3',
                 baud_rate: int = 9600,
                 backend_url: str = 'http://localhost:8005'):
        
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.backend_url = backend_url
        self.serial_conn: Optional[serial.Serial] = None
        self.session = requests.Session()
        
        # CSV file for local backup
        self.csv_file = f"arduino_backend_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
    def connect_arduino(self) -> bool:
        """Connect to Arduino via serial"""
        try:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecting to Arduino on {self.serial_port}...")
            self.serial_conn = serial.Serial(self.serial_port, self.baud_rate, timeout=2)
            time.sleep(2)  # Allow Arduino to initialize
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully connected to Arduino")
            return True
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to connect to Arduino: {e}")
            return False
    
    def test_backend_connection(self) -> bool:
        """Test connection to AgriSense backend"""
        try:
            response = self.session.get(f"{self.backend_url}/arduino/status")
            if response.status_code == 200:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backend connection successful")
                return True
            else:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backend returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backend connection failed: {e}")
            return False
    
    def parse_sensor_reading(self, raw_line: str) -> Optional[dict]:
        """Parse Arduino sensor reading into structured data"""
        try:
            # Handle Arduino temperature format: "Temperature: 25.39 *C"
            if "Temperature:" in raw_line and "*C" in raw_line:
                # Extract temperature value from "Temperature: 25.39 *C"
                temp_str = raw_line.split("Temperature:")[-1].replace("*C", "").strip()
                temp_value = float(temp_str)
                
                # Create AgriSense-compatible sensor reading
                sensor_data = {
                    "device_id": "arduino_nano_001",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "temperature_c": temp_value,
                    "sensor_type": "arduino_temp_sensor",
                    "raw_value": temp_value,
                    "location": "greenhouse_sensor_01"
                }
                return sensor_data
            elif "Sensor Value:" in raw_line:
                # Legacy format - convert raw analog to celsius
                value_str = raw_line.split("Sensor Value:")[-1].strip()
                raw_value = float(value_str)
                # Convert analog reading to celsius (TMP36 sensor)
                voltage = (raw_value * 5.0) / 1024.0
                temp_celsius = (voltage - 0.5) * 100.0
                
                sensor_data = {
                    "device_id": "arduino_nano_001",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "temperature_c": temp_celsius,
                    "sensor_type": "arduino_analog_temp",
                    "raw_value": raw_value,
                    "location": "greenhouse_sensor_01"
                }
                return sensor_data
            elif raw_line.strip().startswith('{'):
                # Handle JSON format if Arduino sends it
                return json.loads(raw_line.strip())
            else:
                return None
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error parsing sensor data: {e}")
            return None
    
    def send_to_backend(self, sensor_data: dict) -> bool:
        """Send sensor data to AgriSense backend"""
        try:
            # Send to Arduino ingest endpoint
            response = self.session.post(
                f"{self.backend_url}/arduino/ingest",
                json=sensor_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Data sent to backend successfully")
                return True
            else:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Backend rejected data: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Failed to send to backend: {e}")
            return False
    
    def save_to_csv(self, sensor_data: dict):
        """Save data to local CSV backup"""
        try:
            # Check if file exists to determine if we need headers
            file_exists = False
            try:
                with open(self.csv_file, 'r'):
                    file_exists = True
            except FileNotFoundError:
                pass
            
            with open(self.csv_file, 'a', newline='') as csvfile:
                fieldnames = ['timestamp', 'device_id', 'temperature_c', 'raw_value', 'sensor_type', 'location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(sensor_data)
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error saving to CSV: {e}")
    
    def run_bridge(self):
        """Main bridge execution loop"""
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === Arduino to AgriSense Backend Bridge Started ===")
        
        # Test connections
        if not self.connect_arduino():
            return
        
        backend_available = self.test_backend_connection()
        if not backend_available:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Warning: Backend not available, will save to CSV only")
        
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting live data capture and forwarding...")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CSV backup file: {self.csv_file}")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Press Ctrl+C to stop")
        print("=" * 80)
        
        reading_count = 0
        try:
            while True:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    # Read from Arduino
                    raw_line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if raw_line:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Raw: {raw_line}")
                        
                        # Parse sensor data
                        sensor_data = self.parse_sensor_reading(raw_line)
                        
                        if sensor_data:
                            reading_count += 1
                            
                            # Save to CSV backup
                            self.save_to_csv(sensor_data)
                            
                            # Send to backend if available
                            if backend_available:
                                success = self.send_to_backend(sensor_data)
                                if not success:
                                    # Retry backend connection test
                                    backend_available = self.test_backend_connection()
                            
                            # Status update every 10 readings
                            if reading_count % 10 == 0:
                                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Status: {reading_count} readings processed")
                
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bridge stopped by user")
        except Exception as e:
            print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bridge error: {e}")
        finally:
            if self.serial_conn:
                self.serial_conn.close()
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Serial connection closed")
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Total readings captured: {reading_count}")
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data saved to: {self.csv_file}")

if __name__ == "__main__":
    bridge = ArduinoBackendBridge(
        serial_port='COM3',
        baud_rate=9600,
        backend_url='http://localhost:8005'
    )
    bridge.run_bridge()