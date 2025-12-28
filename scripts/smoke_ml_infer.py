import requests
import json

# Sample payload
payload = {
    "moisture_pct": 30.0,
    "temperature_c": 25.0,
    "ec_dS_m": 1.5,
    "ph": 6.8,
    "soil_type": "loam",
    "crop": "rice",
    "area_m2": 100
}

# Send request
response = requests.post(
    "http://localhost:8004/recommend",
    json=payload
)

# Check response
if response.status_code == 200:
    result = response.json()
    assert "water_liters" in result, "Missing water_liters in response"
    assert "tips" in result, "Missing tips in response"
    print("Smoke test passed!")
else:
    print(f"Smoke test failed: {response.status_code}")
    print(response.text)
