import io
import base64
from PIL import Image
import numpy as np
import importlib
from typing import Any, cast

# This test runs purely in-process and injects a dummy model into the disease_detection
# module so we avoid heavy ML imports and still validate the inference plumbing and
# treatment_plan generation.


def make_dummy_image_bytes(size=(64, 64), color=(120, 120, 120)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


    # import the module and ensure our functions exist
    m = cast(Any, importlib.import_module("agrisense_app.backend.disease_detection"))
    assert hasattr(m, "analyze_image_bytes")
    assert hasattr(m, "analyze_image_bytes")

    # create a very small dummy model that supports predict_proba and classes_
    class DummyModel:
        def __init__(self):
            self.classes_ = np.array(["healthy", "late_blight", "powdery_mildew"])

        def predict_proba(self, X):
            # For deterministic behavior, return a simple softmax-like distribution
            # shape (1, 3)
            probs = np.array([[0.1, 0.8, 0.1]], dtype=float)
            return probs

    # inject dummy model into the module, set model type to joblib
    m._model = DummyModel()
    m._model_type = "joblib"

    img_bytes = make_dummy_image_bytes()
    res = m.analyze_image_bytes(img_bytes)

    assert isinstance(res, dict)
    assert res.get("ok") is True
    # joblib branch should return 'model': 'joblib'
    assert res.get("model") == "joblib"
    preds = res.get("predictions")
    assert isinstance(preds, list) and len(preds) > 0
    # treatment_plan should be present and correspond to predictions
    synth = res.get("treatment_plan")
    assert synth is not None
    assert isinstance(synth, list)
    # Each item should have severity and treatment list
    for item in synth:
        assert "severity" in item
        assert "treatment" in item
