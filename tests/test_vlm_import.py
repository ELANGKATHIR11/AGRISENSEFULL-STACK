
import sys
import os
import pytest

# Ensure the repository root is on sys.path so local package imports work when tests
# are run from different working directories or virtualenvs.
# Try a few candidate roots so tests run whether executed from the repo root
# or from subfolders (common in CI/test runners).
candidate_roots = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "AGRISENSEFULL-STACK")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrisense_app")),
]
for ROOT in candidate_roots:
    # Prefer the root that contains the backend vlm_engine implementation.
    vlm_path = os.path.join(ROOT, "agrisense_app", "backend", "vlm_engine.py")
    if os.path.isfile(vlm_path):
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        break
    # Fallback: if there is an agrisense_app package at this root, allow it but continue searching
    if os.path.isdir(os.path.join(ROOT, "agrisense_app")) and ROOT not in sys.path:
        sys.path.insert(0, ROOT)
        # do not break here; prefer a root that contains backend/vlm_engine.py

try:
    # Import the vlm engine module; it internally guards heavy ML imports.
    from agrisense_app.backend import vlm_engine
except Exception:
    vlm_engine = None


def test_vlm_engine_import_and_api_contract():
    """Fast smoke test: ensure vlm_engine import works and core API is present.

    This test intentionally does not require GPU or heavy models. The VLM module
    provides fallbacks when optional ML packages are missing, so this test validates
    the lightweight import surface and a basic analysis call.
    """
    assert vlm_engine is not None, "vlm_engine module should be importable"

    # Ensure helper functions exist
    assert hasattr(vlm_engine, "get_vlm_engine")
    assert hasattr(vlm_engine, "analyze_with_vlm")

    engine = vlm_engine.get_vlm_engine()
    # Basic contract: engine should expose generate_enhanced_analysis
    assert hasattr(engine, "generate_enhanced_analysis")

    # Call the analysis with a tiny dummy image (1x1 RGB) encoded as bytes
    from PIL import Image
    import io

    img = Image.new("RGB", (1, 1), color=(0, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    result = vlm_engine.analyze_with_vlm(img_bytes, analysis_type="general", crop_type="test")
    assert isinstance(result, dict)
    assert "vision_analysis" in result
    assert "vlm_version" in result
