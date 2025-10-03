/*
 * AgriSense Arduino Nano Temperature Sensor
 * Captures temperature data and sends via serial communication
 * Compatible with DS18B20 and DHT22 sensors
 * 
 * Hardware Connections:
 * DS18B20:
 *   - VCC to 5V
 *   - GND to GND  
 *   - Data to Digital Pin 2
 *   - 4.7kΩ resistor between VCC and Data
 * 
 * DHT22:
 *   - VCC to 5V
 *   - GND to GND
 *   - Data to Digital Pin 3
 *   - 10kΩ resistor between VCC and Data
 */

#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>
#include <ArduinoJson.h>

// Pin definitions
#define ONE_WIRE_BUS 2
#define DHT_PIN 3
#define DHT_TYPE DHT22

// Sensor setup
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature ds18b20(&oneWire);
DHT dht(DHT_PIN, DHT_TYPE);

// Configuration
const unsigned long READING_INTERVAL = 5000; // 5 seconds
const String DEVICE_ID = "ARDUINO_NANO_01";
unsigned long lastReading = 0;

// Sensor data structure
struct SensorData {
  float ds18b20_temp;
  float dht22_temp;
  float dht22_humidity;
  unsigned long timestamp;
  bool ds18b20_status;
  bool dht22_status;
};

void setup() {
  Serial.begin(115200);
  
  // Initialize sensors
  ds18b20.begin();
  dht.begin();
  
  // Wait for sensors to stabilize
  delay(2000);
  
  Serial.println("AgriSense Arduino Nano Temperature Sensor v1.0");
  Serial.println("Device ID: " + DEVICE_ID);
  Serial.println("Sensors initialized. Starting data collection...");
  
  // Send initial status
  sendStatus();
}

void loop() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastReading >= READING_INTERVAL) {
    SensorData data = readSensors();
    sendSensorData(data);
    lastReading = currentTime;
  }
  
  // Check for serial commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    handleCommand(command);
  }
  
  delay(100);
}

SensorData readSensors() {
  SensorData data;
  data.timestamp = millis();
  
  // Read DS18B20 temperature
  ds18b20.requestTemperatures();
  data.ds18b20_temp = ds18b20.getTempCByIndex(0);
  data.ds18b20_status = (data.ds18b20_temp != DEVICE_DISCONNECTED_C);
  
  // Read DHT22 temperature and humidity
  data.dht22_temp = dht.readTemperature();
  data.dht22_humidity = dht.readHumidity();
  data.dht22_status = (!isnan(data.dht22_temp) && !isnan(data.dht22_humidity));
  
  return data;
}

void sendSensorData(SensorData data) {
  // Create JSON object
  StaticJsonDocument<300> doc;
  
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = "arduino_nano";
  doc["timestamp"] = data.timestamp;
  
  // Temperature readings
  JsonObject temperatures = doc.createNestedObject("temperatures");
  if (data.ds18b20_status) {
    temperatures["ds18b20"] = data.ds18b20_temp;
  } else {
    temperatures["ds18b20"] = nullptr;
  }
  
  if (data.dht22_status) {
    temperatures["dht22"] = data.dht22_temp;
    doc["humidity"] = data.dht22_humidity;
  } else {
    temperatures["dht22"] = nullptr;
    doc["humidity"] = nullptr;
  }
  
  // Sensor status
  JsonObject status = doc.createNestedObject("sensor_status");
  status["ds18b20"] = data.ds18b20_status;
  status["dht22"] = data.dht22_status;
  
  // Calculate average temperature
  float avgTemp = 0;
  int validReadings = 0;
  
  if (data.ds18b20_status) {
    avgTemp += data.ds18b20_temp;
    validReadings++;
  }
  if (data.dht22_status) {
    avgTemp += data.dht22_temp;
    validReadings++;
  }
  
  if (validReadings > 0) {
    doc["avg_temperature"] = avgTemp / validReadings;
  } else {
    doc["avg_temperature"] = nullptr;
  }
  
  // Send JSON data
  Serial.print("DATA:");
  serializeJson(doc, Serial);
  Serial.println();
}

void sendStatus() {
  StaticJsonDocument<200> doc;
  
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = "arduino_nano";
  doc["status"] = "online";
  doc["firmware_version"] = "1.0";
  doc["uptime"] = millis();
  
  // Sensor availability
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["ds18b20"] = "available";
  sensors["dht22"] = "available";
  
  Serial.print("STATUS:");
  serializeJson(doc, Serial);
  Serial.println();
}

void handleCommand(String command) {
  command.toUpperCase();
  
  if (command == "STATUS") {
    sendStatus();
  } else if (command == "READ") {
    SensorData data = readSensors();
    sendSensorData(data);
  } else if (command == "RESET") {
    Serial.println("RESET:OK");
    // Reset device (software reset)
    asm volatile ("  jmp 0");
  } else if (command == "PING") {
    Serial.println("PONG");
  } else {
    Serial.println("ERROR:Unknown command");
  }
}