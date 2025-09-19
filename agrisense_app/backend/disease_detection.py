import os
import io
import json
from typing import Dict, Any, Optional, List

_label_cache: Optional[List[str]] = None

# Minimal scaffold for disease detection: lazy-load model artifacts when available.
# If no model is present, provide a deterministic stub response.

HERE = os.path.dirname(__file__)

MODEL_FILES = [
    os.path.join(HERE, "disease_model_enhanced.joblib"),
    os.path.join(HERE, "disease_model.joblib"),
    os.path.join(HERE, "disease_tf.keras"),
]

_model = None
_model_type = None


def _load_model_if_available() -> None:
    global _model, _model_type
    if _model is not None:
        return
    # Prefer ordering from model_meta.json when available
    candidates = []
    meta_path = os.path.join(HERE, "model_meta.json")
    try:
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                pref = meta.get("preferred_order", [])
                for name in pref:
                    candidates.append(os.path.join(HERE, name))
    except Exception:
        # ignore and fall back to default list
        pass

    # extend with default MODEL_FILES to ensure we don't miss anything
    for p in MODEL_FILES:
        if p not in candidates:
            candidates.append(p)

    # Try to load models following the candidates list
    for p in candidates:
        if not os.path.exists(p):
            continue
        try:
            if p.endswith(".joblib"):
                try:
                    from joblib import load

                    _model = load(p)
                    _model_type = "joblib"
                    return
                except Exception:
                    continue
            if p.endswith(".keras"):
                try:
                    import tensorflow as tf  # type: ignore

                    _model = tf.keras.models.load_model(p)  # type: ignore[attr-defined]
                    _model_type = "keras"
                    return
                except Exception:
                    continue
        except Exception:
            continue


def _load_labels() -> Optional[List[str]]:
    """Attempt to load a labels file that maps model output indices to human labels.
    Look for disease_labels.json or crop_labels.json in the backend folder.
    """
    global _label_cache
    if _label_cache is not None:
        return _label_cache
    candidates = [
        os.path.join(HERE, "disease_labels.json"),
        os.path.join(HERE, "disease_labels.txt"),
        os.path.join(HERE, "crop_labels.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                if p.endswith(".json"):
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Expect either a list or an object with 'labels' key
                        if isinstance(data, list):
                            _label_cache = [str(x) for x in data]
                            return _label_cache
                        if isinstance(data, dict) and "labels" in data:
                            _label_cache = [str(x) for x in data.get("labels", [])]
                            return _label_cache
                else:
                    # plain text, one label per line
                    with open(p, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip()]
                        if lines:
                            _label_cache = lines
                            return _label_cache
            except Exception:
                continue
    return None


def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """Analyze an image (bytes) and return a detection result.
    If no model is available, return a deterministic stub result.
    """
    _load_model_if_available()
    # If we have a model, attempt an inference pass (best-effort, defensive)
    if _model is not None:
        try:
            # Keras model inference path
            if _model_type == "keras":
                try:
                    import tensorflow as tf  # type: ignore
                    import numpy as _np

                    # Decode image and ensure 3 channels
                    img = tf.io.decode_image(image_bytes, channels=3)
                    img = tf.image.convert_image_dtype(img, tf.float32)

                    # Try to infer target size from model input_shape
                    target_h = 224
                    target_w = 224
                    try:
                        inp = _model.input_shape
                        # input_shape may be (None, h, w, c) or (None, None, None, 3)
                        if isinstance(inp, (list, tuple)) and len(inp) >= 3:
                            h = inp[1]
                            w = inp[2]
                            if (
                                isinstance(h, int)
                                and isinstance(w, int)
                                and h > 0
                                and w > 0
                            ):
                                target_h = int(h)
                                target_w = int(w)
                    except Exception:
                        pass

                    img = tf.image.resize(img, [target_h, target_w])
                    batch = tf.expand_dims(img, 0)

                    preds = _model.predict(batch, verbose=0)
                    probs = preds[0]
                    # Ensure probs is 1-D
                    try:
                        import numpy as _np

                        probs = _np.asarray(probs).flatten()
                    except Exception:
                        probs = list(probs)

                    labels = _load_labels()
                    # Build top-k results
                    try:
                        import numpy as _np

                        # Determine number of prediction entries robustly (works for numpy arrays and plain lists)
                        try:
                            # try to read shape (for numpy arrays or similar)
                            n_items = int(getattr(probs, "shape")[0])
                        except Exception:
                            try:
                                # fallback to len() for lists/iterables
                                n_items = len(probs)
                            except Exception:
                                n_items = 0
                        topk = min(5, n_items)
                        idxs = _np.argsort(probs)[::-1][:topk]
                        results = []
                        for i in idxs:
                            lab = None
                            try:
                                lab = (
                                    labels[int(i)]
                                    if labels and int(i) < len(labels)
                                    else str(int(i))
                                )
                            except Exception:
                                lab = str(int(i))
                            results.append(
                                {"label": lab, "confidence": float(probs[int(i)])}
                            )
                    except Exception:
                        # Fallback: list top 1
                        results = [
                            {
                                "label": (labels[0] if labels else "0"),
                                "confidence": float(probs[0]),
                            }
                        ]

                    # Synthesize treatment guidance for top results if labels are available
                    try:
                        synth = _synthesize_treatments(results)
                    except Exception:
                        synth = None
                    return {
                        "ok": True,
                        "model": "keras",
                        "predictions": results,
                        "treatment_plan": synth,
                    }
                except Exception as e:
                    return {
                        "ok": False,
                        "error": "keras_inference_error",
                        "message": str(e),
                    }

            # Joblib/scikit-learn model inference path (classical models or pipelines)
            if _model_type == "joblib":
                try:
                    import numpy as _np

                    # Use PIL if available for robust image decoding; fall back to TensorFlow
                    try:
                        from PIL import Image

                        pil = True
                    except Exception:
                        pil = False

                    if pil:
                        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                        img_small = img.resize((64, 64))
                        arr = _np.asarray(img_small).astype(_np.float32) / 255.0
                    else:
                        try:
                            import tensorflow as tf  # type: ignore

                            img = tf.io.decode_image(image_bytes, channels=3)
                            img = tf.image.resize(img, [64, 64])
                            arr = _np.asarray(img)
                        except Exception:
                            raise RuntimeError(
                                "No image decoder available for joblib model inference"
                            )

                    # Simple feature vector: per-channel histograms + mean/std
                    feats: List[float] = []
                    try:
                        for ch in range(3):
                            h, _ = _np.histogram(
                                arr[:, :, ch].flatten(), bins=16, range=(0.0, 1.0)
                            )
                            feats.extend(h.astype(float).tolist())
                    except Exception:
                        # If arr is 0..255 scaled, normalize
                        arrn = arr.astype(_np.float32) / 255.0
                        for ch in range(3):
                            h, _ = _np.histogram(
                                arrn[:, :, ch].flatten(), bins=16, range=(0.0, 1.0)
                            )
                            feats.extend(h.astype(float).tolist())

                    # means and stds
                    m = _np.mean(arr, axis=(0, 1)).tolist()
                    s = _np.std(arr, axis=(0, 1)).tolist()
                    feats.extend([float(x) for x in m])
                    feats.extend([float(x) for x in s])

                    X = _np.asarray(feats, dtype=_np.float32).reshape(1, -1)
                    model = _model

                    # Try predict_proba for classification, else predict
                    if hasattr(model, "predict_proba"):
                        probs = model.predict_proba(X)
                        probs_row = probs[0]
                        classes = getattr(model, "classes_", None)
                        # Return top-k
                        import numpy as _np

                        idxs = _np.argsort(probs_row)[::-1][:5]
                        results = []
                        for i in idxs:
                            lab = (
                                str(classes[int(i)])
                                if classes is not None and int(i) < len(classes)
                                else str(int(i))
                            )
                            results.append(
                                {"label": lab, "confidence": float(probs_row[int(i)])}
                            )
                        # Synthesize treatment guidance for joblib results as well
                        try:
                            synth = _synthesize_treatments(results)
                        except Exception:
                            synth = None
                        return {
                            "ok": True,
                            "model": "joblib",
                            "predictions": results,
                            "treatment_plan": synth,
                        }
                    else:
                        pred = model.predict(X)
                        return {
                            "ok": True,
                            "model": "joblib",
                            "predictions": [{"label": str(pred[0]), "confidence": 1.0}],
                        }
                except Exception as e:
                    return {
                        "ok": False,
                        "error": "joblib_inference_error",
                        "message": str(e),
                    }
        except Exception as e:
            return {"ok": False, "error": "model_error", "message": str(e)}

    # No model available — deterministic heuristic stub
    # Basic stub: return a synthetic detection with low confidence
    return {
        "ok": True,
        "model": None,
        "diseases": [
            {
                "name": "unknown",
                "confidence": 0.0,
                "severity": "unknown",
                "treatment": [],
            }
        ],
        "note": "No disease model available; returned deterministic stub result.",
    }


def analyze_image_fileobj(fobj: Any) -> Dict[str, Any]:
    """Accept a bytes object, a file-like object (with .read()), or an UploadFile-like
    object and normalize to raw bytes before delegating to analyze_image_bytes.
    This is defensive so endpoints can pass either UploadFile, file.file, or raw bytes.
    """
    # Raw bytes were passed directly
    try:
        if isinstance(fobj, (bytes, bytearray)):
            return analyze_image_bytes(bytes(fobj))
    except Exception:
        pass

    # If a file-like object with read() is provided, call it
    try:
        read_fn = getattr(fobj, "read", None)
        if callable(read_fn):
            data = read_fn()
            # If the read returned a coroutine (async UploadFile.read), try to resolve it
            try:
                import asyncio

                if asyncio.iscoroutine(data):
                    # run the coroutine to completion in this sync helper
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        data = loop.run_until_complete(data)
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass
            except Exception:
                pass

            if isinstance(data, (bytes, bytearray)):
                return analyze_image_bytes(bytes(data))
            if isinstance(data, str):
                return analyze_image_bytes(data.encode("utf-8"))

    except Exception:
        # Fall through to next strategy
        pass

    # Some frameworks (FastAPI UploadFile) expose a .file attribute
    try:
        inner = getattr(fobj, "file", None)
        if inner is not None and hasattr(inner, "read"):
            data = inner.read()
            if isinstance(data, (bytes, bytearray)):
                return analyze_image_bytes(bytes(data))
            if isinstance(data, str):
                return analyze_image_bytes(data.encode("utf-8"))
    except Exception:
        pass

    return {
        "ok": False,
        "error": "no_input",
        "message": "Unsupported input type; provide bytes, a file-like object, or an UploadFile",
    }


def _synthesize_treatments(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate a small rule-based treatment plan and severity tag for each prediction.
    This is intentionally conservative: suggestions are advisory only and should be
    validated by an agronomist in production.
    """
    labels = _load_labels() or []
    out: List[Dict[str, Any]] = []

    # small static map of heuristics for common disease names to treatments
    heuristics = {
        "late_blight": {
            "severity_map": {"low": 0.3, "medium": 0.6, "high": 0.85},
            "steps": [
                "Remove and destroy infected foliage",
                "Apply copper-based fungicide according to label rates",
                "Improve air circulation and avoid overhead irrigation",
            ],
        },
        "powdery_mildew": {
            "severity_map": {"low": 0.25, "medium": 0.55, "high": 0.8},
            "steps": [
                "Prune affected areas and increase sunlight exposure",
                "Apply potassium bicarbonate spray as per instructions",
            ],
        },
        "leaf_spot": {
            "severity_map": {"low": 0.2, "medium": 0.5, "high": 0.75},
            "steps": [
                "Remove heavily affected leaves",
                "Avoid overhead watering and improve drainage",
                "Consider a targeted fungicide if cultural controls fail",
            ],
        },
        "rust": {
            "severity_map": {"low": 0.15, "medium": 0.45, "high": 0.7},
            "steps": [
                "Rake and destroy fallen infected debris",
                "Plant resistant cultivars when available",
                "Rotate crops to reduce inoculum build-up",
            ],
        },
        "septoria_leaf_spot": {
            "severity_map": {"low": 0.2, "medium": 0.5, "high": 0.8},
            "steps": [
                "Improve plant spacing and airflow",
                "Remove symptomatic leaves",
                "Apply recommended fungicide programs per label",
            ],
        },
    }

    for p in predictions:
        label = p.get("label", "unknown")
        confidence = float(p.get("confidence", 0.0) or 0.0)

        # Normalize label key for lookup (lowercase, underscores)
        key = str(label).lower().replace(" ", "_")

        # default severity: derive from confidence
        if confidence >= 0.8:
            severity = "high"
        elif confidence >= 0.5:
            severity = "medium"
        elif confidence > 0.0:
            severity = "low"
        else:
            severity = "unknown"

        # Try to use heuristics for known diseases, otherwise fall back to a
        # conservative, safety-first list of suggestions.
        if key in heuristics:
            rule = heuristics[key]
            treatment_steps = rule.get("steps", [])
            # Optionally, append a conservative consult step for medium/high
            if severity in ("medium", "high"):
                treatment_steps = treatment_steps + [
                    "If unsure, send photos and sample to local extension service before broad chemical use"
                ]
        else:
            # Generic conservative steps
            treatment_steps = [
                "Isolate affected plants if possible",
                "Take a clear photo and consult an expert before chemical control",
            ]

        out.append(
            {
                "label": label,
                "confidence": confidence,
                "severity": severity,
                "treatment": treatment_steps,
            }
        )

    return out
