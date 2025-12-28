#!/usr/bin/env python3
"""
Arduino Temperature Diagnostic Tool
Analyzes the actual sensor data being sent and provides conversion
"""

import serial
import time
import json
import math

def convert_analog_to_celsius(analog_value):
    """
    Convert analog sensor reading to Celsius
    Assuming TMP36 or similar analog temperature sensor
    """
    # TMP36 conversion: Voltage = (analog_value * 5.0) / 1024.0
    # Temperature = (Voltage - 0.5) * 100
    voltage = (analog_value * 5.0) / 1024.0
    celsius = (voltage - 0.5) * 100.0
    return celsius

def convert_thermistor_to_celsius(analog_value):
    """
    Convert thermistor reading to Celsius using Steinhart-Hart equation
    """
    # Typical 10K thermistor values
    R1 = 10000  # resistance at 25°C
    c1 = 1.009249522e-03
    c2 = 2.378405444e-04
    c3 = 2.019202697e-07
    
    R2 = R1 * (1024.0 / analog_value - 1.0)
    logR2 = math.log(R2)
    T = (1.0 / (c1 + c2*logR2 + c3*logR2*logR2*logR2))
    celsius = T - 273.15
    return celsius

def analyze_arduino_data():
    """Analyze what the Arduino is actually sending"""
    try:
        print("=" * 60)
        print("Arduino Temperature Diagnostic Tool")
        print("=" * 60)
        print("Connecting to Arduino on COM3...")
        
        ser = serial.Serial('COM3', 9600, timeout=2)
        time.sleep(2)
        
        print("✓ Connected! Analyzing data...")
        print("Raw data from Arduino:")
        print("-" * 40)
        
        reading_count = 0
        raw_values = []
        
        while reading_count < 10:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[{reading_count+1}] Raw: {line}")
                    
                    # Try to extract numeric value
                    if "Sensor Value:" in line:
                        try:
                            value_str = line.split("Sensor Value:")[-1].strip()
                            raw_value = float(value_str)
                            raw_values.append(raw_value)
                            
                            # Convert using different methods
                            tmp36_temp = convert_analog_to_celsius(raw_value)
                            thermistor_temp = convert_thermistor_to_celsius(raw_value)
                            
                            print(f"    Raw value: {raw_value}")
                            print(f"    TMP36 conversion: {tmp36_temp:.1f}°C")
                            print(f"    Thermistor conversion: {thermistor_temp:.1f}°C")
                            print(f"    Direct value: {raw_value:.1f}°C")
                            print("-" * 40)
                            
                        except ValueError:
                            pass
                    
                    elif line.startswith('{'):
                        # JSON data
                        try:
                            data = json.loads(line)
                            print(f"    JSON data: {data}")
                            if 'temperature' in data:
                                print(f"    Temperature: {data['temperature']}°C")
                        except json.JSONDecodeError:
                            pass
                    
                    reading_count += 1
            
            time.sleep(0.5)
        
        ser.close()
        
        if raw_values:
            avg_raw = sum(raw_values) / len(raw_values)
            print("\n" + "=" * 60)
            print("ANALYSIS RESULTS:")
            print("=" * 60)
            print(f"Average raw value: {avg_raw:.1f}")
            print(f"Room temperature (~25°C) conversions:")
            print(f"  • TMP36 method: {convert_analog_to_celsius(avg_raw):.1f}°C")
            print(f"  • Thermistor method: {convert_thermistor_to_celsius(avg_raw):.1f}°C")
            print(f"  • Direct reading: {avg_raw:.1f}°C")
            print("\nRecommendation:")
            
            # Determine which conversion is closest to 25°C
            tmp36_diff = abs(convert_analog_to_celsius(avg_raw) - 25.0)
            thermistor_diff = abs(convert_thermistor_to_celsius(avg_raw) - 25.0)
            direct_diff = abs(avg_raw - 25.0)
            
            if tmp36_diff < thermistor_diff and tmp36_diff < direct_diff:
                print("  • Use TMP36 conversion (closest to expected 25°C)")
            elif thermistor_diff < direct_diff:
                print("  • Use Thermistor conversion (closest to expected 25°C)")
            else:
                print("  • Arduino may already be sending Celsius values")
                print("  • Check if sensor calibration is needed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_arduino_data()