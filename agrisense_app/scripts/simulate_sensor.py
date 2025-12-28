"""Simple script to post a random reading to the API"""
import random, requests

URL = "http://localhost:8000/ingest"

def one(zone="Z1"):
    body = {
        "zone_id": zone, "plant": "tomato", "soil_type": "loam",
        "area_m2": 120, "ph": round(random.uniform(5.8,7.2),1),
        "moisture_pct": round(random.uniform(15,60),1),
        "temperature_c": round(random.uniform(22,38),1),
        "ec_dS_m": round(random.uniform(0.4,2.0),2),
        "n_ppm": round(random.uniform(10,50),1),
        "p_ppm": round(random.uniform(5,25),1),
        "k_ppm": round(random.uniform(60,200),1)
    }
    r = requests.post(URL, json=body)
    print(r.json())

if __name__ == "__main__":
    one("Z1")