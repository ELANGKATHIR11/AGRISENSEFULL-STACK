import time
from typing import Any, Dict, List, TypedDict, cast

import requests  # type: ignore

BASE = "http://127.0.0.1:8004"


def wait_ready(timeout: float = 5.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(f"{BASE}/health", timeout=2)
            if r.ok:
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise SystemExit("Backend did not start in time")


class PlantItem(TypedDict, total=False):
    value: str
    label: str


def smoke() -> None:
    wait_ready()
    r = requests.get(f"{BASE}/health")
    print("/health:", r.status_code, r.json())

    r = requests.get(f"{BASE}/plants")
    r.raise_for_status()
    plants_raw: Dict[str, Any] = cast(Dict[str, Any], r.json())
    items: List[PlantItem] = cast(List[PlantItem], plants_raw.get("items", []))
    print("/plants count:", len(items))

    payload: Dict[str, Any] = {
        "plant": "rice",
        "soil_type": "loam",
        "area_m2": 50,
        "ph": 6.4,
        "moisture_pct": 30,
        "temperature_c": 27,
        "ec_dS_m": 1.1,
    }
    r = requests.post(f"{BASE}/recommend", json=payload)
    r.raise_for_status()
    print("/recommend keys:", sorted(list(r.json().keys()))[:6], "...")


if __name__ == "__main__":
    smoke()
