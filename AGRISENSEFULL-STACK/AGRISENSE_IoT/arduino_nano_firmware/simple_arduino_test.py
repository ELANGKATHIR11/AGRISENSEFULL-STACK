#!/usr/bin/env python3
"""
Simple Arduino Serial Test - based on user's code
Tests basic serial communication with Arduino
"""

import serial
import time

def main():
    print("Testing Arduino connection on COM3...")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    try:
        ser = serial.Serial('COM3', 9600)  # Replace 'COM3' with your Arduino's serial port
        time.sleep(2)  # Allow time for serial connection to establish
        
        print("Connected! Reading data...")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] {line}")
                
                # You can also write 'line' to a file here
                with open('arduino_readings.txt', 'a') as f:
                    f.write(f"[{timestamp}] {line}\n")
                    
    except KeyboardInterrupt:
        print("\nExiting data capture.")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Make sure Arduino is connected and no other program is using the port")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()
            print("Serial connection closed")

if __name__ == "__main__":
    main()