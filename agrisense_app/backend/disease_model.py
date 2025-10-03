"""
Lightweight, lazy loader for a TensorFlow SavedModel (disease classifier).

Features:
- Respects AGRISENSE_DISABLE_ML to avoid importing TF in CI/dev where ML is disabled.
- Looks for common model locations; path can be overridden with AGRISENSE_DISEASE_MODEL_PATH.
- Uses the SavedModel `serving_default` signature when available and infers input shape.
- Returns top-k (index or label) with scores.

This file avoids forcing `tensorflow` onto CI by raising helpful errors when ML is disabled
or tensorflow is not installed. Place your SavedModel folder at the repo root or set
AGRISENSE_DISEASE_MODEL_PATH to its location.
"""
from __future__ import annotations

import io
import os
import json
from typing import List, Optional, Dict, Any

import numpy as np
from PIL import Image

# Lazy import of tensorflow - only when actually needed
_TF_AVAILABLE = True
try:
    import tensorflow as tf  # type: ignore
except Exception:  # pragma: no cover - TF likely missing in CI/dev
    tf = None
    _TF_AVAILABLE = False


def _is_ml_disabled() -> bool:
    v = os.getenv("AGRISENSE_DISABLE_ML", "0").strip().lower()
    return v in ("1", "true", "yes")


def _candidate_model_paths() -> List[str]:
    # Order: explicit env, common repo places, attached folder name
    env = os.getenv("AGRISENSE_DISEASE_MODEL_PATH")
    candidates = []
    if env:
        candidates.append(env)
    candidates += [
        "ml_models/disease_classification",
        "ml_models/disease_detection",
        "disease-classification-tensorflow2-disease-classification-v1",
        "disease_model",
    ]
    return candidates


def find_model_path() -> Optional[str]:
    for p in _candidate_model_paths():
        if os.path.isabs(p):
            path = p
        else:
            path = os.path.join(os.getcwd(), p)
        if os.path.isdir(path):
            return path
    return None


def _to_numpy(obj: Any) -> np.ndarray:
    """Safely convert a TF tensor-like or array-like object to a numpy ndarray.

    This helper guards against cases where tf.convert_to_tensor may not be present/usable
    or where .numpy() may raise; it tries several fallbacks and always returns an ndarray
    or raises a clear RuntimeError.
    """
    # 1) If object exposes a numpy() method, prefer that
    try:
        if hasattr(obj, "numpy"):
            try:
                np_fn = getattr(obj, "numpy", None)
                if callable(np_fn):
                    try:
                        res = np_fn()
                        return np.asarray(res)
                    except Exception:
                        # fall through to other strategies
                        pass
            except Exception:
                # fall through to other strategies
                pass

        # 2) If TF is available and has convert_to_tensor, try that
        if _TF_AVAILABLE and tf is not None and getattr(tf, "convert_to_tensor", None) and callable(
            tf.convert_to_tensor
        ):
            try:
                t = tf.convert_to_tensor(obj)
                if hasattr(t, "numpy"):
                    try:
                        return t.numpy()
                    except Exception:
                        # fall through to np.asarray
                        pass
                return np.asarray(t)
            except Exception:
                # fall through to other strategies
                pass

        # 3) Common Python/numpy sequences
        if isinstance(obj, (np.ndarray, list, tuple)):
            return np.asarray(obj)

        # 4) Last resort: try np.asarray on whatever we have
        return np.asarray(obj)
    except Exception as exc:
        raise RuntimeError("Failed to convert model output to numpy array") from exc


class DiseaseModel:
    """Wrapper around a TF SavedModel to do simple image predictions.

    Usage:
        m = DiseaseModel()
        preds = m.predict_from_image_bytes(open('foo.jpg','rb').read())
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or find_model_path()
        self._loaded = False
        self._model = None
        self._signature = None
        self._input_shape = (224, 224, 3)
        self._dtype = None
        self._labels: Optional[List[str]] = None

    def load(self) -> None:
        if _is_ml_disabled():
            raise RuntimeError("ML is disabled (AGRISENSE_DISABLE_ML=1). Enable to load model.")
        # Ensure both the availability flag and the module object are present so static
        # type checkers understand that `tf` is not None below.
        if not _TF_AVAILABLE or tf is None:
            raise RuntimeError("tensorflow is not available. Install tensorflow to use the disease model.")
        if not self.model_path:
            raise FileNotFoundError(
                "No model path found. Set AGRISENSE_DISEASE_MODEL_PATH or place the SavedModel in a known location."
            )

        # Load SavedModel
        # 'tf' is guarded above; static type checkers can now assume it's not None
        loaded = tf.saved_model.load(self.model_path)

        # Try to obtain serving_default signature in a safe way (loaded may be an AutoTrackable
        # without a 'signatures' attribute or with signatures set to None).
        sig = None
        try:
            sigs = getattr(loaded, "signatures", None)
            if sigs is not None:
                # signatures is usually a dict-like mapping; guard against unexpected types
                sig = sigs.get("serving_default") if hasattr(sigs, "get") else None
        except Exception:
            sig = None

        # If no signature, try calling the loaded object itself on a tensor
        self._model = loaded
        self._signature = sig

        # Infer input shape/dtype from signature if possible
        if sig is not None:
            try:
                _, kwargs = sig.structured_input_signature
                # kwargs will be a mapping of name->TensorSpec; take the first
                if kwargs:
                    first = next(iter(kwargs.values()))
                    shape = getattr(first, "shape", None)
                    dtype = getattr(first, "dtype", None)
                    if shape is not None:
                        # shape is like (None, H, W, C) or (None, dim)
                        if len(shape) >= 3:
                            h, w = int(shape[1]), int(shape[2])
                            self._input_shape = (h, w, 3)
                    if dtype is not None:
                        self._dtype = dtype
            except Exception:
                pass

        self._loaded = True

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        h, w, _ = self._input_shape
        # Use Pillow's Resampling enum if available (newer Pillow versions),
        # otherwise fall back to the legacy constant for older versions.
        # Avoid direct attribute access that static type checkers may flag.
        resample = None
        resampling_cls = getattr(Image, "Resampling", None)
        if resampling_cls is not None:
            resample = getattr(resampling_cls, "BILINEAR", None)
        if resample is None:
            # fallback to legacy constant if present, else use NEAREST as safe default
            resample = getattr(Image, "BILINEAR", getattr(Image, "NEAREST"))
        img = img.resize((w, h), resample)
        arr = np.asarray(img).astype(np.float32) / 255.0
        # If model expects a different dtype, cast later in TF
        arr = np.expand_dims(arr, axis=0)
        return arr

    def _load_labels_if_present(self) -> None:
        # Look for a labels file next to model
        if not self.model_path:
            return
        for fname in ("labels.txt", "labels.json", "labels.csv"):
            p = os.path.join(self.model_path, fname)
            if os.path.exists(p):
                try:
                    if fname.endswith(".txt"):
                        with open(p, "r", encoding="utf8") as f:
                            self._labels = [l.strip() for l in f if l.strip()]
                    else:
                        with open(p, "r", encoding="utf8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self._labels = data
                            elif isinstance(data, dict) and "labels" in data:
                                self._labels = data["labels"]
                except Exception:
                    # silently ignore
                    self._labels = None
                return

    def predict_from_image_bytes(self, image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
        """Run inference on raw image bytes and return top-k predictions.

        Returns list of {"label"|"index", "score"}.
        """
        self._ensure_loaded()
        self._load_labels_if_present()

        arr = self._preprocess(image_bytes)

        # Convert to tf tensor if TF is available
        if _TF_AVAILABLE and tf is not None:
            tensor = tf.convert_to_tensor(arr)
            out = None

            # If signature exists, try to use it
            if self._signature is not None:
                try:
                    _, kwargs = self._signature.structured_input_signature
                    if kwargs:
                        # pass the first expected input name
                        name = next(iter(kwargs.keys()))
                        out = self._signature(**{name: tensor})
                    else:
                        out = self._signature(tensor)
                except Exception:
                    # signature invocation failed; fall back to other strategies
                    out = None

            # If signature wasn't usable, try common model callables (predict/call/__call__)
            if out is None:
                for attr in ("predict", "call", "__call__"):
                    fn = getattr(self._model, attr, None)
                    if callable(fn):
                        try:
                            out = fn(tensor)
                            break
                        except Exception:
                            out = None

            if out is None:
                raise RuntimeError(
                    "Model object is not directly callable and no usable signatures were found; "
                    "ensure the SavedModel exposes a 'serving_default' signature or provides a 'predict'/'call' method."
                )

            # Normalize outputs to a numpy array using the robust helper
            if isinstance(out, dict):
                val = next(iter(out.values()))
                scores = _to_numpy(val)
            else:
                scores = _to_numpy(out)

            scores = np.asarray(scores)
            # ensure (N, num_classes)
            if scores.ndim == 1:
                scores = np.expand_dims(scores, axis=0)

            scores = scores[0]
            # Get top-k indices
            top_idx = np.argsort(scores)[::-1][:top_k]
            results = []
            for i in top_idx:
                label = None
                if self._labels and i < len(self._labels):
                    label = self._labels[i]
                results.append({"index": int(i), "label": label or str(i), "score": float(scores[int(i)])})
            return results
        else:
            raise RuntimeError("tensorflow is not available for inference")


# Convenience module-level functions
_GLOBAL_MODEL: Optional[DiseaseModel] = None


def get_global_model() -> DiseaseModel:
    global _GLOBAL_MODEL
    if _GLOBAL_MODEL is None:
        _GLOBAL_MODEL = DiseaseModel()
    return _GLOBAL_MODEL


def predict_from_image_bytes(image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    return get_global_model().predict_from_image_bytes(image_bytes, top_k=top_k)
