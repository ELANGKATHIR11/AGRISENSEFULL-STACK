import requests, json
from typing import Dict, Any

BASE = "http://127.0.0.1:8004"

print("/health:", requests.get(f"{BASE}/health").json())

sample: Dict[str, Any] = {
    "zone_id":"Z1","plant":"generic","soil_type":"loam","area_m2":100,
    "ph":6.5,"moisture_pct":35,"temperature_c":28,"ec_dS_m":1.0,
    "n_ppm":20,"p_ppm":10,"k_ppm":80
}

print("/recommend:")
print(json.dumps(requests.post(f"{BASE}/recommend", json=sample).json(), indent=2))

print("/ingest:", requests.post(f"{BASE}/ingest", json=sample).json())
print("/recent:", requests.get(f"{BASE}/recent", params={"zone_id":"Z1","limit":1}).json())
