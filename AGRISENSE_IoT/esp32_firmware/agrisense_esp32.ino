/*
 * AgriSense ESP32 Comprehensive Sensor Node
 * Real-time agricultural monitoring with multiple sensors
 * 
 * Sensors supported:
 * - DHT22: Temperature & Humidity
 * - Soil Moisture: Capacitive sensor
 * - pH Sensor: Analog pH probe
 * - Light Sensor: LDR/Photoresistor
 * - DS18B20: Soil Temperature
 * 
 * Data sent via MQTT to AgriSense backend
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// WiFi Configuration - UPDATE THESE VALUES
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Configuration - UPDATE WITH YOUR VS CODE MACHINE IP
const char* mqtt_server = "192.168.1.100";  // Your VS Code machine IP
const int mqtt_port = 1883;
const char* mqtt_topic_sensors = "agrisense/sensors/data";
const char* mqtt_topic_commands = "agrisense/commands";

// Sensor Pin Definitions for ESP32
#define DHT_PIN 2              // DHT22 Temperature & Humidity
#define DHT_TYPE DHT22
#define SOIL_MOISTURE_PIN 34   // Analog pin for soil moisture sensor
#define SOIL_TEMP_PIN 4        // DS18B20 soil temperature sensor
#define PH_SENSOR_PIN 35       // Analog pin for pH sensor
#define LIGHT_SENSOR_PIN 36    // Analog pin for light sensor (LDR)
#define PUMP_RELAY_PIN 5       // Relay pin for water pump control

// Initialize sensors
DHT dht(DHT_PIN, DHT_TYPE);
OneWire oneWire(SOIL_TEMP_PIN);
DallasTemperature soilTempSensor(&oneWire);

WiFiClient espClient;
PubSubClient client(espClient);

// Sensor data structure
struct SensorData {
  float air_temperature;
  float humidity;
  float soil_moisture_percentage;
  float soil_temperature;
  float ph_level;
  float light_intensity_percentage;
  String location;
  String timestamp;
  bool pump_status;
};

// Timing variables
unsigned long lastSensorReading = 0;
const unsigned long sensorInterval = 30000; // Send data every 30 seconds
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 300000; // Heartbeat every 5 minutes

void setup() {
  Serial.begin(115200);
  Serial.println("Starting AgriSense ESP32 Sensor Node...");
  
  // Initialize pins
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  digitalWrite(PUMP_RELAY_PIN, LOW); // Pump off initially
  
  // Initialize sensors
  dht.begin();
  soilTempSensor.begin();
  
  // Connect to WiFi
  setup_wifi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqtt_callback);
  
  Serial.println("AgriSense ESP32 Sensor Node Ready!");
  Serial.println("Sensors initialized:");
  Serial.println("- DHT22 (Air Temp & Humidity)");
  Serial.println("- Soil Moisture Sensor");
  Serial.println("- DS18B20 (Soil Temperature)");
  Serial.println("- pH Sensor");
  Serial.println("- Light Sensor (LDR)");
  Serial.println("- Pump Relay Control");
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected successfully!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  // Handle incoming MQTT commands from AgriSense backend
  Serial.print("Message received [");
  Serial.print(topic);
  Serial.print("]: ");
  
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Parse command JSON
  DynamicJsonDocument command(1024);
  deserializeJson(command, message);
  
  // Handle pump control commands
  if (command["action"] == "pump_on") {
    digitalWrite(PUMP_RELAY_PIN, HIGH);
    Serial.println("Pump turned ON");
    send_pump_status(true);
  } else if (command["action"] == "pump_off") {
    digitalWrite(PUMP_RELAY_PIN, LOW);
    Serial.println("Pump turned OFF");
    send_pump_status(false);
  }
}

void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "AgriSense-ESP32-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Subscribe to command topic
      client.subscribe(mqtt_topic_commands);
      Serial.println("Subscribed to commands topic");
      
      // Send connection status
      send_heartbeat();
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

SensorData read_all_sensors() {
  SensorData data;
  
  // Read DHT22 (Air Temperature & Humidity)
  data.air_temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Read soil moisture (convert to percentage)
  int soil_raw = analogRead(SOIL_MOISTURE_PIN);
  data.soil_moisture_percentage = map(soil_raw, 0, 4095, 100, 0); // Invert: wet=100%, dry=0%
  
  // Read soil temperature
  soilTempSensor.requestTemperatures();
  data.soil_temperature = soilTempSensor.getTempCByIndex(0);
  
  // Read pH level (convert analog reading to pH scale)
  int ph_raw = analogRead(PH_SENSOR_PIN);
  data.ph_level = map(ph_raw, 0, 4095, 0, 14) / 10.0; // Simple linear mapping to pH 0-14
  
  // Read light intensity (convert to percentage)
  int light_raw = analogRead(LIGHT_SENSOR_PIN);
  data.light_intensity_percentage = map(light_raw, 0, 4095, 0, 100);
  
  // Set metadata
  data.location = "Field_Zone_1"; // Configure based on your setup
  data.timestamp = String(millis());
  data.pump_status = digitalRead(PUMP_RELAY_PIN);
  
  return data;
}

void send_sensor_data() {
  SensorData data = read_all_sensors();
  
  // Validate sensor readings
  if (isnan(data.air_temperature) || isnan(data.humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["device_id"] = "ESP32_AgriSense_001";
  doc["location"] = data.location;
  doc["timestamp"] = WiFi.getTime();
  doc["uptime_ms"] = millis();
  
  // Sensor readings
  JsonObject sensors = doc.createNestedObject("sensors");
  sensors["air_temperature"] = data.air_temperature;
  sensors["humidity"] = data.humidity;
  sensors["soil_moisture_percentage"] = data.soil_moisture_percentage;
  sensors["soil_temperature"] = data.soil_temperature;
  sensors["ph_level"] = data.ph_level;
  sensors["light_intensity_percentage"] = data.light_intensity_percentage;
  
  // Device status
  JsonObject status = doc.createNestedObject("status");
  status["pump_active"] = data.pump_status;
  status["wifi_rssi"] = WiFi.RSSI();
  status["free_heap"] = ESP.getFreeHeap();
  
  // Serialize and send
  String jsonString;
  serializeJson(doc, jsonString);
  
  if (client.publish(mqtt_topic_sensors, jsonString.c_str())) {
    Serial.println("Sensor data sent successfully:");
    Serial.printf("  Air Temp: %.1f°C\n", data.air_temperature);
    Serial.printf("  Humidity: %.1f%%\n", data.humidity);
    Serial.printf("  Soil Moisture: %.1f%%\n", data.soil_moisture_percentage);
    Serial.printf("  Soil Temp: %.1f°C\n", data.soil_temperature);
    Serial.printf("  pH Level: %.1f\n", data.ph_level);
    Serial.printf("  Light: %.1f%%\n", data.light_intensity_percentage);
    Serial.printf("  Pump: %s\n", data.pump_status ? "ON" : "OFF");
  } else {
    Serial.println("Failed to send sensor data!");
  }
}

void send_pump_status(bool status) {
  DynamicJsonDocument doc(256);
  doc["device_id"] = "ESP32_AgriSense_001";
  doc["action"] = "pump_status_update";
  doc["pump_active"] = status;
  doc["timestamp"] = WiFi.getTime();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish("agrisense/pump/status", jsonString.c_str());
}

void send_heartbeat() {
  DynamicJsonDocument doc(512);
  doc["device_id"] = "ESP32_AgriSense_001";
  doc["action"] = "heartbeat";
  doc["timestamp"] = WiFi.getTime();
  doc["uptime_ms"] = millis();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["sensor_count"] = 6;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish("agrisense/devices/heartbeat", jsonString.c_str());
  Serial.println("Heartbeat sent");
}

void loop() {
  // Ensure MQTT connection
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();
  
  unsigned long currentMillis = millis();
  
  // Send sensor data every 30 seconds
  if (currentMillis - lastSensorReading >= sensorInterval) {
    send_sensor_data();
    lastSensorReading = currentMillis;
  }
  
  // Send heartbeat every 5 minutes
  if (currentMillis - lastHeartbeat >= heartbeatInterval) {
    send_heartbeat();
    lastHeartbeat = currentMillis;
  }
  
  // Small delay to prevent watchdog timer issues
  delay(100);
}

/*
 * HARDWARE SETUP GUIDE:
 * 
 * ESP32 Pin Connections:
 * - DHT22: VCC -> 3.3V, GND -> GND, DATA -> GPIO 2
 * - Soil Moisture: VCC -> 3.3V, GND -> GND, AOUT -> GPIO 34
 * - DS18B20: VCC -> 3.3V, GND -> GND, DATA -> GPIO 4 (with 4.7k pullup)
 * - pH Sensor: VCC -> 3.3V, GND -> GND, AOUT -> GPIO 35
 * - Light Sensor (LDR): One end -> 3.3V, Other end -> GPIO 36 and 10k resistor to GND
 * - Pump Relay: VCC -> 5V, GND -> GND, IN -> GPIO 5
 * 
 * REQUIRED LIBRARIES (Install via Arduino IDE Library Manager):
 * - DHT sensor library by Adafruit
 * - OneWire by Jim Studt
 * - DallasTemperature by Miles Burton
 * - ArduinoJson by Benoit Blanchon
 * - PubSubClient by Nick O'Leary
 * 
 * CONFIGURATION STEPS:
 * 1. Update WiFi credentials (ssid, password)
 * 2. Update MQTT server IP (your VS Code machine IP)
 * 3. Upload to ESP32
 * 4. Open Serial Monitor to see sensor readings
 */
