import io
from PIL import Image
import importlib
from fastapi.testclient import TestClient


def make_dummy_image_bytes(size=(64, 64), color=(120, 120, 120)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_disease_detect_endpoint_client():
    # Import the FastAPI app
    app_mod = importlib.import_module("agrisense_app.backend.main")
    app = getattr(app_mod, "app")

    # Import disease_detection module and inject dummy joblib model
    dd = importlib.import_module("agrisense_app.backend.disease_detection")

    class DummyModel:
        def __init__(self):
            self.classes_ = ["healthy", "late_blight", "powdery_mildew"]

        def predict_proba(self, X):
            import numpy as _np

            return _np.array([[0.1, 0.8, 0.1]])

    setattr(dd, "_model", DummyModel())
    setattr(dd, "_model_type", "joblib")

    client = TestClient(app)
    img_bytes = make_dummy_image_bytes()
    files = {"file": ("test.png", io.BytesIO(img_bytes), "image/png")}
    r = client.post("/disease/detect", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("model") == "joblib"
    assert isinstance(data.get("predictions"), list)
    assert isinstance(data.get("treatment_plan"), list)
