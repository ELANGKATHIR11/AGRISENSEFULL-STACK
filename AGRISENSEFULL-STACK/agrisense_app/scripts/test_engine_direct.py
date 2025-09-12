import json
import sys
sys.path.insert(0, r'd:\downloads\agrisense_app')
from backend.engine import RecoEngine

eng = RecoEngine()
rec = eng.recommend({
    'plant':'wheat',
    'soil_type':'loam',
    'area_m2': 100,
    'ph': 6.5,
    'moisture_pct': 30,
    'temperature_c': 28,
    'ec_dS_m': 1.0
})
print(json.dumps(rec, indent=2))
