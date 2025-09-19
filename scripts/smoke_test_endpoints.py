import requests
import base64
import io
from PIL import Image

BASE = "http://127.0.0.1:8004"


def print_resp(r):
    print(r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)


if __name__ == "__main__":
    print("GET /health")
    r = requests.get(BASE + "/health")
    print_resp(r)

    print("\nPOST /disease/detect without payload")
    r = requests.post(BASE + "/disease/detect")
    print_resp(r)

    print("\nPOST /disease/detect with image (form upload)")
    # create small PNG
    img = Image.new("RGB", (100, 100), (120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    files = {"file": ("test.png", buf, "image/png")}
    r = requests.post(BASE + "/disease/detect", files=files)
    print_resp(r)

    print("\nPOST /suggest_crop sample payload")
    payload = {
        "zone_id": "Z1",
        "plant": "tomato",
        "soil_type": "loam",
        "area_m2": 100,
        "ph": 6.5,
        "moisture_pct": 34.0,
        "temperature_c": 28.0,
        "ec_dS_m": 1.0,
    }
    r = requests.post(BASE + "/suggest_crop", json=payload)
    print_resp(r)
