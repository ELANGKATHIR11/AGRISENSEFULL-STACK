import os
import sys
from pathlib import Path
try:
    import pytest  # type: ignore[import-not-found]
except Exception:
    pytest = None
from fastapi.testclient import TestClient

# Default to ML disabled for fast tests
os.environ.setdefault("AGRISENSE_DISABLE_ML", "1")

# Ensure the package root is importable in editors and CI
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agrisense_app.backend.main import app

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


def test_recommend_returns_required_keys(monkeypatch):
    # Ensure ML is disabled for CI-speed
    monkeypatch.setenv("AGRISENSE_DISABLE_ML", "1")

    resp = client.post("/recommend", json=SAMPLE_READING)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code} {resp.text}"
    j = resp.json()
    # Top-level shape: {"reading": ..., "recommendation": {...}}
    # Allow both response shapes: wrapper {"recommendation": {...}} or direct recommendation dict
    if "recommendation" in j and isinstance(j["recommendation"], dict):
        rec = j["recommendation"]
    elif isinstance(j, dict) and ("water_liters" in j or "tips" in j):
        rec = j
    else:
        raise AssertionError(f"Response did not include a recommendation object: {j}")
    # Required minimal keys from contract
    assert "water_liters" in rec
    assert "tips" in rec
    # water_liters should be numeric
    assert isinstance(rec.get("water_liters"), (int, float))
    assert isinstance(rec.get("tips"), list)
