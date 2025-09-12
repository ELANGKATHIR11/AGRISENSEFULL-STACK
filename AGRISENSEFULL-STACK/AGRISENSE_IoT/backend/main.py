from fastapi import FastAPI
from datetime import datetime
from models import SensorData
from database import sensor_readings, recommendations
from engine import predict_irrigation

app = FastAPI(title='AGRISENSE IoT Backend')

@app.post('/edge/ingest')
async def ingest(data: SensorData):
    record = data.dict()
    record['timestamp'] = datetime.utcnow()
    sensor_readings.insert_one(record)

    features = [data.soil_moisture, data.temperature_c, data.ec_dS_m, data.ph]
    irrigation_liters = predict_irrigation(features)

    irrigate = data.soil_moisture < 35 and data.tank_percent > 20
    water_source = 'tank' if data.tank_percent > 20 else 'groundwater'

    reco = {
        'timestamp': datetime.utcnow(),
        'irrigate': irrigate,
        'recommended_liters': irrigation_liters,
        'soil_moisture': data.soil_moisture,
        'ph': data.ph,
        'ec_dS_m': data.ec_dS_m,
        'temperature_c': data.temperature_c,
        'humidity': data.humidity,
        'tank_percent': data.tank_percent,
        'water_source': water_source,
        'notes': 'Soil dry, irrigate now' if irrigate else 'Skip irrigation today'
    }
    recommendations.insert_one(reco)
    return {'status': 'ok', 'recommendation': reco}

@app.get('/recommend/latest')
async def latest_reco():
    rec = recommendations.find_one(sort=[('timestamp', -1)])
    if rec:
        rec['_id'] = str(rec['_id'])
    return rec

@app.get('/sensors/recent')
async def recent_sensors(limit: int = 10):
    docs = sensor_readings.find().sort('timestamp', -1).limit(limit)
    readings = []
    for d in docs:
        d['_id'] = str(d['_id'])
        readings.append(d)
    return readings
