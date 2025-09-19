import io
import os
import tempfile
import json

import numpy as np
from PIL import Image

from agrisense_app.backend import disease_detection as dd


def make_dummy_joblib_model(path):
    # Create a very small sklearn-like object with predict and predict_proba
    class DummyModel:
        def __init__(self):
            self.classes_ = ["healthy", "diseased"]

        def predict(self, X):
            return ["healthy"]

        def predict_proba(self, X):
            # return equal probabilities
            return np.array([[0.6, 0.4]])

    try:
        from joblib import dump

        dump(DummyModel(), path)
        return True
    except Exception:
        return False


def test_joblib_inference_path(tmp_path):
    # Create a tiny RGB image
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b = buf.getvalue()

    # Write a dummy joblib model into backend dir
    backend_dir = os.path.dirname(dd.__file__)
    model_path = os.path.join(backend_dir, "disease_model.joblib")

    # Try to write a dummy joblib model into backend dir. If joblib isn't available
    # in this environment, fall back to injecting a dummy model directly into the
    # disease_detection module so we can exercise the inference path without
    # requiring the joblib package.
    ok = False
    try:
        if os.access(backend_dir, os.W_OK):
            ok = make_dummy_joblib_model(model_path)
            if ok and model_path not in dd.MODEL_FILES:
                dd.MODEL_FILES.insert(0, model_path)
        else:
            # write into tmp and add to search list
            model_path = str(tmp_path / "disease_model.joblib")
            ok = make_dummy_joblib_model(model_path)
            if ok:
                dd.MODEL_FILES.insert(0, model_path)
    except Exception:
        ok = False

    if not ok:
        # Fallback: inject dummy model directly
        class DummyModelLocal:
            def __init__(self):
                self.classes_ = ["healthy", "diseased"]

            def predict(self, X):
                return ["healthy"]

            def predict_proba(self, X):
                return np.array([[0.6, 0.4]])

        dd._model = DummyModelLocal()
        dd._model_type = "joblib"

    res = dd.analyze_image_bytes(b)
    assert isinstance(res, dict)
    assert res.get("ok") is True
    assert res.get("model") == "joblib"
    preds = res.get("predictions")
    assert isinstance(preds, list) and len(preds) >= 1
    # cleanup
    try:
        os.remove(model_path)
    except Exception:
        pass
