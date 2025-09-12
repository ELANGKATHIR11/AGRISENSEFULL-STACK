from pydantic import BaseModel

class SensorData(BaseModel):
    soil_moisture: float
    temperature_c: float
    humidity: float
    ph: float
    ec_dS_m: float
    tank_percent: float
