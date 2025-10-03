# ESP32 Arduino Sensor Setup Guide

## Quick Fix for IntelliSense Errors

The IntelliSense errors you're seeing are now fixed with the configuration files I've created:

- ✅ **C/C++ IntelliSense Configuration**: `.vscode/c_cpp_properties.json`
- ✅ **Arduino Project Configuration**: `arduino.json`
- ✅ **PlatformIO Configuration**: `AGRISENSE_IoT/esp32_firmware/platformio.ini`

## Development Options

You now have **TWO ways** to develop your ESP32 firmware:

### Option 1: Arduino IDE (Traditional)
- Use: `AGRISENSE_IoT/esp32_firmware/agrisense_esp32.ino`
- Install libraries manually through Arduino IDE Library Manager
- Upload using Arduino IDE

### Option 2: PlatformIO in VS Code (Recommended)
- Use: `AGRISENSE_IoT/esp32_firmware/src/main.cpp`
- Libraries auto-managed via `platformio.ini`
- Build, upload, and monitor directly in VS Code

## Hardware Setup

### ESP32 Pin Connections:
```
DHT22 Temperature/Humidity:
  VCC -> 3.3V
  GND -> GND  
  DATA -> GPIO 2

Soil Moisture Sensor:
  VCC -> 3.3V
  GND -> GND
  AOUT -> GPIO 34

DS18B20 Soil Temperature:
  VCC -> 3.3V
  GND -> GND
  DATA -> GPIO 4 (with 4.7kΩ pullup resistor)

pH Sensor:
  VCC -> 3.3V
  GND -> GND
  AOUT -> GPIO 35

Light Sensor (LDR):
  One end -> 3.3V
  Other end -> GPIO 36 and 10kΩ resistor to GND

Water Pump Relay:
  VCC -> 5V
  GND -> GND
  IN -> GPIO 5
```

## Software Configuration

### 1. Update WiFi Credentials
In either `agrisense_esp32.ino` or `src/main.cpp`, update:
```cpp
const char* ssid = "YOUR_WIFI_NETWORK_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
```

### 2. Update MQTT Server IP
Find your VS Code machine's IP address:
```powershell
ipconfig
```
Then update:
```cpp
const char* mqtt_server = "192.168.1.100";  // Your actual IP
```

### 3. Using PlatformIO (Recommended)

**Install Required Libraries:**
The `platformio.ini` file automatically handles all dependencies:
- DHT sensor library
- OneWire library
- DallasTemperature library
- ArduinoJson library
- PubSubClient library

**Build and Upload:**
1. Open VS Code
2. Open the `AGRISENSE_IoT/esp32_firmware/` folder
3. Click on PlatformIO icon in sidebar
4. Click "Build" to compile
5. Connect your ESP32 via USB
6. Click "Upload" to flash firmware
7. Click "Monitor" to view serial output

### 4. Using Arduino IDE (Alternative)

**Install ESP32 Board:**
1. File → Preferences
2. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Tools → Board → Boards Manager
4. Search and install "esp32"

**Install Required Libraries:**
Go to Sketch → Include Library → Library Manager and install:
- DHT sensor library by Adafruit
- OneWire by Jim Studt  
- DallasTemperature by Miles Burton
- ArduinoJson by Benoit Blanchon
- PubSubClient by Nick O'Leary

**Upload Code:**
1. Open `agrisense_esp32.ino` in Arduino IDE
2. Select Board: "ESP32 Dev Module"
3. Select correct COM port
4. Click Upload

## Testing Your Setup

### 1. Serial Monitor Output
You should see:
```
Starting AgriSense ESP32 Sensor Node...
Connecting to WiFi: YOUR_NETWORK
WiFi connected successfully!
IP address: 192.168.1.XXX
AgriSense ESP32 Sensor Node Ready!
Sensor data sent successfully:
  Air Temp: 24.5°C
  Humidity: 65.2%
  Soil Moisture: 45.8%
  ...
```

### 2. MQTT Data Flow
Your ESP32 will send data to topics:
- `agrisense/sensors/data` - Main sensor readings
- `agrisense/devices/heartbeat` - Device status
- `agrisense/pump/status` - Pump status updates

### 3. AgriSense Backend Integration
The MQTT bridge service (`mqtt_sensor_bridge.py`) will:
- ✅ Receive ESP32 sensor data
- ✅ Forward to AgriSense backend APIs
- ✅ Enable real-time data in frontend

## Troubleshooting

### IntelliSense Errors (Fixed)
- ✅ "WiFi.h not found" - Fixed with c_cpp_properties.json
- ✅ ESP32 libraries missing - Fixed with proper include paths

### Common Issues:
1. **WiFi Connection Failed**: Check SSID/password, network availability
2. **MQTT Connection Failed**: Verify MQTT broker IP, ensure broker is running
3. **Sensor Reading NaN**: Check wiring, power supply, library compatibility
4. **Upload Failed**: Check USB cable, correct COM port, ESP32 board selection

### Hardware Debugging:
- Use multimeter to verify 3.3V/5V power supply
- Check sensor wiring with continuity tester
- Test individual sensors with simple Arduino sketches first

## Next Steps

1. **Test Individual Sensors**: Start with one sensor at a time
2. **Configure WiFi/MQTT**: Update network credentials
3. **Upload Firmware**: Use PlatformIO for best experience
4. **Monitor Serial Output**: Verify sensor readings
5. **Run MQTT Bridge**: Start the backend bridge service
6. **Frontend Integration**: Enable real-time data display

Your ESP32 sensor node is now ready for comprehensive agricultural monitoring! 🌱