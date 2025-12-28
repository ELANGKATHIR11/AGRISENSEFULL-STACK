import json
from typing import Dict, Any
# Import via package path so this file can be imported during test collection without
# relying on adhoc sys.path hacks. When executed as a script, it will run a small demo.
try:
    from agrisense_app.backend.core.engine import RecoEngine
except Exception:
    # Fallback to legacy top-level package name if present in some environments.
    from backend.core.engine import RecoEngine  # type: ignore

def run_example() -> None:
    eng = RecoEngine()
    rec = eng.recommend({
    'plant': 'wheat',
    'soil_type': 'loam',
    'area_m2': 100,
    'ph': 6.5,
    'moisture_pct': 30,
    'temperature_c': 28,
    'ec_dS_m': 1.0,
    })
    print(json.dumps(rec, indent=2))

if __name__ == '__main__':
    run_example()
import json
import sys
sys.path.insert(0, r'd:\downloads\agrisense_app')
from backend.core.engine import RecoEngine

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
