import os
import sys

# Ensure repository root on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from typing import Any, Dict, cast
import httpx
from fastapi.testclient import TestClient  # type: ignore
from agrisense_app.backend.main import app

client: TestClient = TestClient(app)

def test_edge_health_available_key() -> None:
    r: httpx.Response = client.get("/edge/health")
    assert r.status_code == 200
    data = cast(Dict[str, Any], r.json())
    assert "status" in data

def test_edge_capture_graceful_when_unavailable() -> None:
    r: httpx.Response = client.post("/edge/capture", json={"zone_id": "Z1"})
    # If the edge reader is available, capture should succeed with 200.
    # If not available, API responds with 503. Either is acceptable here.
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = cast(Dict[str, Any], r.json())
        assert "reading" in data and "recommendation" in data

if __name__ == "__main__":
    test_edge_health_available_key()
    test_edge_capture_graceful_when_unavailable()
    print("Edge endpoints tests passed.")
