from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi import HTTPException
import os
import csv
import json
from typing import Dict, Any, List, Optional, Union, cast, Protocol, runtime_checkable, Set
from pydantic import BaseModel

# Support running as a package (uvicorn backend.main:app) or as a module from backend folder (uvicorn main:app)
try:
    from .models import SensorReading, Recommendation
    from .engine import RecoEngine
    from .data_store import insert_reading, recent, insert_reco_snapshot, recent_reco
    from .smart_farming_ml import SmartFarmingRecommendationSystem
except ImportError:  # no parent package context
    from models import SensorReading, Recommendation
    from engine import RecoEngine
    from data_store import insert_reading, recent, insert_reco_snapshot, recent_reco
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
    # Optionally log snapshots if flag set
    if os.getenv("AGRISENSE_LOG_RECO", "0") not in ("0", "false", "False", "no"):
        try:
            insert_reco_snapshot(payload.get("zone_id", "Z1"), str(payload.get("plant", "generic")), rec, None)
        except Exception:
            pass
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
    category: Optional[str] = None

class PlantsResponse(BaseModel):
    items: List[PlantItem]

# Simple cache of dataset rows (name/category)
_dataset_crops_cache: Optional[List[Dict[str, Optional[str]]]] = None

def _load_dataset_crops() -> List[Dict[str, Optional[str]]]:
    global _dataset_crops_cache
    if _dataset_crops_cache is not None:
        return _dataset_crops_cache
    ROOT = os.path.dirname(__file__)
    dataset_path = os.path.join(ROOT, "india_crop_dataset.csv")
    crops: List[Dict[str, Optional[str]]] = []
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = str(row.get("Crop", "")).strip()
                    if name:
                        cat_raw = row.get("Crop_Category")
                        category = str(cat_raw).strip() if cat_raw is not None else None
                        crops.append({"name": name, "category": category})
        except Exception:
            pass
    # de-duplicate while preserving order
    seen: Set[str] = set()
    unique: List[Dict[str, Optional[str]]] = []
    for c in crops:
        key = str(c.get("name", ""))
        if key not in seen:
            unique.append(c)
            seen.add(key)
    _dataset_crops_cache = unique
    return unique

@app.get("/plants")
def get_plants() -> PlantsResponse:
    """Return a combined list of crops from config and dataset labels.
    Output shape: [{"value": "rice", "label": "Rice"}, ...]
    """
    ROOT = os.path.dirname(__file__)
    labels_path = os.path.join(ROOT, "crop_labels.json")

    def norm(name: str, category: Optional[str] = None) -> PlantItem:
        slug = (
            name.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )
        label = name.replace("_", " ").strip()
        # Title case but preserve acronyms reasonably
        label = " ".join([w.capitalize() for w in label.split()])
        return PlantItem(value=slug, label=label, category=category or None)

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
    # Also merge crops from the CSV dataset (with categories when available)
    for row in _load_dataset_crops():
        nm = str(row.get("name", ""))
        cat_val = row.get("category")
        cat = str(cat_val) if cat_val else None
        n = norm(nm, category=cat)
        if n.value:
            items[n.value] = n
    # Ensure a sensible default exists
    if "generic" not in items:
        items["generic"] = PlantItem(value="generic", label="Generic")

    sorted_items = sorted(items.values(), key=lambda x: x.label)
    return PlantsResponse(items=sorted_items)

# Rich crop info for the Crops UI page
class CropCard(BaseModel):
    id: str
    name: str
    scientificName: Optional[str] = None
    category: Optional[str] = None
    season: Optional[str] = None
    waterRequirement: Optional[str] = None  # Low|Medium|High
    tempRange: Optional[str] = None
    phRange: Optional[str] = None
    growthPeriod: Optional[str] = None
    description: Optional[str] = None
    tips: List[str] = []

class CropsResponse(BaseModel):
    items: List[CropCard]

def _bucket_water_req(mm: Optional[float]) -> Optional[str]:
    if mm is None:
        return None
    try:
        v = float(mm)
    except Exception:
        return None
    if v <= 400:
        return "Low"
    if v <= 800:
        return "Medium"
    return "High"

def _dataset_to_cards() -> List[CropCard]:
    ROOT = os.path.dirname(__file__)
    dataset_path = os.path.join(ROOT, "india_crop_dataset.csv")
    items: List[CropCard] = []
    if not os.path.exists(dataset_path):
        return items
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = str(row.get("Crop", "")).strip()
                if not name:
                    continue
                cat = str(row.get("Crop_Category") or "").strip() or None
                try:
                    ph_min = row.get("pH_Min")
                    ph_max = row.get("pH_Max")
                    ph_range = f"{float(ph_min):.1f}-{float(ph_max):.1f}" if ph_min and ph_max else None
                except Exception:
                    ph_range = None
                try:
                    t_min = row.get("Temperature_Min_C")
                    t_max = row.get("Temperature_Max_C")
                    temp_range = f"{int(float(t_min))}-{int(float(t_max))}°C" if t_min and t_max else None
                except Exception:
                    temp_range = None
                try:
                    growth_days = row.get("Growth_Duration_days")
                    growth_period = f"{int(float(growth_days))} days" if growth_days else None
                except Exception:
                    growth_period = None
                try:
                    w_mm = row.get("Water_Requirement_mm")
                    water_req = _bucket_water_req(float(w_mm) if w_mm else None)
                except Exception:
                    water_req = None
                season = str(row.get("Growing_Season") or "").strip() or None

                slug = (
                    name.lower().replace(" ", "_").replace("-", "_")
                )
                # Simple, category-based generic tips
                base_tips: Dict[str, List[str]] = {
                    "Cereal": ["Ensure adequate nitrogen", "Maintain consistent moisture", "Plant within optimal temperature"],
                    "Vegetable": ["Use well-drained soil", "Water regularly", "Monitor pests"],
                    "Oilseed": ["Avoid waterlogging", "Sunlight exposure is key", "Balanced fertilization"],
                    "Pulse": ["Rotate with cereals", "Inoculate seeds if needed", "Avoid excessive nitrogen"],
                    "Cash Crop": ["Optimize irrigation", "Fertilize per schedule", "Scout for pests"],
                    "Spice": ["Partial shade as needed", "Mulch to retain moisture", "Harvest at maturity"],
                    "Plantation": ["Deep fertile soil", "Regular irrigation", "Nutrient management"],
                    "Tuber": ["Loose, sandy loam soil", "Avoid waterlogging", "Hill soil as needed"],
                }
                tips = base_tips.get(cat or "", ["Follow local best practices", "Test soil pH", "Irrigate as required"])

                items.append(CropCard(
                    id=slug,
                    name=name,
                    scientificName=None,
                    category=cat,
                    season=season,
                    waterRequirement=water_req,
                    tempRange=temp_range,
                    phRange=ph_range,
                    growthPeriod=growth_period,
                    description=None,
                    tips=tips,
                ))
    except Exception:
        pass
    # Ensure uniqueness by id while preserving order
    seen: Set[str] = set()
    result: List[CropCard] = []
    for it in items:
        if it.id not in seen:
            result.append(it)
            seen.add(it.id)
    return result

@app.get("/crops")
def get_crops_full() -> CropsResponse:
    return CropsResponse(items=_dataset_to_cards())

# Recommendation history endpoints for impact graphs
@app.get("/reco/recent")
def get_reco_recent(zone_id: str = "Z1", limit: int = 200) -> Dict[str, Any]:
        return {"items": recent_reco(zone_id, limit)}

@app.post("/reco/log")
def log_reco_snapshot(body: Dict[str, Any]) -> Dict[str, Any]:
        """Explicitly log a recommendation snapshot from the client.
        Body shape example:
        {
            "zone_id":"Z1","plant":"rice",
            "rec": {"water_liters":123, "expected_savings_liters":45, "fert_n_g":10, "fert_p_g":5, "fert_k_g":8},
            "yield_potential": 2.5
        }
        """
        zone_id = str(body.get("zone_id", "Z1"))
        plant = str(body.get("plant", "generic"))
        rec = dict(body.get("rec") or {})
        yield_p = body.get("yield_potential")
        insert_reco_snapshot(zone_id, plant, rec, yield_p)
        return {"ok": True}

# Serve the frontend as static files under /ui.
ROOT = os.path.dirname(__file__)
FRONTEND_DIST_NESTED = os.path.join(ROOT, "..", "frontend", "farm-fortune-frontend-main", "dist")
FRONTEND_DIST = os.path.join(ROOT, "..", "frontend", "dist")
FRONTEND_LEGACY = os.path.join(ROOT, "..", "frontend")
frontend_root: Optional[str] = None
if os.path.isdir(FRONTEND_DIST_NESTED):
    frontend_root = FRONTEND_DIST_NESTED
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIST_NESTED, html=True), name="frontend")
elif os.path.isdir(FRONTEND_DIST):
    frontend_root = FRONTEND_DIST
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
elif os.path.isdir(FRONTEND_LEGACY):
    frontend_root = FRONTEND_LEGACY
    app.mount("/ui", StaticFiles(directory=FRONTEND_LEGACY, html=True), name="frontend")

@app.get("/")
def root() -> RedirectResponse:
    # Redirect to the frontend so browsers request /ui/favicon.ico instead of /favicon.ico
    return RedirectResponse(url="/ui", status_code=307)

# SPA fallback so deep links like /ui/live or /ui/recommend render the app
@app.get("/ui/{path:path}")
def serve_spa(path: str):
    if frontend_root:
        index_file = os.path.join(frontend_root, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="UI not found")