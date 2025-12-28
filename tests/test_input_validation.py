import pytest
from fastapi.testclient import TestClient
from agrisense_app.backend.main import app

client = TestClient(app)

@pytest.mark.parametrize("payload, expected_status", [
    ({"moisture_pct": 120, "temperature_c": 25, "ec_dS_m": 1.5, "ph": 6.8, "soil_type": "loam", "crop": "rice", "area_m2": 100}, 422),
    ({"moisture_pct": 30, "temperature_c": 100, "ec_dS_m": 1.5, "ph": 6.8, "soil_type": "loam", "crop": "rice", "area_m2": 100}, 422),
    ({"moisture_pct": 30, "temperature_c": 25, "ec_dS_m": 15, "ph": 6.8, "soil_type": "loam", "crop": "rice", "area_m2": 100}, 422),
    ({"moisture_pct": 30, "temperature_c": 25, "ec_dS_m": 1.5, "ph": 10, "soil_type": "loam", "crop": "rice", "area_m2": 100}, 422),
    ({"moisture_pct": 30, "temperature_c": 25, "ec_dS_m": 1.5, "ph": 6.8, "soil_type": "loam", "crop": "rice", "area_m2": 0}, 422),
    ({"moisture_pct": 30, "temperature_c": 25, "ec_dS_m": 1.5, "ph": 6.8, "soil_type": "loam", "crop": "rice", "area_m2": 100}, 200)
])
def test_input_validation(payload, expected_status):
    response = client.post("/recommend", json=payload)
    assert response.status_code == expected_status
