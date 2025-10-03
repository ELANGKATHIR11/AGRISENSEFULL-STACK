# Arduino Nano Temperature Sensor Wiring Guide
## For AgriSense Smart Agriculture Platform

### Hardware Requirements

**Core Components:**
- Arduino Nano (or compatible microcontroller)
- USB Mini-B cable for programming and power
- Breadboard or perfboard for connections
- Jumper wires (male-to-male, male-to-female)

**Temperature Sensors (Choose one or both):**
- **DS18B20** Digital Temperature Sensor (waterproof version recommended)
- **DHT22** Temperature and Humidity Sensor

**Required Resistors:**
- 4.7kΩ resistor (for DS18B20 pull-up)
- 10kΩ resistor (for DHT22 pull-up, optional but recommended)

### Wiring Diagrams

#### Option 1: DS18B20 Only (Simple Temperature)

```
Arduino Nano          DS18B20 Sensor
+5V (VCC)     ───────── VCC (Red wire)
GND           ───────── GND (Black wire)  
Pin D2        ───────── Data (Yellow wire)

Pull-up Resistor:
4.7kΩ between VCC and Data lines
```

**DS18B20 Pin Configuration:**
- Pin 1 (GND): Black wire → Arduino GND
- Pin 2 (Data): Yellow wire → Arduino Pin D2
- Pin 3 (VCC): Red wire → Arduino +5V
- 4.7kΩ resistor between Pin 2 and Pin 3

#### Option 2: DHT22 Only (Temperature + Humidity)

```
Arduino Nano          DHT22 Sensor
+5V (VCC)     ───────── Pin 1 (VCC)
Pin D3        ───────── Pin 2 (Data)
Not Connected ───────── Pin 3 (Not used)
GND           ───────── Pin 4 (GND)

Pull-up Resistor:
10kΩ between VCC and Data lines (optional)
```

**DHT22 Pin Configuration:**
- Pin 1: VCC → Arduino +5V
- Pin 2: Data → Arduino Pin D3  
- Pin 3: Not connected
- Pin 4: GND → Arduino GND

#### Option 3: Both Sensors (Dual Temperature Monitoring)

```
Arduino Nano          DS18B20          DHT22
+5V (VCC)     ───────── VCC      ───────── Pin 1 (VCC)
GND           ───────── GND      ───────── Pin 4 (GND)
Pin D2        ───────── Data     
Pin D3        ─────────────────── ──────── Pin 2 (Data)

Resistors:
- 4.7kΩ between DS18B20 VCC and Data
- 10kΩ between DHT22 VCC and Data (optional)
```

### Step-by-Step Assembly

#### Step 1: Prepare the Breadboard
1. Insert Arduino Nano into breadboard (optional, can wire directly)
2. Connect power rails: red (+5V) and black (GND)

#### Step 2: DS18B20 Connection
1. **Power**: Connect DS18B20 VCC (red) to Arduino +5V
2. **Ground**: Connect DS18B20 GND (black) to Arduino GND
3. **Data**: Connect DS18B20 Data (yellow) to Arduino Pin D2
4. **Pull-up**: Connect 4.7kΩ resistor between VCC and Data lines

#### Step 3: DHT22 Connection (if using)
1. **Power**: Connect DHT22 Pin 1 to Arduino +5V
2. **Data**: Connect DHT22 Pin 2 to Arduino Pin D3
3. **Ground**: Connect DHT22 Pin 4 to Arduino GND
4. **Pull-up**: Connect 10kΩ resistor between Pin 1 and Pin 2 (optional)

#### Step 4: Verify Connections
- Double-check all power connections (VCC to +5V, GND to GND)
- Ensure data pins are connected to correct Arduino pins (D2, D3)
- Verify pull-up resistors are properly placed

### Sensor Placement Tips

**For Greenhouse/Indoor Use:**
- Mount sensors away from direct heat sources
- Ensure good air circulation around DHT22
- Keep DS18B20 away from direct sunlight

**For Outdoor/Soil Use:**
- Use waterproof DS18B20 for soil temperature monitoring
- Protect DHT22 in weatherproof enclosure
- Use cable glands for wire protection

**Mounting Options:**
- Zip ties for temporary installations
- Sensor mounts for permanent setups
- Protective housings for harsh environments

### Power Considerations

**USB Power (Development):**
- Connect Arduino via USB cable to computer
- Suitable for testing and development
- Power consumption: ~50mA total

**External Power (Production):**
- Use 7-12V DC adapter connected to Arduino VIN pin
- Or 5V regulated supply to 5V pin
- Ensure adequate current capacity (100mA minimum)

### Troubleshooting

**Common Issues:**

1. **No sensor readings:**
   - Check wiring connections
   - Verify power supply (5V, GND)
   - Ensure pull-up resistors are connected

2. **Inconsistent readings:**
   - Check for loose connections
   - Verify proper pull-up resistor values
   - Move sensors away from interference sources

3. **Communication errors:**
   - Confirm correct pin assignments in code
   - Check for damaged sensors
   - Verify baud rate (115200) in serial monitor

4. **DHT22 specific issues:**
   - Readings may take 2-3 seconds to stabilize
   - Sensor needs 2-second delay between readings
   - Check for condensation inside sensor

5. **DS18B20 specific issues:**
   - Multiple sensors need unique addresses
   - Check for proper 4.7kΩ pull-up resistor
   - Verify one-wire bus integrity

### Safety Notes

- Always power off Arduino before making wiring changes
- Use appropriate wire gauges for connections
- Avoid short circuits between power and ground
- Handle sensors gently to prevent damage
- Keep connections dry in outdoor installations

### Next Steps

After completing the wiring:

1. **Upload Firmware**: Flash the AgriSense Arduino sketch
2. **Test Sensors**: Open Arduino Serial Monitor to verify readings
3. **Install Bridge**: Set up Python serial bridge on your computer
4. **Configure Port**: Update COM port in bridge script
5. **Start Monitoring**: Run bridge to send data to AgriSense backend

### Additional Resources

- Arduino Nano pinout diagram
- DS18B20 datasheet and libraries
- DHT22 sensor specifications
- AgriSense backend API documentation