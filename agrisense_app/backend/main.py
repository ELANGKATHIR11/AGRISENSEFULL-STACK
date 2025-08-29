from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
from typing import Dict, Any, List, Optional, Union, cast, Protocol, runtime_checkable
from pydantic import BaseModel

# Support running as a package (uvicorn backend.main:app) or as a module from backend folder (uvicorn main:app)
try:
    from .models import SensorReading, Recommendation
    from .engine import RecoEngine
    from .data_store import insert_reading, recent
    from .smart_farming_ml import SmartFarmingRecommendationSystem
except ImportError:  # no parent package context
    from models import SensorReading, Recommendation
    from engine import RecoEngine
    from data_store import insert_reading, recent
    from smart_farming_ml import SmartFarmingRecommendationSystem

app = FastAPI(title="Agri-Sense API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RecoEngine()

@runtime_checkable
class HasCropRecommender(Protocol):
    def get_crop_recommendations(self, sensor_data: Dict[str, Union[float, str]]) -> Optional[List[Dict[str, Any]]]:
        ...

farming_system: Optional[HasCropRecommender] = None  # lazy init to avoid longer cold start

class Health(BaseModel):
    status: str

@app.get("/health")
def health() -> Health:
    return Health(status="ok")

@app.get("/live")
def live() -> Health:
    return Health(status="live")

@app.get("/ready")
def ready() -> Dict[str, Any]:
    # Ready if engine constructed and models (optional) loaded fine
    return {"status": "ready", "water_model": engine.water_model is not None, "fert_model": engine.fert_model is not None}

    

@app.post("/ingest")
def ingest(reading: SensorReading) -> Dict[str, bool]:
    insert_reading(reading.model_dump())
    return {"ok": True}

@app.get("/recent")
def get_recent(zone_id: str = "Z1", limit: int = 50) -> Dict[str, Any]:
    return {"items": recent(zone_id, limit)}

@app.post("/recommend")
def recommend(reading: SensorReading, request: Request) -> Recommendation:
    # don't persist automatically; clients can call /ingest
    payload = reading.model_dump()
    rec: Dict[str, Any] = engine.recommend(payload)
    # Pydantic will coerce Dict[str, Any] -> Recommendation
    return Recommendation.model_validate(rec)

class CropSuggestion(BaseModel):
    crop: str
    suitability_score: float
    expected_yield: Optional[float] = None

class SuggestCropResponse(BaseModel):
    soil_type: str
    top: List[CropSuggestion]

@app.post("/suggest_crop")
def suggest_crop(payload: Dict[str, Any]) -> SuggestCropResponse:
    """
    Suggest high-yield crops for a given soil type and optional conditions.
    Body example: {"soil_type": "loam", "ph": 6.8, "temperature": 25, "moisture": 60}
    """
    global farming_system
    if farming_system is None:
        # Initialize on first use, honor optional env var for dataset path
        ds_override = os.getenv("AGRISENSE_DATASET") or os.getenv("DATASET_CSV")
        if ds_override:
            farming_system = cast(HasCropRecommender, SmartFarmingRecommendationSystem(dataset_path=ds_override))
        else:
            farming_system = cast(HasCropRecommender, SmartFarmingRecommendationSystem())

    soil_in = str(payload.get("soil_type", "loam")).strip().lower()
    # Map internal simple soil types to dataset soil categories
    soil_map = {
        "loam": "Loam",
        "sandy": "Sandy",
        "sand": "Sandy",
        "clay": "Clay Loam",
        "clay loam": "Clay Loam",
        "sandy loam": "Sandy Loam",
        "black cotton": "Black Cotton",
    }
    soil_ds = soil_map.get(soil_in, soil_in.title())

    sensor_data: Dict[str, Union[float, str]] = {
        "ph": float(payload.get("ph", 6.8)),
        "nitrogen": float(payload.get("nitrogen", 100)),
        "phosphorus": float(payload.get("phosphorus", 40)),
        "potassium": float(payload.get("potassium", 40)),
        "temperature": float(payload.get("temperature", payload.get("temperature_c", 25))),
        "water_level": float(payload.get("water_level", 500)),
        "moisture": float(payload.get("moisture", payload.get("moisture_pct", 60))),
        "humidity": float(payload.get("humidity", 70)),
        "soil_type": soil_ds,
    }
    # Typed via Protocol so Pylance understands shapes
    recs_raw: Optional[List[Dict[str, Any]]] = farming_system.get_crop_recommendations(sensor_data)  # type: ignore[reportUnknownMemberType]
    recs: List[CropSuggestion] = []
    for r in (recs_raw or []):
        score_val = r.get("suitability_score", r.get("score", 0.0))
        try:
            score = float(score_val)  # type: ignore[arg-type]
        except Exception:
            score = 0.0
        item = CropSuggestion(crop=str(r.get("crop", "")), suitability_score=score)
        ey = r.get("expected_yield")
        if ey is not None:
            try:
                item.expected_yield = float(ey)  # type: ignore[arg-type]
            except Exception:
                pass
        recs.append(item)
    # Return compact top items
    return SuggestCropResponse(soil_type=soil_ds, top=recs[:5])

class PlantItem(BaseModel):
    value: str
    label: str

class PlantsResponse(BaseModel):
    items: List[PlantItem]

@app.get("/plants")
def get_plants() -> PlantsResponse:
    """Return a combined list of crops from config and dataset labels.
    Output shape: [{"value": "rice", "label": "Rice"}, ...]
    """
    ROOT = os.path.dirname(__file__)
    labels_path = os.path.join(ROOT, "crop_labels.json")

    def norm(name: str) -> PlantItem:
        slug = (
            name.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )
        label = name.replace("_", " ").strip()
        # Title case but preserve acronyms reasonably
        label = " ".join([w.capitalize() for w in label.split()])
        return PlantItem(value=slug, label=label)

    items: Dict[str, PlantItem] = {}
    # From config plants
    for k in engine.plants.keys():
        items[k] = norm(k)
    # From dataset labels if present
    if os.path.exists(labels_path):
        try:
            with open(labels_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for c in data.get("crops", []):
                n = norm(str(c))
                items[n.value] = n
        except Exception:
            pass
    # Ensure a sensible default exists
    if "generic" not in items:
        items["generic"] = PlantItem(value="generic", label="Generic")

    sorted_items = sorted(items.values(), key=lambda x: x.label)
    return PlantsResponse(items=sorted_items)

# Serve the frontend as static files under /ui.
# Prefer built React app in frontend/dist if present; otherwise serve legacy frontend directory.
ROOT = os.path.dirname(__file__)
FRONTEND_DIST = os.path.join(ROOT, "..", "frontend", "dist")
FRONTEND_LEGACY = os.path.join(ROOT, "..", "frontend")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
elif os.path.isdir(FRONTEND_LEGACY):
    app.mount("/ui", StaticFiles(directory=FRONTEND_LEGACY, html=True), name="frontend")