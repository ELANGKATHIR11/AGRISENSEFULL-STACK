from typing import Dict, Any

from fastapi.testclient import TestClient

try:
    # When running from repo root with package
    from agrisense_app.backend.main import app
except Exception:
    # Fallback if executed from scripts folder directly
    import sys, os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from backend.main import app  # type: ignore


client = TestClient(app)


def pretty(obj: Any) -> str:
    try:
        import json

        return json.dumps(obj, indent=2)
    except Exception:
        return str(obj)


def main() -> None:
    print("/health =>", client.get("/health").json())

    plants = client.get("/plants").json()
    print("/plants => count", len(plants.get("items", [])))

    sample: Dict[str, Any] = {
        "zone_id": "Z1",
        "plant": "generic",
        "soil_type": "loam",
        "area_m2": 100,
        "ph": 6.5,
        "moisture_pct": 35,
        "temperature_c": 28,
        "ec_dS_m": 1.0,
        "n_ppm": 20,
        "p_ppm": 10,
        "k_ppm": 80,
    }

    rec = client.post("/recommend", json=sample).json()
    print("/recommend =>", pretty(rec))

    ing = client.post("/ingest", json=sample).json()
    print("/ingest =>", ing)

    recent = client.get("/recent", params={"zone_id": "Z1", "limit": 1}).json()
    print("/recent =>", pretty(recent))

    crop = client.post(
        "/suggest_crop",
        json={"soil_type": "loam", "ph": 6.8, "temperature": 25, "moisture": 60},
    ).json()
    print("/suggest_crop =>", pretty(crop))

    # IoT compatibility shims
    iot_recent = client.get(
        "/sensors/recent", params={"zone_id": "Z1", "limit": 1}
    ).json()
    print("/sensors/recent =>", pretty(iot_recent))
    iot_latest = client.get("/recommend/latest", params={"zone_id": "Z1"}).json()
    print("/recommend/latest =>", pretty(iot_latest))


if __name__ == "__main__":
    main()
