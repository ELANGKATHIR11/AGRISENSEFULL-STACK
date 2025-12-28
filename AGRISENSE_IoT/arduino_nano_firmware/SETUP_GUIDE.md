# Arduino Nano AgriSense Integration Setup Guide

## Overview
This guide helps you integrate Arduino Nano with temperature sensors into your AgriSense smart agriculture platform for real-time wired sensor monitoring.

## Quick Start Checklist

### Hardware Setup
- [ ] Arduino Nano board
- [ ] DS18B20 temperature sensor (waterproof recommended)
- [ ] DHT22 temperature/humidity sensor (optional)
- [ ] 4.7kΩ resistor for DS18B20
- [ ] 10kΩ resistor for DHT22 (optional)
- [ ] USB cable for programming and power
- [ ] Breadboard and jumper wires

### Software Setup
- [ ] Arduino IDE installed
- [ ] Required libraries installed
- [ ] Python environment with required packages
- [ ] AgriSense backend running

## Step 1: Arduino IDE Setup

### Install Arduino IDE
1. Download from [Arduino.cc](https://www.arduino.cc/en/software)
2. Install and open Arduino IDE
3. Select **Tools > Board > Arduino Nano**
4. Select correct **Port** (usually COM3, COM4, etc. on Windows)

### Install Required Libraries
Open **Tools > Manage Libraries** and install:

```
1. OneWire (by Jim Studt, Tom Pollard)
2. DallasTemperature (by Miles Burton)
3. DHT sensor library (by Adafruit)
4. ArduinoJson (by Benoit Blanchon)
```

## Step 2: Hardware Assembly

### Basic DS18B20 Setup (Recommended)
```
Arduino Nano    DS18B20 Sensor
+5V       ──────── VCC (Red)
GND       ──────── GND (Black)
Pin D2    ──────── Data (Yellow)

Connect 4.7kΩ resistor between VCC and Data
```

### Optional DHT22 Addition
```
Arduino Nano    DHT22 Sensor
+5V       ──────── Pin 1 (VCC)
Pin D3    ──────── Pin 2 (Data)
GND       ──────── Pin 4 (GND)

Connect 10kΩ resistor between Pin 1 and Pin 2
```

## Step 3: Upload Firmware

1. **Open Arduino IDE**
2. **Load the sketch**: Copy the contents of `agrisense_nano_temp_sensor.ino`
3. **Connect Arduino**: Plug USB cable into computer
4. **Select Board**: Tools > Board > Arduino Nano
5. **Select Port**: Tools > Port > (your Arduino port)
6. **Upload**: Click Upload button (→)

### Verify Upload
1. Open **Tools > Serial Monitor**
2. Set baud rate to **115200**
3. You should see:
   ```
   AgriSense Arduino Nano Temperature Sensor v1.0
   Device ID: ARDUINO_NANO_01
   Sensors initialized. Starting data collection...
   ```

## Step 4: Test Sensors

### Check Sensor Output
In Serial Monitor, you should see JSON data every 5 seconds:
```json
DATA:{"device_id":"ARDUINO_NANO_01","device_type":"arduino_nano","timestamp":12345,"temperatures":{"ds18b20":25.4,"dht22":24.8},"humidity":65.2,"sensor_status":{"ds18b20":true,"dht22":true},"avg_temperature":25.1}
```

### Test Commands
Type these commands in Serial Monitor:
- `STATUS` - Get device status
- `READ` - Force immediate reading
- `PING` - Test communication (should respond "PONG")

## Step 5: Python Bridge Setup

### Install Python Dependencies
```bash
cd AGRISENSE_IoT/arduino_nano_firmware
pip install -r requirements.txt
```

### Configure Serial Port
Edit `arduino_bridge.py`:
```python
# Find your Arduino port
ARDUINO_PORT = "COM3"  # Change to your port (Windows)
# ARDUINO_PORT = "/dev/ttyUSB0"  # Linux
# ARDUINO_PORT = "/dev/cu.usbserial-xxx"  # macOS
```

### Find Your Arduino Port
**Windows:**
1. Open Device Manager
2. Look under "Ports (COM & LPT)"
3. Find "Arduino Nano" or "USB Serial Device"
4. Note the COM port number (e.g., COM3, COM4)

**Linux:**
```bash
ls /dev/ttyUSB*
# or
ls /dev/ttyACM*
```

**macOS:**
```bash
ls /dev/cu.usbserial*
```

## Step 6: Start the Integration

### 1. Start AgriSense Backend
```bash
cd AGRISENSEFULL-STACK
.venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app --port 8004
```

### 2. Start Arduino Bridge
```bash
cd AGRISENSE_IoT/arduino_nano_firmware
python arduino_bridge.py
```

### 3. Verify Data Flow
You should see in the bridge console:
```
2025-09-16 10:30:15 - INFO - Starting Arduino Bridge...
2025-09-16 10:30:16 - INFO - Successfully connected to Arduino on COM3
2025-09-16 10:30:21 - INFO - Received sensor data: {'device_id': 'ARDUINO_NANO_01', ...}
2025-09-16 10:30:21 - INFO - Successfully sent data to backend
```

### 4. Check Dashboard
1. Open AgriSense frontend: `http://localhost:8080`
2. Go to Dashboard
3. Look for "Arduino Nano Sensors" section
4. You should see live temperature data

## Troubleshooting

### Arduino Issues

**Problem**: Arduino not detected
- Check USB cable connection
- Try different USB port
- Install Arduino drivers if needed

**Problem**: Upload fails
- Verify correct board selection (Arduino Nano)
- Check if correct port is selected
- Press reset button before uploading

**Problem**: No sensor data
- Check wiring connections
- Verify pull-up resistors are connected
- Test with simple sensor examples

### Python Bridge Issues

**Problem**: "Port not found" error
- Update `ARDUINO_PORT` in `arduino_bridge.py`
- Check Arduino is connected and recognized
- Close Arduino IDE Serial Monitor before running bridge

**Problem**: "Backend connection failed"
- Ensure AgriSense backend is running on port 8004
- Check `BACKEND_URL` in bridge script
- Verify network connectivity

**Problem**: Permission denied (Linux/macOS)
```bash
sudo usermod -a -G dialout $USER  # Linux
# Then logout and login again
```

### Data Flow Issues

**Problem**: Data not appearing in dashboard
- Check backend logs for API errors
- Verify Arduino endpoint is working: `http://localhost:8004/arduino/status`
- Ensure frontend is refreshing data

**Problem**: Inconsistent readings
- Check sensor connections
- Verify power supply stability
- Move sensors away from heat sources

## Advanced Configuration

### Multiple Arduino Devices
To use multiple Arduino Nanos:

1. **Change Device ID** in each Arduino:
   ```cpp
   const String DEVICE_ID = "ARDUINO_NANO_02";  // Unique ID
   ```

2. **Run separate bridge scripts** with different ports:
   ```python
   ARDUINO_PORT = "COM4"  # Different port for each Arduino
   ```

### Sensor Placement Tips
- **Indoor**: Mount away from heat sources, ensure air circulation
- **Outdoor**: Use waterproof sensors, protect connections
- **Soil**: Use waterproof DS18B20, bury at consistent depth

### Production Deployment
- Use external power supply instead of USB
- Implement error handling and automatic restart
- Set up bridge as system service
- Use appropriate enclosures for electronics

## Integration Points

### AgriSense Backend
- Arduino data goes to `/arduino/ingest` endpoint
- Status available at `/arduino/status` endpoint
- Data stored in same database as ESP32 sensors

### Dashboard Display
- Real-time Arduino temperature data
- Device status and connection monitoring
- Historical data visualization
- Setup instructions and troubleshooting

### Data Format
Arduino sends structured JSON data:
```json
{
  "device_id": "ARDUINO_NANO_01",
  "temperatures": {"ds18b20": 25.4, "dht22": 24.8},
  "humidity": 65.2,
  "avg_temperature": 25.1,
  "sensor_status": {"ds18b20": true, "dht22": true}
}
```

## Support

For technical support:
1. Check this setup guide first
2. Review troubleshooting section
3. Verify all connections and configurations
4. Check AgriSense backend logs
5. Test individual components separately

The Arduino Nano integration provides reliable wired sensor monitoring to complement your ESP32 wireless sensors, giving you comprehensive environmental monitoring for your AgriSense smart agriculture platform.