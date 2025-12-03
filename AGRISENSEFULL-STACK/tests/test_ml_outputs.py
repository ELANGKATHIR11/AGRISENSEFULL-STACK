import base64
from io import BytesIO
from PIL import Image
import json

import pytest

from agrisense_app.backend.comprehensive_disease_detector import ComprehensiveDiseaseDetector

# Simple helper to create a tiny RGB image and encode to base64

def make_test_image(color=(120,200,120)):
    img = Image.new('RGB', (64,64), color)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


def test_disease_output_schema():
    detector = ComprehensiveDiseaseDetector()
    img_b64 = make_test_image()
    result = detector.analyze_disease_image(img_b64, crop_type='Tomato')

    # Required keys
    required_keys = ['timestamp', 'crop_type', 'primary_disease', 'confidence', 'severity', 'treatment', 'recommended_treatments']
    for k in required_keys:
        assert k in result, f"Missing key: {k}"

    # Types
    assert isinstance(result['primary_disease'], str)
    assert isinstance(result['confidence'], float)
    assert isinstance(result['severity'], str)
    assert isinstance(result['treatment'], dict)
    assert isinstance(result['recommended_treatments'], dict)


@pytest.mark.skip(reason="Weed model artifacts may not be available in CI")
def test_weed_output_schema():
    from agrisense_app.backend.weed_management import WeedManagementEngine
    engine = WeedManagementEngine()
    img_b64 = make_test_image(color=(60,180,90))
    res = engine.detect_weeds(img_b64)

    # Expected keys
    keys = ['timestamp', 'weed_coverage_percentage', 'weed_regions', 'management_recommendations']
    for k in keys:
        assert k in res

    assert isinstance(res['weed_coverage_percentage'], (float, type(None)))
    assert isinstance(res['weed_regions'], list)
    assert isinstance(res['management_recommendations'], list)
