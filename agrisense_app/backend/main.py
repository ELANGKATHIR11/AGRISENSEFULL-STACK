from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi import Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi import HTTPException
from starlette.middleware.gzip import GZipMiddleware  # type: ignore
import logging
import time
import os
import sys
import csv
import json
import uuid
import threading
from typing import (
    Dict,
    Any,
    List,
    Optional,
    Union,
    cast,
    Protocol,
    runtime_checkable,
    Set,
)
from pydantic import BaseModel

# Support running as a package (uvicorn backend.main:app) or as a module from backend folder (uvicorn main:app)
try:
    from .models import SensorReading, Recommendation
    from .engine import RecoEngine
    from .data_store import (
        insert_reading,
        recent,
        insert_reco_snapshot,
        recent_reco,
        insert_tank_level,
        latest_tank_level,
        log_valve_event,
        recent_valve_events,
        insert_alert,
        recent_alerts,
        reset_database,
    )

    # Lazy-import ML-heavy module to avoid import-time overhead when AGRISENSE_DISABLE_ML is set
    SmartFarmingRecommendationSystem = None
    from .weather import fetch_and_cache_weather, read_latest_from_cache
except ImportError:  # no parent package context
    from models import SensorReading, Recommendation
    from engine import RecoEngine
    from data_store import (
        insert_reading,
        recent,
        insert_reco_snapshot,
        recent_reco,
        insert_tank_level,
        latest_tank_level,
        log_valve_event,
        recent_valve_events,
        insert_alert,
        recent_alerts,
        reset_database,
    )

    # Lazy-import placeholder; actual import happens inside handlers that need it
    SmartFarmingRecommendationSystem = None
    from weather import fetch_and_cache_weather, read_latest_from_cache

# Load environment from .env if present (development convenience)
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

app = FastAPI(title="Agri-Sense API", version="0.2.0")

# Basic structured logger
logger = logging.getLogger("agrisense")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

# In-process counters for a lightweight /metrics endpoint
_metrics_lock = threading.Lock()
_metrics: Dict[str, Any] = {
    "started_at": time.time(),
    "requests_total": 0,
    "errors_total": 0,
    "by_path": {},  # path -> count
}


# Request ID + timing + counters middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore[no-redef]
    req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
    # update counters
    with _metrics_lock:
        _metrics["requests_total"] += 1
        by_path: Dict[str, int] = _metrics.setdefault("by_path", {})  # type: ignore[assignment]
        path = request.url.path
        by_path[path] = int(by_path.get(path, 0)) + 1
    # log and annotate response
    status = getattr(response, "status_code", 0)
    if status >= 500:
        with _metrics_lock:
            _metrics["errors_total"] += 1
    response.headers.setdefault("X-Request-ID", req_id)
    response.headers.setdefault("Server-Timing", f"app;dur={duration_ms:.1f}")
    logger.info(
        "%s %s -> %s in %.1fms rid=%s",
        request.method,
        request.url.path,
        status,
        duration_ms,
        req_id,
    )
    return response


# Consistent JSON error shapes
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # type: ignore[no-redef]
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[no-redef]
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "error": "Internal Server Error",
            "path": request.url.path,
        },
    )


# CORS: allow all in dev by default; allow configuring specific origins via env
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
_allow_origins = [o.strip() for o in _origins_env.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable gzip compression for larger responses
app.add_middleware(GZipMiddleware, minimum_size=500)

# Optionally mount Flask-based storage server under /storage via WSGI
try:
    from starlette.middleware.wsgi import WSGIMiddleware  # type: ignore

    try:
        if __package__:
            from .storage_server import create_storage_app  # type: ignore
        else:
            from storage_server import create_storage_app  # type: ignore
        _flask_app = create_storage_app()  # type: ignore[assignment]
        app.mount("/storage", WSGIMiddleware(_flask_app))  # type: ignore[arg-type]
    except Exception:
        # Flask not installed or failed to initialize; ignore silently
        pass
except Exception:
    pass

engine = RecoEngine()
try:
    from .notifier import send_alert  # type: ignore
except Exception:

    def send_alert(title: str, message: str, extra: Optional[Dict[str, Any]] = None) -> bool:  # type: ignore
        return False


# ---- Optional Edge integration (SensorReader) ----
# Allow importing the minimal edge module without extra setup by adding repo root to sys.path.
try:
    _BACKEND_DIR = os.path.dirname(__file__)
    _REPO_ROOT = os.path.abspath(os.path.join(_BACKEND_DIR, "..", ".."))
    if _REPO_ROOT not in sys.path:
        sys.path.append(_REPO_ROOT)
except Exception:
    _REPO_ROOT = None  # type: ignore[assignment]

try:
    # Import SensorReader and util from the edge module if available
    from agrisense_pi_edge_minimal.edge.reader import SensorReader  # type: ignore[reportMissingImports]
    from agrisense_pi_edge_minimal.edge.util import load_config  # type: ignore[reportMissingImports]

    _edge_available = True
except Exception:
    SensorReader = None  # type: ignore[assignment]
    load_config = None  # type: ignore[assignment]
    _edge_available = False

_edge_reader: Optional["SensorReader"] = None  # type: ignore[name-defined]


@runtime_checkable
class HasCropRecommender(Protocol):
    def get_crop_recommendations(
        self, sensor_data: Dict[str, Union[float, str]]
    ) -> Optional[List[Dict[str, Any]]]: ...


farming_system: Optional[HasCropRecommender] = (
    None  # lazy init to avoid longer cold start
)


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
    return {
        "status": "ready",
        "water_model": engine.water_model is not None,
        "fert_model": engine.fert_model is not None,
    }


# --- Admin protection helper ---
class AdminGuard:
    def __init__(self, env_var: str = "AGRISENSE_ADMIN_TOKEN") -> None:
        self.env_var = env_var

    def __call__(self, x_admin_token: Optional[str] = Header(default=None)) -> None:
        token = os.getenv(self.env_var)
        if not token:
            return  # no guard configured
        if not x_admin_token or x_admin_token != token:
            raise HTTPException(
                status_code=401, detail="Unauthorized: missing or invalid admin token"
            )


require_admin = AdminGuard()


@app.post("/admin/reset")
def admin_reset(_=Depends(require_admin)) -> Dict[str, bool]:
    """Erase all stored data. Irreversible."""
    reset_database()
    return {"ok": True}


@app.post("/admin/weather/refresh")
def admin_weather_refresh(
    lat: float = float(os.getenv("AGRISENSE_LAT", "27.3")),
    lon: float = float(os.getenv("AGRISENSE_LON", "88.6")),
    days: int = 7,
    cache_path: str = os.getenv("AGRISENSE_WEATHER_CACHE", "weather_cache.csv"),
) -> Dict[str, Any]:
    _ = require_admin()
    path = fetch_and_cache_weather(lat=lat, lon=lon, days=days, cache_path=cache_path)
    latest = read_latest_from_cache(path)
    return {"ok": True, "cache_path": str(path), "latest": latest}


@app.post("/admin/notify")
def admin_notify(
    title: str = "Test Alert",
    message: str = "This is a test notification.",
    _=Depends(require_admin),
) -> Dict[str, Any]:
    ok = send_alert(title, message)
    return {"ok": ok}


@app.get("/edge/health")
def edge_health() -> Dict[str, Any]:
    """Report basic availability of the optional Edge reader on the server.
    This does not require the edge API process; it uses the SensorReader class if present.
    """
    ok = bool(_edge_available)
    return {"status": "ok" if ok else "unavailable", "edge_module": _edge_available}


@app.post("/ingest")
def ingest(reading: SensorReading) -> Dict[str, bool]:
    insert_reading(reading.model_dump())
    return {"ok": True}


@app.post("/edge/capture")
def edge_capture(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Capture a reading using the local SensorReader (if available),
    ingest it, and return the reading with a fresh recommendation.
    Optional body: {"zone_id":"Z1"}
    """
    if not _edge_available:
        raise HTTPException(
            status_code=503, detail="Edge reader not available on server"
        )
    global _edge_reader
    if _edge_reader is None:
        # Load config via edge util; fallback to defaults
        cfg: Dict[str, Any] = {}
        try:
            if load_config is not None:
                cfg = load_config()  # type: ignore[misc]
        except Exception:
            cfg = {}
        try:
            _edge_reader = SensorReader(cfg)  # type: ignore[call-arg]
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to init edge reader: {e}"
            )

    zone_id = str((body or {}).get("zone_id", "Z1"))
    try:
        reading_raw = _edge_reader.capture(zone_id)  # type: ignore[union-attr]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edge capture failed: {e}")

    # Normalize to SensorReading model fields expected by our backend
    reading_map: Dict[str, Any] = {}
    if isinstance(reading_raw, dict):
        # trust shape and cast for typing
        reading_map = cast(Dict[str, Any], reading_raw)
    payload: Dict[str, Any] = {
        "zone_id": reading_map.get("zone_id", zone_id),
        "plant": reading_map.get("plant", "tomato"),
        "soil_type": reading_map.get("soil_type", "loam"),
        "area_m2": reading_map.get("area_m2", 120),
        "ph": reading_map.get("ph", 6.5),
        "moisture_pct": reading_map.get("moisture_pct", 35.0),
        "temperature_c": reading_map.get("temperature_c", 28.0),
        "ec_dS_m": reading_map.get("ec_dS_m", 1.0),
        "n_ppm": reading_map.get("n_ppm"),
        "p_ppm": reading_map.get("p_ppm"),
        "k_ppm": reading_map.get("k_ppm"),
    }
    # Validate through Pydantic
    reading = SensorReading.model_validate(payload)
    # Persist then compute rec
    insert_reading(reading.model_dump())
    rec: Dict[str, Any] = engine.recommend(reading.model_dump())
    return {"reading": reading.model_dump(), "recommendation": rec}


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
            insert_reco_snapshot(
                payload.get("zone_id", "Z1"),
                str(payload.get("plant", "generic")),
                rec,
                None,
            )
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


# --- Sikkim smart irrigation additions ---
class TankLevel(BaseModel):
    tank_id: str = "T1"
    level_pct: Optional[float] = None
    volume_l: Optional[float] = None
    rainfall_mm: Optional[float] = None


class TankStatus(BaseModel):
    tank_id: str
    level_pct: Optional[float] = None
    volume_l: Optional[float] = None
    last_update: Optional[str] = None


class IrrigationCommand(BaseModel):
    zone_id: str = "Z1"
    duration_s: Optional[int] = None  # required for start
    force: bool = False


class IrrigationAck(BaseModel):
    ok: bool
    status: str
    note: Optional[str] = None


class AlertItem(BaseModel):
    zone_id: str = "Z1"
    category: str
    message: str
    sent: bool = False


@app.post("/suggest_crop")
def suggest_crop(payload: Dict[str, Any]) -> SuggestCropResponse:
    """
    Suggest high-yield crops for a given soil type and optional conditions.
    Body example: {"soil_type": "loam", "ph": 6.8, "temperature": 25, "moisture": 60}
    """
    global farming_system
    if farming_system is None:
        # No-op recommender used when ML is disabled or unavailable
        class _NoopRecommender:
            def get_crop_recommendations(self, _):
                return []

        # Lazy-import the SmartFarmingRecommendationSystem to avoid heavy ML imports at app startup
        if os.getenv("AGRISENSE_DISABLE_ML"):
            farming_system = cast(HasCropRecommender, _NoopRecommender())
        else:
            # Import when ML is enabled
            import importlib

            try:
                sfm = importlib.import_module("agrisense_app.backend.smart_farming_ml")
            except Exception:
                try:
                    sfm = importlib.import_module("smart_farming_ml")
                except Exception:
                    sfm = None

            if sfm is None or not hasattr(sfm, "SmartFarmingRecommendationSystem"):
                farming_system = cast(HasCropRecommender, _NoopRecommender())
            else:
                SmartFarmingRecommendationSystem = getattr(
                    sfm, "SmartFarmingRecommendationSystem"
                )
                ds_override = os.getenv("AGRISENSE_DATASET") or os.getenv("DATASET_CSV")
                if ds_override:
                    farming_system = cast(
                        HasCropRecommender,
                        SmartFarmingRecommendationSystem(dataset_path=ds_override),
                    )
                else:
                    farming_system = cast(
                        HasCropRecommender, SmartFarmingRecommendationSystem()
                    )

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
        "temperature": float(
            payload.get("temperature", payload.get("temperature_c", 25))
        ),
        "water_level": float(payload.get("water_level", 500)),
        "moisture": float(payload.get("moisture", payload.get("moisture_pct", 60))),
        "humidity": float(payload.get("humidity", 70)),
        "soil_type": soil_ds,
    }
    # Typed via Protocol so Pylance understands shapes
    recs_raw: Optional[List[Dict[str, Any]]] = farming_system.get_crop_recommendations(sensor_data)  # type: ignore[reportUnknownMemberType]
    recs: List[CropSuggestion] = []
    for r in recs_raw or []:
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


# --- Tank and irrigation endpoints ---
@app.post("/tank/level")
def post_tank_level(body: TankLevel) -> Dict[str, bool]:
    insert_tank_level(
        body.tank_id,
        float(body.level_pct or 0.0),
        float(body.volume_l or 0.0),
        float(body.rainfall_mm or 0.0),
    )
    return {"ok": True}


@app.get("/tank/status")
def get_tank_status(tank_id: str = "T1") -> TankStatus:
    row = latest_tank_level(tank_id) or {}
    return TankStatus(
        tank_id=tank_id,
        level_pct=cast(Optional[float], row.get("level_pct")),
        volume_l=cast(Optional[float], row.get("volume_l")),
        last_update=cast(Optional[str], row.get("ts")),
    )


@app.get("/valves/events")
def get_valve_events(zone_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return {"items": recent_valve_events(zone_id, limit)}


def _has_water_for(liters: float) -> bool:
    row = latest_tank_level("T1")
    if not row:
        return True  # assume connected to mains
    try:
        vol = float(row.get("volume_l") or 0.0)
        return vol >= max(0.0, liters)
    except Exception:
        return True


try:
    from .mqtt_publish import publish_command  # type: ignore
except Exception:

    def publish_command(zone_id: str, payload: Dict[str, Any]) -> bool:  # type: ignore
        return False


@app.post("/irrigation/start")
def irrigation_start(cmd: IrrigationCommand) -> IrrigationAck:
    # Compute water need for zone and enforce tank constraint unless forced
    # Approximate: use last reading for zone if any; else default reading
    need: float = 20.0 * engine.defaults.get("area_m2", 100)  # fallback
    try:
        last = recent(cmd.zone_id, 1)
        if last:
            need = float(engine.recommend(last[0]).get("water_liters", need))
    except Exception:
        pass
    if not cmd.force and not _has_water_for(need):
        msg = f"Tank insufficient for planned irrigation: need ~{need:.0f} L"
        insert_alert(cmd.zone_id, "water_low", msg)
        try:
            send_alert(
                "Water low", msg, {"zone_id": cmd.zone_id, "need_l": round(need, 1)}
            )
        except Exception:
            pass
        log_valve_event(
            cmd.zone_id, "start", float(cmd.duration_s or 0), status="blocked"
        )
        return IrrigationAck(
            ok=False, status="blocked", note="Insufficient water in tank"
        )
    duration = int(
        cmd.duration_s or max(1, int(need / max(1e-6, engine.pump_flow_lpm)) * 60)
    )
    ok = publish_command(cmd.zone_id, {"action": "open", "duration_s": duration})
    log_valve_event(
        cmd.zone_id, "start", float(duration), status="sent" if ok else "queued"
    )
    try:
        send_alert(
            "Irrigation start",
            f"Zone {cmd.zone_id} for {duration}s",
            {"zone_id": cmd.zone_id, "duration_s": duration},
        )
    except Exception:
        pass
    return IrrigationAck(
        ok=ok, status="sent" if ok else "queued", note=f"Duration {duration}s"
    )


@app.post("/irrigation/stop")
def irrigation_stop(cmd: IrrigationCommand) -> IrrigationAck:
    ok = publish_command(cmd.zone_id, {"action": "close"})
    log_valve_event(cmd.zone_id, "stop", 0.0, status="sent" if ok else "queued")
    try:
        send_alert("Irrigation stop", f"Zone {cmd.zone_id}", {"zone_id": cmd.zone_id})
    except Exception:
        pass
    return IrrigationAck(ok=ok, status="sent" if ok else "queued")


@app.get("/alerts")
def get_alerts(zone_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return {"items": recent_alerts(zone_id, limit)}


@app.post("/alerts")
def post_alert(alert: AlertItem) -> Dict[str, bool]:
    insert_alert(alert.zone_id, alert.category, alert.message, alert.sent)
    return {"ok": True}


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
        slug = name.strip().lower().replace(" ", "_").replace("-", "_")
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
                    ph_range = (
                        f"{float(ph_min):.1f}-{float(ph_max):.1f}"
                        if ph_min and ph_max
                        else None
                    )
                except Exception:
                    ph_range = None
                try:
                    t_min = row.get("Temperature_Min_C")
                    t_max = row.get("Temperature_Max_C")
                    temp_range = (
                        f"{int(float(t_min))}-{int(float(t_max))}°C"
                        if t_min and t_max
                        else None
                    )
                except Exception:
                    temp_range = None
                try:
                    growth_days = row.get("Growth_Duration_days")
                    growth_period = (
                        f"{int(float(growth_days))} days" if growth_days else None
                    )
                except Exception:
                    growth_period = None
                try:
                    w_mm = row.get("Water_Requirement_mm")
                    water_req = _bucket_water_req(float(w_mm) if w_mm else None)
                except Exception:
                    water_req = None
                season = str(row.get("Growing_Season") or "").strip() or None

                slug = name.lower().replace(" ", "_").replace("-", "_")
                # Simple, category-based generic tips
                base_tips: Dict[str, List[str]] = {
                    "Cereal": [
                        "Ensure adequate nitrogen",
                        "Maintain consistent moisture",
                        "Plant within optimal temperature",
                    ],
                    "Vegetable": [
                        "Use well-drained soil",
                        "Water regularly",
                        "Monitor pests",
                    ],
                    "Oilseed": [
                        "Avoid waterlogging",
                        "Sunlight exposure is key",
                        "Balanced fertilization",
                    ],
                    "Pulse": [
                        "Rotate with cereals",
                        "Inoculate seeds if needed",
                        "Avoid excessive nitrogen",
                    ],
                    "Cash Crop": [
                        "Optimize irrigation",
                        "Fertilize per schedule",
                        "Scout for pests",
                    ],
                    "Spice": [
                        "Partial shade as needed",
                        "Mulch to retain moisture",
                        "Harvest at maturity",
                    ],
                    "Plantation": [
                        "Deep fertile soil",
                        "Regular irrigation",
                        "Nutrient management",
                    ],
                    "Tuber": [
                        "Loose, sandy loam soil",
                        "Avoid waterlogging",
                        "Hill soil as needed",
                    ],
                }
                tips = base_tips.get(
                    cat or "",
                    [
                        "Follow local best practices",
                        "Test soil pH",
                        "Irrigate as required",
                    ],
                )

                items.append(
                    CropCard(
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
                    )
                )
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
FRONTEND_DIST_NESTED = os.path.join(
    ROOT, "..", "frontend", "farm-fortune-frontend-main", "dist"
)
FRONTEND_DIST = os.path.join(ROOT, "..", "frontend", "dist")
FRONTEND_LEGACY = os.path.join(ROOT, "..", "frontend")
frontend_root: Optional[str] = None


class StaticFilesWithCache(StaticFiles):
    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)  # type: ignore[arg-type]
        # Apply cache headers to non-HTML assets; keep HTML short to allow quick updates
        try:
            # path like "assets/app.js" or "index.html"
            if isinstance(path, str) and not path.endswith(".html"):
                response.headers.setdefault(
                    "Cache-Control", "public, max-age=604800, immutable"
                )
            else:
                # cache for a minute for index.html to reduce flashing
                response.headers.setdefault("Cache-Control", "public, max-age=60")
        except Exception:
            pass
        return response


if os.path.isdir(FRONTEND_DIST_NESTED):
    frontend_root = FRONTEND_DIST_NESTED
    app.mount(
        "/ui",
        StaticFilesWithCache(directory=FRONTEND_DIST_NESTED, html=True),
        name="frontend",
    )
elif os.path.isdir(FRONTEND_DIST):
    frontend_root = FRONTEND_DIST
    app.mount(
        "/ui", StaticFilesWithCache(directory=FRONTEND_DIST, html=True), name="frontend"
    )
elif os.path.isdir(FRONTEND_LEGACY):
    frontend_root = FRONTEND_LEGACY
    app.mount(
        "/ui",
        StaticFilesWithCache(directory=FRONTEND_LEGACY, html=True),
        name="frontend",
    )


@app.get("/")
def root() -> RedirectResponse:
    # Redirect to the frontend so browsers request /ui/favicon.ico instead of /favicon.ico
    return RedirectResponse(url="/ui", status_code=307)


# SPA fallback so deep links like /ui/live or /ui/recommend render the app
# Admin protection helper is defined earlier above the admin endpoints.

# AdminGuard already defined earlier; duplicate definition removed to avoid name conflict.


# --- Lightweight metrics ---
@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    with _metrics_lock:
        out = dict(_metrics)
    # Compute uptime seconds on the fly
    out["uptime_s"] = round(time.time() - float(out.get("started_at", time.time())), 3)
    return out


@app.get("/version")
def version() -> Dict[str, Any]:
    return {"name": app.title, "version": app.version}


# --- Blueprint-stub endpoints (safe fallbacks returning not-implemented or graceful responses)
@app.post("/chat/ask")
def chat_ask(body: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Placeholder chat endpoint."""
    return JSONResponse(
        status_code=501,
        content={"error": "Not implemented", "message": "Chat service not configured"},
    )


@app.get("/chatbot/ask")
@app.post("/chatbot/ask")
def chatbot_ask(body: Optional[Dict[str, Any]] = None) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"error": "Not implemented", "message": "Chatbot not available"},
    )


@app.get("/chatbot/metrics")
def chatbot_metrics() -> Dict[str, Any]:
    return {"metrics": {}}


@app.post("/chatbot/reload")
def chatbot_reload() -> Dict[str, Any]:
    return {"ok": False, "reason": "not implemented"}


@app.post("/chatbot/tune")
def chatbot_tune(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"ok": False, "reason": "not implemented"}


try:
    from .disease_detection import analyze_image_fileobj, analyze_image_bytes  # type: ignore
except Exception:
    analyze_image_fileobj = None
    analyze_image_bytes = None


@app.post("/disease/detect")
async def detect_plant_disease(
    file: Optional[UploadFile] = File(None),
    image_b64: Optional[str] = Form(None),
) -> JSONResponse:
    """Accept an uploaded image file or a base64-encoded image in a multipart/form form field `image_b64`.
    Delegates to `agrisense_app.backend.disease_detection` scaffold which will lazy-load models when available.
    """
    # Uploaded file preferred
    if file is not None and analyze_image_fileobj is not None:
        try:
            result = analyze_image_fileobj(await file.read())
            return JSONResponse(status_code=200, content=result)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "inference_error", "message": str(e)},
            )

    # base64 form field handling (if present)
    if image_b64 and analyze_image_bytes is not None:
        try:
            import base64

            b = base64.b64decode(image_b64)
            result = analyze_image_bytes(b)
            return JSONResponse(status_code=200, content=result)
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "bad_request", "message": str(e)},
            )

    # No input or no model util available
    if analyze_image_fileobj is None and analyze_image_bytes is None:
        return JSONResponse(
            status_code=501,
            content={
                "ok": False,
                "error": "not_implemented",
                "message": "Disease detection scaffold not installed",
            },
        )

    return JSONResponse(
        status_code=400,
        content={
            "ok": False,
            "error": "no_input",
            "message": "Provide an image file or base64 image in `image_b64` form field",
        },
    )


@app.post("/weed/analyze")
def analyze_weeds(body: Optional[Dict[str, Any]] = None) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"error": "Not implemented", "message": "Weed analysis not available"},
    )


@app.get("/status/tensorflow-serving")
def tensorflow_serving_status() -> Dict[str, Any]:
    return {
        "available": False,
        "detail": "TensorFlow Serving integration not configured",
    }


@app.get("/status/websocket")
def websocket_status() -> Dict[str, Any]:
    return {"available": False}


@app.post("/health/assess")
def comprehensive_health_assessment(
    body: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not implemented",
            "message": "Comprehensive health assessment not available",
        },
    )


@app.get("/health/enhanced")
def enhanced_health() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not implemented",
            "message": "Enhanced health endpoint not available",
        },
    )


@app.get("/health/trends")
def get_health_trends() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"error": "Not implemented", "message": "Health trends not available"},
    )


@app.post("/rainwater/log")
def rainwater_log(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Reuse existing tank level insertion if provided
    try:
        if body and isinstance(body, dict):
            tank_id = str(body.get("tank_id", "T1"))
            level = float(body.get("level_pct", 0.0))
            vol = float(body.get("volume_l", 0.0))
            rain = float(body.get("rainfall_mm", 0.0))
            insert_tank_level(tank_id, level, vol, rain)
            return {"ok": True}
    except Exception:
        pass
    return {"ok": False, "reason": "invalid payload or not implemented"}


@app.get("/rainwater/recent")
def rainwater_recent_api() -> Dict[str, Any]:
    return {"items": []}


@app.get("/rainwater/summary")
def rainwater_summary_api() -> Dict[str, Any]:
    return {"summary": {}}


@app.get("/simple-metrics")
def get_simple_metrics() -> Dict[str, Any]:
    with _metrics_lock:
        return {
            "requests_total": _metrics.get("requests_total", 0),
            "errors_total": _metrics.get("errors_total", 0),
        }


@app.get("/soil/types")
def get_soil_types() -> Dict[str, Any]:
    # Provide a sensible default list; can be extended later
    return {"soil_types": ["loam", "sand", "clay", "sandy loam", "clay loam"]}


@app.get("/recommend/latest")
def iot_recommend_latest(zone_id: str = "Z1") -> Dict[str, Any]:
    # Return the most recent recommendation snapshot if any
    try:
        items = recent_reco(zone_id, 1)
        return {"item": items[0] if items else None}
    except Exception:
        return {"item": None}
