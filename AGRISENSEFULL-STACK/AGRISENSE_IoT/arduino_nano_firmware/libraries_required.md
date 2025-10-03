# Arduino Nano Libraries Required

To compile and run the AgriSense Arduino Nano temperature sensor firmware, you need to install the following libraries in the Arduino IDE:

## Required Libraries

1. **OneWire** (by Jim Studt, Tom Pollard, Robin James, etc.)
   - For DS18B20 temperature sensor communication
   - Install via Arduino IDE Library Manager

2. **DallasTemperature** (by Miles Burton, etc.)
   - For simplified DS18B20 sensor control
   - Install via Arduino IDE Library Manager

3. **DHT sensor library** (by Adafruit)
   - For DHT22 temperature and humidity sensor
   - Install via Arduino IDE Library Manager

4. **ArduinoJson** (by Benoit Blanchon)
   - For JSON data formatting and serial communication
   - Install via Arduino IDE Library Manager

## Installation Steps

1. Open Arduino IDE
2. Go to **Tools > Manage Libraries**
3. Search for each library by name and click **Install**
4. Select the latest stable version for each library

## Library Versions (Tested)

- OneWire: 2.3.7 or later
- DallasTemperature: 3.9.0 or later  
- DHT sensor library: 1.4.4 or later
- ArduinoJson: 6.21.3 or later

## Alternative Installation

You can also install libraries via the Arduino CLI:

```bash
arduino-cli lib install "OneWire"
arduino-cli lib install "DallasTemperature" 
arduino-cli lib install "DHT sensor library"
arduino-cli lib install "ArduinoJson"
```

## Hardware Requirements

- Arduino Nano (or compatible)
- DS18B20 temperature sensor (optional)
- DHT22 temperature/humidity sensor (optional)
- 4.7kΩ resistor (for DS18B20)
- 10kΩ resistor (for DHT22)
- Breadboard and jumper wires