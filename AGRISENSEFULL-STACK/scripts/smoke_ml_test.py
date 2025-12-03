import io
import base64
import json
from PIL import Image

from agrisense_app.backend.comprehensive_disease_detector import ComprehensiveDiseaseDetector
from agrisense_app.backend.weed_management import WeedManagementEngine

print('Creating disease detector...')
detector = ComprehensiveDiseaseDetector()
print('Detector created')

# create tiny green image
img = Image.new('RGB', (200, 200), color='green')
buf = io.BytesIO()
img.save(buf, format='JPEG')
b64 = base64.b64encode(buf.getvalue()).decode()

print('\nRunning disease analysis...')
res = detector.analyze_disease_image(b64, 'Tomato')
print('Disease output keys:', list(res.keys())[:10])
print('Primary disease:', res.get('primary_disease') or res.get('disease'))
print('Confidence:', res.get('confidence'))

print('\nCreating weed engine...')
we = WeedManagementEngine()
print('Weed engine created')

print('\nRunning weed analysis (mock)...')
we_res = we.detect_weeds(b64)
print('Weed output keys:', list(we_res.keys())[:10])
print('Weed coverage:', we_res.get('weed_coverage_percentage'))

# Print JSON summaries
print('\nDisease full summary:')
print(json.dumps({k: res[k] for k in list(res.keys())[:8]}, indent=2, default=str))
print('\nWeed full summary:')
print(json.dumps({k: we_res.get(k) for k in ['weed_coverage_percentage','weed_regions','management_recommendations']}, indent=2, default=str))
