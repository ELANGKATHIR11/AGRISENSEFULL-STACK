class SensorReader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
    def capture(self, zone_id: str, base=None):
        # Dummy placeholder for sensor reads
        reading = base.copy() if base else {}
        reading.update({
            "zone_id": zone_id,
            "plant": "tomato",
            "soil_type": "loam",
            "area_m2": 120,
            "ph": 6.5,
            "moisture_pct": 30.0,
            "temperature_c": 28.0,
            "ec_dS_m": 1.0,
        })
        return reading
