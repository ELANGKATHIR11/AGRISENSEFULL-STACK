try:
    from pymongo import MongoClient  # type: ignore
except Exception as e:
    raise ImportError("Missing dependency 'pymongo'. Install with: pip install pymongo") from e

MONGO_URI = 'mongodb://localhost:27017'
DB_NAME = 'agrisense'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

sensor_readings = db['sensor_readings']
recommendations = db['recommendations']

sensor_readings.create_index('timestamp')
recommendations.create_index('timestamp')
