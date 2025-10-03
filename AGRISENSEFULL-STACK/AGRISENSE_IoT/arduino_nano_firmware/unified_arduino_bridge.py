"""
AgriSense Arduino Bridge - Unified and Organized
Handles all Arduino sensor communication and data forwarding
"""

import json
import time
import requests
import threading
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Try to import serial module
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    print("Warning: pyserial not installed. Install with: pip install pyserial")
    serial = None
    SERIAL_AVAILABLE = False

# Configuration
ARDUINO_PORT = os.getenv("ARDUINO_PORT", "COM3")
BAUD_RATE = int(os.getenv("ARDUINO_BAUD_RATE", "9600"))
BACKEND_URL = os.getenv("AGRISENSE_BACKEND_URL", "http://127.0.0.1:8004")
DEVICE_ID = os.getenv("ARDUINO_DEVICE_ID", "ARDUINO_NANO_01")
RECONNECT_DELAY = int(os.getenv("ARDUINO_RECONNECT_DELAY", "5"))
API_TIMEOUT = int(os.getenv("ARDUINO_API_TIMEOUT", "10"))

# Admin token for API access
ADMIN_TOKEN = os.getenv("AGRISENSE_ADMIN_TOKEN", "your-admin-token-here")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arduino_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ArduinoBridge:
    """Unified Arduino Bridge for sensor data collection and forwarding"""
    
    def __init__(self):
        self.serial_connection: Optional[Any] = None
        self.running = False
        self.last_data_time = 0
        self.connection_thread = None
        
    def connect_arduino(self) -> bool:
        """Establish serial connection to Arduino"""
        if not SERIAL_AVAILABLE:
            logger.error("pyserial module not available. Cannot connect to Arduino.")
            return False
            
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                
            if serial:
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
                self.serial_connection.write(b"PING\\n")
                response = self.serial_connection.readline().decode().strip()
            
                if response == "PONG":
                    logger.info(f"Successfully connected to Arduino on {ARDUINO_PORT}")
                    return True
                else:
                    logger.warning(f"Arduino ping failed. Response: {response}")
                    return False
            else:
                logger.error("Serial connection failed to initialize")
                return False
                logger.warning(f"Arduino ping failed. Response: {response}")
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

    def run(self):
        """Main loop to read Arduino data and forward to backend"""
        logger.info("Starting Arduino Bridge...")
        
        if not SERIAL_AVAILABLE:
            logger.error("Cannot start bridge - pyserial not available")
            return
            
        self.running = True
        
        while self.running:
            try:
                if not self.connect_arduino():
                    logger.warning(f"Failed to connect to Arduino. Retrying in {RECONNECT_DELAY} seconds...")
                    time.sleep(RECONNECT_DELAY)
                    continue
                
                logger.info("Arduino bridge is running. Reading sensor data...")
                
                while self.running and self.serial_connection and self.serial_connection.is_open:
                    try:
                        if self.serial_connection.in_waiting > 0:
                            line = self.serial_connection.readline().decode().strip()
                            if line:
                                self.process_arduino_message(line)
                        else:
                            time.sleep(0.1)  # Small delay to prevent busy waiting
                            
                    except Exception as e:
                        logger.error(f"Error reading from Arduino: {e}")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Shutting down Arduino bridge...")
                break
            except Exception as e:
                logger.error(f"Arduino bridge error: {e}")
                time.sleep(RECONNECT_DELAY)
                
        self.cleanup()
    
    def process_arduino_message(self, message: str):
        """Process incoming message from Arduino"""
        try:
            message = message.strip()
            logger.debug(f"Received message: {message}")
            
            if message.startswith("DATA:"):
                # Extract JSON data
                json_str = message[5:]  # Remove "DATA:" prefix
                data = json.loads(json_str)
                
                logger.info(f"Received sensor data: {data}")
                
                # Send to backend
                if self.send_to_backend(data):
                    self.last_data_time = time.time()
                    
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
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    logger.info(f"Parsed temperature: {temp_celsius}°C")
                    
                    # Send to backend
                    self.send_to_backend(sensor_data)
                    
                except ValueError as e:
                    logger.error(f"Failed to parse temperature: {e}")
                    
            else:
                logger.debug(f"Unhandled message: {message}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        logger.info("Arduino bridge cleaned up")


def main():
    """Main entry point"""
    bridge = ArduinoBridge()
    try:
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        bridge.cleanup()


if __name__ == "__main__":
    main()