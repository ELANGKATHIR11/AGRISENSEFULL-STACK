import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Prefer ML disabled for fast smoke tests unless the env explicitly enables ML
os.environ.setdefault("AGRISENSE_DISABLE_ML", "1")

# Make imports resilient in different run contexts (CI, editor, local)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from agrisense_app.backend.main import app
except Exception as e:
    print("Failed to import app:", e)
    sys.exit(2)

client = TestClient(app)

SAMPLE_READING = {
    "zone_id": "Z1",
    "plant": "generic",
    "soil_type": "loam",
    "area_m2": 120,
    "ph": 6.5,
    "moisture_pct": 35.0,
    "temperature_c": 28.0,
    "ec_dS_m": 1.0,
}

print("Posting to /recommend with ML disabled...")
resp = client.post("/recommend", json=SAMPLE_READING)
print(f"Status: {resp.status_code}")
try:
    j = resp.json()
except Exception:
    print("Failed to parse JSON response:\n", resp.text)
    sys.exit(3)

if resp.status_code != 200:
    print("FAIL: non-200 response:\n", j)
    sys.exit(4)

# Support two shapes: either {"recommendation": {...}} or the recommendation object directly
if "recommendation" in j and isinstance(j["recommendation"], dict):
    rec = j["recommendation"]
elif isinstance(j, dict) and ("water_liters" in j or "tips" in j):
    rec = j
else:
    print("FAIL: response did not contain a recommendation object:\n", j)
    sys.exit(5)

if "water_liters" not in rec or "tips" not in rec:
    print("FAIL: recommendation missing required keys. Keys present:", list(rec.keys()))
    sys.exit(6)

print("PASS: /recommend returned recommendation with required keys")
print("water_liters:", rec.get("water_liters"))
print("tips:", rec.get("tips"))
sys.exit(0)
