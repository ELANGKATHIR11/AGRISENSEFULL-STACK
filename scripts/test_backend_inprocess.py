import os
import sys
from typing import Any

# Ensure repository root on path so 'agrisense_app' package resolves when running from any cwd
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from typing import Any, Dict, List, cast
from fastapi.testclient import TestClient  # type: ignore
from agrisense_app.backend.main import app

client = TestClient(app)

def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") in ("ok", "live")
    r2 = client.get("/ready")
    assert r2.status_code == 200
    ready = cast(Dict[str, Any], r2.json())
    # After TF install and model files present, these should be true
    assert isinstance(ready.get("water_model"), bool)
    assert isinstance(ready.get("fert_model"), bool)


def test_plants_and_recommend() -> None:
    r = client.get("/plants")
    assert r.status_code == 200
    items_raw = r.json().get("items", [])
    items: List[Dict[str, Any]] = list(cast(List[Dict[str, Any]], items_raw))
    assert isinstance(items, list) and len(items) > 0

    first_item: Dict[str, Any] = items[0]
    payload: Dict[str, Any] = {
        "plant": cast(str, first_item.get("value", "generic")),
        "soil_type": "loam",
        "area_m2": 25,
        "ph": 6.5,
        "moisture_pct": 30,
        "temperature_c": 27,
        "ec_dS_m": 1.0,
    }
    r2 = client.post("/recommend", json=payload)
    assert r2.status_code == 200, r2.text
    data = r2.json()
    for key in ("water_liters", "fert_n_g", "fert_p_g", "fert_k_g"):
        assert key in data


def test_crops_full_list() -> None:
    r = client.get("/crops")
    assert r.status_code == 200
    payload = cast(Dict[str, Any], r.json())
    items = cast(List[Dict[str, Any]], payload.get("items", []))
    assert isinstance(items, list)
    assert len(items) >= 40, f"Expected >= 40 crops, got {len(items)}"


if __name__ == "__main__":
    # Execute tests when run as a script
    test_health()
    test_plants_and_recommend()
    test_crops_full_list()
    print("Backend in-process smoke tests passed.")
