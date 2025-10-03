"""Simple CLI to run the disease SavedModel on an image file.

Usage:
    $env:AGRISENSE_DISABLE_ML='0'; .venv\Scripts\python.exe scripts\test_disease_model_inference.py path/to/image.jpg

If tensorflow is not installed or ML is disabled the script will print an error explaining how to enable it.
"""
import sys
import os
from pprint import pprint
import importlib
import pytest

# Import VLM engine for optional visual-language based checks in integration
# Note: 'pylance' is a VS Code extension (not a python package). If you're
# using VS Code, enable the Pylance extension and set "python.analysis.typeCheckingMode"
# in .vscode/settings.json for stricter type checking. No runtime import needed here.
from agrisense_app.backend import vlm_engine


# Import the disease_model module dynamically so the script degrades gracefully
# when ML dependencies are not installed or ML is intentionally disabled.
try:
    disease_model = importlib.import_module("agrisense_app.backend.disease_model")
except Exception:
    disease_model = None


def main(argv):
    if len(argv) < 2:
        print("Usage: test_disease_model_inference.py <image_path>")
        return 2
    img_path = argv[1]
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        return 2

    if disease_model is None or not hasattr(disease_model, "predict_from_image_bytes"):
        print(
            "ML module not available: the disease model cannot be imported. "
            "Ensure you have installed ML dependencies and set AGRISENSE_DISABLE_ML='0'. "
            "See the project README for installation instructions."
        )
        return 1

    try:
        with open(img_path, "rb") as f:
            data = f.read()
        preds = disease_model.predict_from_image_bytes(data, top_k=5)
        print("Predictions:")
        pprint(preds)
    except Exception as exc:
        print(f"Error running inference: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
