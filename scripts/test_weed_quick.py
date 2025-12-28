#!/usr/bin/env python
"""Quick weed detection helper.

This file previously performed a live HTTP POST at import time which caused
pytest collection to attempt network calls. We now guard the live call so the
module can be imported safely. A small helper function is provided for manual
invocation and a pytest-friendly function is present for unit tests to mock.
"""
from typing import Dict

import requests


def post_weed_image(base_url: str, image_b64: str) -> requests.Response:
    """Post a base64-encoded image to the weed analyze endpoint."""
    return requests.post(f"{base_url.rstrip('/')}/weed/analyze", json={"image_data": image_b64})


def run_quick_test() -> None:
    test_image = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    response = post_weed_image("http://127.0.0.1:8004", test_image)

    if response.status_code == 200:
        result = response.json()
        print("🌿 Weed Detection Success!")
        print(f"   Classification: {result.get('classification', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.1f}%")
        print(f"   Analysis Method: {result.get('analysis_method', 'unknown')}")
    else:
        print(f"❌ Weed Detection Failed: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    run_quick_test()