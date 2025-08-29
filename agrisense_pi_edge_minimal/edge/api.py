from fastapi import FastAPI, Query
from .util import load_config
from .reader import SensorReader
from .publisher import BackendClient, MqttCaptureTrigger

cfg = load_config()
reader = SensorReader(cfg)
backend = BackendClient(cfg.get("backend_base_url", "http://localhost:8000"))

app = FastAPI(title="AgriSense Edge API", version="0.1.0")

if cfg.get("use_mqtt", False):
    m = cfg.get("mqtt", {})
    MqttCaptureTrigger(m.get("broker","localhost"), int(m.get("port",1883)),
                       m.get("capture_topic_pattern","agrisense/+/capture_now"),
                       on_capture=lambda zone: reader.capture(zone or cfg.get("zone_id","Z1")))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/capture")
def capture(zone_id: str = Query(None)):
    zone = zone_id or cfg.get("zone_id", "Z1")
    reading = reader.capture(zone)
    payload = {
        "zone_id": reading["zone_id"],
        "plant": reading.get("plant","tomato"),
        "soil_type": reading.get("soil_type","loam"),
        "area_m2": reading.get("area_m2",120),
        "ph": reading.get("ph", 6.5),
        "moisture_pct": reading.get("moisture_pct", 35.0),
        "temperature_c": reading.get("temperature_c", 28.0),
        "ec_dS_m": reading.get("ec_dS_m", 1.0),
        "n_ppm": reading.get("n_ppm"),
        "p_ppm": reading.get("p_ppm"),
        "k_ppm": reading.get("k_ppm"),
    }
    try:
        backend.ingest(payload)
    except Exception:
        pass
    rec = backend.recommend(payload)
    return {"reading": reading, "recommendation": rec}
