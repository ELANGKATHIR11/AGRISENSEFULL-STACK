#!/usr/bin/env python3
"""
Arduino Temperature Capture - Fixed for actual Arduino format
Captures temperature data in "Temperature: XX.XX *C" format
"""

import serial
import time
import datetime
import csv
import json
from typing import Optional

def capture_arduino_temperature():
    """Capture temperature data from Arduino with correct parsing"""
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === Arduino Temperature Capture (Fixed) ===")
    
    # Setup files
    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"arduino_temp_fixed_{timestamp_str}.csv"
    
    try:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecting to Arduino on COM3...")
        ser = serial.Serial('COM3', 9600, timeout=2)
        time.sleep(2)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Successfully connected!")
        
        # Create CSV with headers
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'temperature_celsius', 'raw_data'])
        
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting temperature capture...")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CSV file: {csv_filename}")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Press Ctrl+C to stop")
        print("=" * 60)
        
        reading_count = 0
        temperatures = []
        
        while True:
            if ser.in_waiting > 0:
                raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if raw_line:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Raw: {raw_line}")
                    
                    # Parse temperature from "Temperature: 25.39 *C" format
                    if "Temperature:" in raw_line and "*C" in raw_line:
                        try:
                            # Extract temperature value
                            temp_str = raw_line.split("Temperature:")[-1].replace("*C", "").strip()
                            temp_celsius = float(temp_str)
                            temperatures.append(temp_celsius)
                            
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Temperature: {temp_celsius:.2f}°C")
                            
                            # Save to CSV
                            timestamp = datetime.datetime.now().isoformat()
                            with open(csv_filename, 'a', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow([timestamp, temp_celsius, raw_line])
                            
                            reading_count += 1
                            
                            # Status update every 10 readings
                            if reading_count % 10 == 0:
                                avg_temp = sum(temperatures[-10:]) / min(len(temperatures), 10)
                                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Status: {reading_count} readings | Avg temp (last 10): {avg_temp:.2f}°C")
                        
                        except ValueError as e:
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Could not parse temperature: {e}")
                    
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Capture stopped by user")
    except Exception as e:
        print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Serial connection closed")
        
        if reading_count > 0:
            avg_temp = sum(temperatures) / len(temperatures)
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === CAPTURE SUMMARY ===")
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Total readings: {reading_count}")
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Temperature range: {min_temp:.1f}°C - {max_temp:.1f}°C")
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Average temperature: {avg_temp:.2f}°C")
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data saved to: {csv_filename}")

if __name__ == "__main__":
    capture_arduino_temperature()