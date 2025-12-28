#!/usr/bin/env python3
"""
AgriSense MQTT Sensor Data Bridge
Receives real-time sensor data from ESP32 and forwards to AgriSense backend
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
import requests
import threading
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AgriSense-MQTT-Bridge')

@dataclass
class SensorReading:
    """Structure for sensor data"""
    device_id: str
    location: str
    timestamp: str
    air_temperature: float
    humidity: float
    soil_moisture_percentage: float
    soil_temperature: float
    ph_level: float
    light_intensity_percentage: float
    pump_active: bool
    wifi_rssi: int
    
class AgriSenseMQTTBridge:
    def __init__(self):
        # MQTT Configuration
        self.mqtt_broker = "localhost"
        self.mqtt_port = 1883
        self.mqtt_client = mqtt.Client()
        
        # AgriSense Backend Configuration
        self.backend_url = "http://127.0.0.1:8004"
        self.admin_token = "your-admin-token-here"  # Set your admin token
        
        # Data storage
        self.latest_sensor_data = {}
        self.sensor_history = []
        self.max_history = 1000  # Keep last 1000 readings
        
        # Setup MQTT client
        self.setup_mqtt()
        
        # Status tracking
        self.connected_devices = set()
        self.last_data_time = {}
        
    def setup_mqtt(self):
        """Configure MQTT client"""
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            # Subscribe to all AgriSense sensor topics
            topics = [
                "agrisense/sensors/data",
                "agrisense/devices/heartbeat", 
                "agrisense/pump/status"
            ]
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        logger.warning("Disconnected from MQTT broker")
        
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received message on {topic}")
            
            if topic == "agrisense/sensors/data":
                self.handle_sensor_data(payload)
            elif topic == "agrisense/devices/heartbeat":
                self.handle_device_heartbeat(payload)
            elif topic == "agrisense/pump/status":
                self.handle_pump_status(payload)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_sensor_data(self, data: Dict[str, Any]):
        """Process incoming sensor data"""
        try:
            device_id = data.get("device_id", "unknown")
            sensors = data.get("sensors", {})
            status = data.get("status", {})
            
            # Create sensor reading object
            reading = SensorReading(
                device_id=device_id,
                location=data.get("location", "unknown"),
                timestamp=datetime.now().isoformat(),
                air_temperature=sensors.get("air_temperature", 0.0),
                humidity=sensors.get("humidity", 0.0),
                soil_moisture_percentage=sensors.get("soil_moisture_percentage", 0.0),
                soil_temperature=sensors.get("soil_temperature", 0.0),
                ph_level=sensors.get("ph_level", 7.0),
                light_intensity_percentage=sensors.get("light_intensity_percentage", 0.0),
                pump_active=status.get("pump_active", False),
                wifi_rssi=status.get("wifi_rssi", -100)
            )
            
            # Store latest data
            self.latest_sensor_data[device_id] = reading
            self.last_data_time[device_id] = time.time()
            self.connected_devices.add(device_id)
            
            # Add to history
            self.sensor_history.append(reading)
            if len(self.sensor_history) > self.max_history:
                self.sensor_history.pop(0)
            
            logger.info(f"Processed sensor data from {device_id}: "
                       f"Temp={reading.air_temperature}°C, "
                       f"Humidity={reading.humidity}%, "
                       f"Soil Moisture={reading.soil_moisture_percentage}%")
            
            # Forward to AgriSense backend
            self.forward_to_backend(reading)
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    def handle_device_heartbeat(self, data: Dict[str, Any]):
        """Process device heartbeat messages"""
        device_id = data.get("device_id", "unknown")
        self.connected_devices.add(device_id)
        self.last_data_time[device_id] = time.time()
        logger.info(f"Heartbeat from {device_id}")
    
    def handle_pump_status(self, data: Dict[str, Any]):
        """Process pump status updates"""
        device_id = data.get("device_id", "unknown")
        pump_status = data.get("pump_active", False)
        logger.info(f"Pump status update from {device_id}: {'ON' if pump_status else 'OFF'}")
    
    def forward_to_backend(self, reading: SensorReading):
        """Forward sensor data to AgriSense backend API"""
        try:
            # Convert to format expected by AgriSense backend
            payload = {
                "device_id": reading.device_id,
                "location": reading.location,
                "temperature_c": reading.air_temperature,
                "humidity_pct": reading.humidity,
                "soil_moisture_pct": reading.soil_moisture_percentage,
                "soil_temperature_c": reading.soil_temperature,
                "ph": reading.ph_level,
                "light_intensity_pct": reading.light_intensity_percentage,
                "timestamp": reading.timestamp
            }
            
            # Send to edge ingest endpoint
            headers = {
                "Content-Type": "application/json",
                "X-Admin-Token": self.admin_token
            }
            
            response = requests.post(
                f"{self.backend_url}/edge/ingest",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Successfully forwarded sensor data to AgriSense backend")
            else:
                logger.warning(f"Backend returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to forward data to backend: {e}")
        except Exception as e:
            logger.error(f"Error forwarding to backend: {e}")
    
    def get_latest_data(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get latest sensor data for API access"""
        if device_id:
            reading = self.latest_sensor_data.get(device_id)
            return asdict(reading) if reading else {}
        else:
            return {device_id: asdict(reading) 
                   for device_id, reading in self.latest_sensor_data.items()}
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get status of connected devices"""
        current_time = time.time()
        status = {}
        
        for device_id in self.connected_devices:
            last_seen = self.last_data_time.get(device_id, 0)
            time_since_last = current_time - last_seen
            is_online = time_since_last < 300  # Consider offline if no data for 5 minutes
            
            status[device_id] = {
                "online": is_online,
                "last_seen": datetime.fromtimestamp(last_seen).isoformat(),
                "time_since_last_data": time_since_last
            }
        
        return status
    
    def send_pump_command(self, device_id: str, action: str):
        """Send pump control command to device"""
        command = {
            "device_id": device_id,
            "action": action,  # "pump_on" or "pump_off"
            "timestamp": datetime.now().isoformat()
        }
        
        topic = "agrisense/commands"
        self.mqtt_client.publish(topic, json.dumps(command))
        logger.info(f"Sent pump command '{action}' to {device_id}")
    
    def start(self):
        """Start the MQTT bridge service"""
        logger.info("Starting AgriSense MQTT Bridge...")
        
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            
            # Start MQTT loop in background
            self.mqtt_client.loop_start()
            
            logger.info("MQTT Bridge started successfully")
            logger.info(f"Listening for sensor data on MQTT broker {self.mqtt_broker}:{self.mqtt_port}")
            logger.info(f"Forwarding data to AgriSense backend at {self.backend_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MQTT bridge: {e}")
            return False
    
    def stop(self):
        """Stop the MQTT bridge service"""
        logger.info("Stopping MQTT Bridge...")
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

# Global bridge instance for API access
mqtt_bridge = AgriSenseMQTTBridge()

def start_mqtt_bridge():
    """Start the MQTT bridge as a background service"""
    if mqtt_bridge.start():
        logger.info("MQTT Bridge is running")
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            mqtt_bridge.stop()
    else:
        logger.error("Failed to start MQTT Bridge")

if __name__ == "__main__":
    # Run as standalone script
    start_mqtt_bridge()