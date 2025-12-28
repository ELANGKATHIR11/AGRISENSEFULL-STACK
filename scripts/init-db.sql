-- AgriSense Database Initialization Script
-- Creates tables, indexes, and initial data

-- Create sensor_readings table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    soil_moisture DECIMAL(5,2),
    ph_level DECIMAL(4,2),
    nitrogen INTEGER,
    phosphorus INTEGER,
    potassium INTEGER,
    rainfall DECIMAL(7,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_device_timestamp ON sensor_readings(device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_readings(timestamp DESC);

-- Create irrigation_logs table
CREATE TABLE IF NOT EXISTS irrigation_logs (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    water_amount DECIMAL(10,2) NOT NULL,
    recommendation_id INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create crop_recommendations table
CREATE TABLE IF NOT EXISTS crop_recommendations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nitrogen INTEGER,
    phosphorus INTEGER,
    potassium INTEGER,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    ph_level DECIMAL(4,2),
    rainfall DECIMAL(7,2),
    recommended_crop VARCHAR(100),
    confidence DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create disease_detections table
CREATE TABLE IF NOT EXISTS disease_detections (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    detected_disease VARCHAR(200),
    confidence DECIMAL(5,4),
    treatment_recommended TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create weed_detections table
CREATE TABLE IF NOT EXISTS weed_detections (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    weed_count INTEGER,
    weed_classes TEXT,
    treatment_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chatbot_interactions table
CREATE TABLE IF NOT EXISTS chatbot_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence DECIMAL(5,4),
    feedback VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table (optional for future auth)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Insert sample device for testing
INSERT INTO sensor_readings (device_id, temperature, humidity, soil_moisture, ph_level, nitrogen, phosphorus, potassium, rainfall)
VALUES ('DEMO_DEVICE_001', 25.5, 65.0, 45.0, 6.5, 40, 50, 60, 200.0)
ON CONFLICT DO NOTHING;

-- Create view for latest sensor readings
CREATE OR REPLACE VIEW latest_sensor_readings AS
SELECT DISTINCT ON (device_id) 
    device_id,
    timestamp,
    temperature,
    humidity,
    soil_moisture,
    ph_level,
    nitrogen,
    phosphorus,
    potassium,
    rainfall
FROM sensor_readings
ORDER BY device_id, timestamp DESC;

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agrisense;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agrisense;
