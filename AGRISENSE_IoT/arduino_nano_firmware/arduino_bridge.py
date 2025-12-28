"""
AgriSense Arduino Nano Serial Bridge
Reads sensor data from Arduino Nano via serial connection
and forwards it to the AgriSense backend API
"""

import json
import time
import requests
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
import os
import sys

# Try to import serial module
try:
    import serial
    SerialType = serial.Serial
except ImportError:
    print("Warning: pyserial not installed. Install with: pip install pyserial")
    serial = None
    SerialType = None  # type: ignore

# Configuration
ARDUINO_PORT = "COM3"  # Updated to detected Arduino port
BAUD_RATE = 9600  # Updated to match Arduino's actual baud rate
BACKEND_URL = "http://127.0.0.1:8005"  # Updated to current backend port
DEVICE_ID = "ARDUINO_NANO_01"
RECONNECT_DELAY = 5  # seconds
API_TIMEOUT = 10  # seconds

# Admin token for API access (if required)
ADMIN_TOKEN = os.getenv("AGRISENSE_ADMIN_TOKEN", "your-admin-token-here")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arduino_bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ArduinoBridge:
    def __init__(self):
        self.serial_connection: Optional[Any] = None
        self.running = False
        self.last_data_time = time.time()
        
    def connect_arduino(self) -> bool:
        """Establish serial connection to Arduino"""
        if serial is None:
            logger.error("pyserial module not available. Cannot connect to Arduino.")
            return False
            
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                
            self.serial_connection = serial.Serial(
                port=ARDUINO_PORT,
                baudrate=BAUD_RATE,
                timeout=1,
                write_timeout=1
            )
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Send ping to verify connection
            if self.serial_connection:
                self.serial_connection.write(b"PING\n")
                response = self.serial_connection.readline().decode().strip()
            
                if response == "PONG":
                    logger.info(f"Successfully connected to Arduino on {ARDUINO_PORT}")
                    return True
                else:
                    logger.warning(f"Arduino ping failed. Response: {response}")
                    return False
            else:
                logger.error("Serial connection is None")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def send_to_backend(self, data: Dict[str, Any]) -> bool:
        """Send sensor data to AgriSense backend"""
        try:
            # Prepare data for backend API
            api_data = {
                "device_id": data.get("device_id", DEVICE_ID),
                "device_type": "arduino_nano",
                "timestamp": datetime.now().isoformat(),
                "sensor_data": data
            }
            
            # Send to Arduino-specific endpoint
            headers = {
                "Content-Type": "application/json",
                "X-Admin-Token": ADMIN_TOKEN
            }
            
            response = requests.post(
                f"{BACKEND_URL}/arduino/ingest",
                json=api_data,
                headers=headers,
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                logger.info("Successfully sent data to backend")
                return True
            else:
                logger.error(f"Backend API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to backend: {e}")
            return False
    
    def process_arduino_message(self, message: str) -> None:
        """Process incoming message from Arduino"""
        try:
            message = message.strip()
            
            if message.startswith("DATA:"):
                # Extract JSON data
                json_str = message[5:]  # Remove "DATA:" prefix
                data = json.loads(json_str)
                
                logger.info(f"Received sensor data: {data}")
                
                # Send to backend
                if self.send_to_backend(data):
                    self.last_data_time = time.time()
                    
            elif message.startswith("STATUS:"):
                # Extract status JSON
                json_str = message[7:]  # Remove "STATUS:" prefix
                status = json.loads(json_str)
                
                logger.info(f"Arduino status: {status}")
                
            elif "Temperature:" in message and "*C" in message:
                # Handle temperature format: "Temperature: 25.39 *C"
                try:
                    temp_str = message.split("Temperature:")[-1].replace("*C", "").strip()
                    temp_celsius = float(temp_str)
                    
                    # Create sensor data structure for backend
                    sensor_data = {
                        "device_id": DEVICE_ID,
                        "temperature_c": temp_celsius,
                        "sensor_type": "arduino_temperature",
                        "location": "greenhouse_sensor_01",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    logger.info(f"Temperature reading: {temp_celsius:.2f}°C")
                    
                    # Send to backend
                    if self.send_to_backend(sensor_data):
                        self.last_data_time = time.time()
                        
                except ValueError as e:
                    logger.error(f"Failed to parse temperature value: {e}")
                    
            elif message == "PONG":
                logger.debug("Arduino ping response received")
                
            else:
                logger.debug(f"Arduino message: {message}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Arduino: {e}")
        except Exception as e:
            logger.error(f"Error processing Arduino message: {e}")
    
    def read_serial_data(self) -> None:
        """Main loop to read data from Arduino"""
        while self.running:
            try:
                if not self.serial_connection or not self.serial_connection.is_open:
                    logger.info("Attempting to reconnect to Arduino...")
                    if not self.connect_arduino():
                        time.sleep(RECONNECT_DELAY)
                        continue
                
                # Read line from Arduino
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore')
                    if line.strip():
                        self.process_arduino_message(line)
                
                # Check for connection timeout
                if time.time() - self.last_data_time > 60:  # 1 minute timeout
                    logger.warning("No data received from Arduino for 1 minute")
                    self.last_data_time = time.time()
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                if serial and hasattr(serial, 'SerialException') and isinstance(e, serial.SerialException):
                    logger.error(f"Serial communication error: {e}")
                    time.sleep(RECONNECT_DELAY)
                else:
                    logger.error(f"Unexpected error in serial reading: {e}")
                    time.sleep(1)
    
    def start(self) -> None:
        """Start the Arduino bridge"""
        logger.info("Starting Arduino Bridge...")
        
        self.running = True
        
        # Start serial reading in a separate thread
        serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        serial_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the Arduino bridge"""
        logger.info("Stopping Arduino Bridge...")
        
        self.running = False
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
        logger.info("Arduino Bridge stopped")

def test_backend_connection() -> bool:
    """Test connection to AgriSense backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            logger.info("Backend connection test successful")
            return True
        else:
            logger.error(f"Backend test failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Backend connection test failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("AgriSense Arduino Bridge v1.0")
    
    # Test backend connection
    if not test_backend_connection():
        logger.error("Cannot connect to backend. Please ensure AgriSense backend is running.")
        return
    
    # Create and start bridge
    bridge = ArduinoBridge()
    bridge.start()

if __name__ == "__main__":
    main()