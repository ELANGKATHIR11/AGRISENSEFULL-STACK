#!/usr/bin/env python3
"""
Simple Arduino Temperature Sensor Data Capture
Reads temperature data from Arduino via serial connection
Based on user's specified code with enhancements
"""

import serial
import time
import json
import csv
from datetime import datetime
import os

# Configuration
ARDUINO_PORT = 'COM3'  # Your Arduino's serial port
BAUD_RATE = 9600  # Standard Arduino baud rate
DATA_FILE = 'arduino_temperature_data.csv'
LOG_FILE = 'arduino_capture.log'

def log_message(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # Also write to log file
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + '\n')

def initialize_csv():
    """Initialize CSV file with headers if it doesn't exist"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Raw_Data', 'Temperature_C', 'Humidity_%', 'Sensor_Type'])
        log_message(f"Created new data file: {DATA_FILE}")

def parse_arduino_data(line):
    """Parse Arduino data - try to extract temperature values"""
    data_entry = {
        'timestamp': datetime.now().isoformat(),
        'raw_data': line,
        'temperature_c': None,
        'humidity_pct': None,
        'sensor_type': 'unknown'
    }
    
    try:
        # Try to parse as JSON first (if using our firmware)
        if line.startswith('DATA:'):
            json_str = line[5:]  # Remove "DATA:" prefix
            parsed = json.loads(json_str)
            
            if 'ds18b20_temp' in parsed:
                data_entry['temperature_c'] = parsed['ds18b20_temp']
                data_entry['sensor_type'] = 'DS18B20'
            elif 'dht22_temp' in parsed:
                data_entry['temperature_c'] = parsed['dht22_temp']
                data_entry['humidity_pct'] = parsed.get('dht22_humidity')
                data_entry['sensor_type'] = 'DHT22'
                
        # Try to parse simple temperature format like "Temperature: 23.5°C"
        elif 'Temperature:' in line or 'Temp:' in line:
            import re
            temp_match = re.search(r'(\d+\.?\d*)', line)
            if temp_match:
                data_entry['temperature_c'] = float(temp_match.group(1))
                data_entry['sensor_type'] = 'Generic'
                
        # Try to parse simple numeric value (assume it's temperature)
        elif line.replace('.', '').replace('-', '').isdigit():
            data_entry['temperature_c'] = float(line)
            data_entry['sensor_type'] = 'Numeric'
            
    except (json.JSONDecodeError, ValueError) as e:
        log_message(f"Could not parse data: {line} - Error: {e}")
    
    return data_entry

def save_to_csv(data_entry):
    """Save data entry to CSV file"""
    with open(DATA_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            data_entry['timestamp'],
            data_entry['raw_data'],
            data_entry['temperature_c'],
            data_entry['humidity_pct'],
            data_entry['sensor_type']
        ])

def main():
    """Main data capture function"""
    log_message("=== Arduino Temperature Data Capture Started ===")
    log_message(f"Connecting to Arduino on {ARDUINO_PORT} at {BAUD_RATE} baud...")
    
    # Initialize CSV file
    initialize_csv()
    
    try:
        # Create serial connection
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Allow time for serial connection to establish
        
        log_message(f"Successfully connected to {ARDUINO_PORT}")
        log_message("Starting data capture... Press Ctrl+C to stop")
        log_message("=" * 50)
        
        data_count = 0
        
        while True:
            if ser.in_waiting > 0:
                # Read line from Arduino
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line:  # Only process non-empty lines
                    data_count += 1
                    
                    # Parse and display data
                    data_entry = parse_arduino_data(line)
                    
                    # Format output for console
                    if data_entry['temperature_c'] is not None:
                        temp_str = f"Temperature: {data_entry['temperature_c']}°C"
                        if data_entry['humidity_pct'] is not None:
                            temp_str += f" | Humidity: {data_entry['humidity_pct']}%"
                        temp_str += f" [{data_entry['sensor_type']}]"
                        log_message(temp_str)
                    else:
                        log_message(f"Raw: {line}")
                    
                    # Save to CSV
                    save_to_csv(data_entry)
                    
                    # Show progress every 10 readings
                    if data_count % 10 == 0:
                        log_message(f"Captured {data_count} readings so far...")
            
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
            
    except serial.SerialException as e:
        log_message(f"Serial connection error: {e}")
        log_message("Make sure:")
        log_message("1. Arduino is connected to the correct port")
        log_message("2. No other applications are using the serial port")
        log_message("3. Arduino firmware is uploaded and running")
        
    except KeyboardInterrupt:
        log_message("Data capture stopped by user")
        
    except Exception as e:
        log_message(f"Unexpected error: {e}")
        
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            log_message("Serial connection closed")
        
        log_message(f"Data saved to: {DATA_FILE}")
        log_message(f"Log saved to: {LOG_FILE}")
        log_message("=== Arduino Temperature Data Capture Ended ===")

if __name__ == "__main__":
    main()