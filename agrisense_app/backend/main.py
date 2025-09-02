from fastapi import FastAPI, Request
from fastapi import Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi import HTTPException
from starlette.middleware.gzip import GZipMiddleware  # type: ignore
import logging
from pathlib import Path
from pathlib import Path
import time
import os
import sys
import csv
import json
import joblib
import numpy as np
import tensorflow as tf
import numpy as np
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
from pydantic import BaseModel, Field
from collections import OrderedDict
from . import llm_clients  # optional LLM reranker (Gemini/DeepSeek)

# Support running as a package (uvicorn backend.main:app) or as a module from backend folder (uvicorn main:app)
try:
    from .models import SensorReading, Recommendation
    from .engine import RecoEngine

    # Prefer MongoDB store when configured; fallback to SQLite store
    if os.getenv("AGRISENSE_DB", "sqlite").lower() in ("mongo", "mongodb"):
        from .data_store_mongo import (  # type: ignore
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
            rainwater_summary,
            insert_rainwater_entry,
            recent_rainwater,
            mark_alert_ack,
        )
    else:
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
            rainwater_summary,
            insert_rainwater_entry,
            recent_rainwater,
            mark_alert_ack,
        )
    from .smart_farming_ml import SmartFarmingRecommendationSystem
    from .weather import fetch_and_cache_weather, read_latest_from_cache
except ImportError:  # no parent package context
    from models import SensorReading, Recommendation
    from engine import RecoEngine

    if os.getenv("AGRISENSE_DB", "sqlite").lower() in ("mongo", "mongodb"):
        from data_store_mongo import (  # type: ignore
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
            rainwater_summary,
            insert_rainwater_entry,
            recent_rainwater,
            mark_alert_ack,
        )
    else:
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
            rainwater_summary,
            insert_rainwater_entry,
            recent_rainwater,
            mark_alert_ack,
        )
    from smart_farming_ml import SmartFarmingRecommendationSystem
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

# --- Admin protection helper (defined early to allow dependency use) ---


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
    # Augment recommendation with water source decision based on tank volume
    try:
        need_l = float(rec.get("water_liters", 0.0))
    except Exception:
        need_l = 0.0
    rec["water_source"] = _select_water_source(need_l)
    return {"reading": reading.model_dump(), "recommendation": rec}


@app.get("/recent")
def get_recent(zone_id: str = "Z1", limit: int = 50) -> Dict[str, Any]:
    return {"items": recent(zone_id, limit)}


@app.post("/recommend")
def recommend(reading: SensorReading, request: Request) -> Recommendation:
    # don't persist automatically; clients can call /ingest
    payload = reading.model_dump()
    rec: Dict[str, Any] = engine.recommend(payload)
    # Decide water source (tank vs groundwater) based on latest tank volume
    try:
        need_l = float(rec.get("water_liters", 0.0))
    except Exception:
        need_l = 0.0
    rec["water_source"] = _select_water_source(need_l)
    # Optionally send a recommendation alert
    if os.getenv("AGRISENSE_ALERT_ON_RECOMMEND", "0") not in (
        "0",
        "false",
        "False",
        "no",
    ):
        try:
            insert_alert(
                payload.get("zone_id", "Z1"),
                "RECOMMENDATION",
                f"Water {need_l:.0f} L, source {rec['water_source']}",
            )
            send_alert(
                "Recommendation",
                f"Water {need_l:.0f} L via {rec['water_source']}",
                {"zone_id": payload.get("zone_id", "Z1")},
            )
        except Exception:
            pass
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
    capacity_liters: Optional[float] = None


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
        # Initialize on first use, honor optional env var for dataset path
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
    level_pct = float(body.level_pct or 0.0)
    vol_l = float(body.volume_l or 0.0)
    insert_tank_level(body.tank_id, level_pct, vol_l, float(body.rainfall_mm or 0.0))
    # Low tank alert if below threshold
    try:
        low_thresh = float(
            os.getenv("AGRISENSE_TANK_LOW_PCT", os.getenv("TANK_LOW_PCT", "20"))
        )
        if level_pct > 0 and level_pct <= low_thresh:
            msg = f"Tank {body.tank_id} low: {level_pct:.1f}%"
            insert_alert("Z1", "LOW_TANK", msg)
            send_alert(
                "Tank low",
                msg,
                {"tank_id": body.tank_id, "level_pct": round(level_pct, 1)},
            )
    except Exception:
        pass
    return {"ok": True}


@app.get("/tank/status")
def get_tank_status(tank_id: str = "T1") -> TankStatus:
    row = latest_tank_level(tank_id) or {}
    return TankStatus(
        tank_id=tank_id,
        level_pct=cast(Optional[float], row.get("level_pct")),
        volume_l=cast(Optional[float], row.get("volume_l")),
        last_update=cast(Optional[str], row.get("ts")),
        capacity_liters=float(
            os.getenv("AGRISENSE_TANK_CAP_L", os.getenv("TANK_CAPACITY_L", "0")) or 0.0
        )
        or None,
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


def _select_water_source(required_liters: float) -> str:
    """Choose 'tank' if the latest tank volume can cover the required liters, else 'groundwater'.
    If no tank info is available, default to 'groundwater' only if requirement is zero; otherwise assume tank available.
    """
    row = latest_tank_level("T1")
    try:
        vol = float((row or {}).get("volume_l") or 0.0)
    except Exception:
        vol = 0.0
    if required_liters > 0 and vol >= required_liters:
        return "tank"
    return "groundwater"


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
    ok = publish_command(cmd.zone_id, {"action": "start", "duration_s": duration})
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
    ok = publish_command(cmd.zone_id, {"action": "stop"})
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
    # Use India dataset (46 crops) as primary for crop display; optionally merge Sikkim additions
    sikkim = os.path.join(ROOT, "..", "..", "sikkim_crop_dataset.csv")
    dataset_path = os.path.join(ROOT, "india_crop_dataset.csv")
    crops: List[Dict[str, Optional[str]]] = []
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Support India schema ("Crop") and Sikkim schema ("crop")
                    name = str((row.get("Crop") or row.get("crop") or "")).strip()
                    if name:
                        cat_raw = row.get("Crop_Category") or row.get("category")
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


@app.get("/soil/types")
def get_soil_types() -> Dict[str, Any]:
    """Expose available soil types from config for data-driven selection in UI."""
    try:
        soil_cfg = engine.cfg.get("soil", {})  # type: ignore[assignment]
        if isinstance(soil_cfg, dict) and soil_cfg:
            items = [str(k) for k in soil_cfg.keys()]
        else:
            items = ["sand", "loam", "clay"]
    except Exception:
        items = ["sand", "loam", "clay"]
    return {"items": items}


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
    tips: List[str] = Field(default_factory=list)


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
    sikkim = os.path.join(ROOT, "..", "..", "sikkim_crop_dataset.csv")
    dataset_path = os.path.join(ROOT, "india_crop_dataset.csv")
    items: List[CropCard] = []

    def _read_rows(path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except Exception:
            return []

    rows = _read_rows(dataset_path)
    # Optionally append Sikkim rows to enrich the catalog
    rows += _read_rows(sikkim)
    try:
        for row in rows:
            name = str((row.get("Crop") or row.get("crop") or "")).strip()
            if not name:
                continue
            cat = (
                str((row.get("Crop_Category") or row.get("category") or "")).strip()
                or None
            )
            try:
                ph_min = row.get("pH_Min") or row.get("ph_min")
                ph_max = row.get("pH_Max") or row.get("ph_max")
                ph_range = (
                    f"{float(ph_min):.1f}-{float(ph_max):.1f}"
                    if ph_min and ph_max
                    else None
                )
            except Exception:
                ph_range = None
            try:
                t_min = row.get("Temperature_Min_C") or row.get("temperature_min_c")
                t_max = row.get("Temperature_Max_C") or row.get("temperature_max_c")
                temp_range = (
                    f"{int(float(t_min))}-{int(float(t_max))}°C"
                    if t_min and t_max
                    else None
                )
            except Exception:
                temp_range = None
            try:
                growth_days = row.get("Growth_Duration_days") or row.get("growth_days")
                growth_period = (
                    f"{int(float(growth_days))} days" if growth_days else None
                )
            except Exception:
                growth_period = None
            try:
                w_mm = row.get("Water_Requirement_mm")
                if w_mm:
                    water_req = _bucket_water_req(float(w_mm))
                else:
                    w_lpm2 = row.get("water_need_l_per_m2")
                    if w_lpm2:
                        v = float(w_lpm2)
                        water_req = (
                            "Low" if v <= 5.0 else ("Medium" if v <= 7.0 else "High")
                        )
                    else:
                        water_req = None
            except Exception:
                water_req = None
            season = (
                str((row.get("Growing_Season") or row.get("season") or "")).strip()
                or None
            )

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
                ["Follow local best practices", "Test soil pH", "Irrigate as required"],
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


# --- Chatbot ---
class ChatRequest(BaseModel):
    message: str
    zone_id: str = "Z1"


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None


def _find_crop_card(name: str) -> Optional[CropCard]:
    nm = name.strip().lower().replace("-", " ")
    for c in _dataset_to_cards():
        if c.name.lower() == nm or c.id.lower() == nm or nm in c.name.lower():
            return c
    return None


def _normalize_simple(text: str) -> str:
    t = text.lower()
    t = "".join(ch if ch.isalnum() else " " for ch in t)
    # collapse spaces
    return " ".join(t.split())


def _find_crop_in_text(text: str) -> Optional[CropCard]:
    """Find best crop mention as a whole-word phrase in the text.
    Prefers longer names (e.g., 'green peas' over 'peas').
    """
    qnorm = f" {_normalize_simple(text)} "
    best: Optional[CropCard] = None
    best_len = -1
    for c in _dataset_to_cards():
        name_norm = f" {c.name.lower().replace('-', ' ')} "
        id_norm = f" {c.id.lower().replace('_', ' ')} "
        hit = False
        if name_norm in qnorm:
            hit = True
            cand_len = len(name_norm.strip())
        elif id_norm in qnorm:
            hit = True
            cand_len = len(id_norm.strip())
        else:
            cand_len = -1
        if hit and cand_len > best_len:
            best = c
            best_len = cand_len
    return best


def _format_reco(rec: Dict[str, Any]) -> str:
    parts: List[str] = []
    try:
        wl = rec.get("water_liters")
        if wl is not None:
            parts.append(f"Water ~{float(wl):.0f} L ({rec.get('water_source','tank')})")
    except Exception:
        pass
    for k, label in [("fert_n_g", "N"), ("fert_p_g", "P"), ("fert_k_g", "K")]:
        try:
            v = rec.get(k)
            if v is not None and float(v) > 0:
                parts.append(f"{label} {float(v):.0f} g")
        except Exception:
            pass
    if not parts:
        return "No immediate action required. Maintain regular monitoring."
    return "; ".join(parts)


@app.post("/chat/ask")
def chat_ask(req: ChatRequest) -> ChatResponse:
    q = req.message.strip()
    ql = q.lower()
    sources: List[str] = []

    # 1) If question mentions a crop, return its quick facts
    tokens = [w.strip("., ?!()[]{}\"'`").lower() for w in q.split()]
    crop_hit: Optional[CropCard] = None
    for w in tokens:
        c = _find_crop_card(w)
        if c is not None:
            crop_hit = c
            break
    if crop_hit is not None:
        ans = [
            f"Crop: {crop_hit.name}",
        ]
        if crop_hit.category:
            ans.append(f"Category: {crop_hit.category}")
        if crop_hit.season:
            ans.append(f"Season: {crop_hit.season}")
        if crop_hit.waterRequirement:
            ans.append(f"Water need: {crop_hit.waterRequirement}")
        if crop_hit.tempRange:
            ans.append(f"Temperature: {crop_hit.tempRange}")
        if crop_hit.phRange:
            ans.append(f"Soil pH: {crop_hit.phRange}")
        if crop_hit.growthPeriod:
            ans.append(f"Growth period: {crop_hit.growthPeriod}")
        if crop_hit.tips:
            ans.append("Tips: " + "; ".join(crop_hit.tips[:3]))
        sources.append("india_crop_dataset.csv (+ Sikkim additions if present)")
        return ChatResponse(answer="\n".join(ans), sources=sources)

    # 2) Irrigation / fertiliser intent -> use last reading and engine
    if any(
        k in ql
        for k in ["irrigat", "water", "moisture", "fert", "urea", "dap", "mop", "npk"]
    ):
        last = recent(req.zone_id, 1)
        base = last[0] if last else engine.defaults
        rec = engine.recommend(dict(base))
        # augment water source decision
        try:
            need_l = float(rec.get("water_liters", 0.0))
        except Exception:
            need_l = 0.0
        rec["water_source"] = _select_water_source(need_l)
        txt = _format_reco(rec)
        sources.extend(["latest reading", "engine.recommend"])
        return ChatResponse(answer=txt, sources=sources)

    # 3) Tank status intent
    if any(k in ql for k in ["tank", "storage", "reservoir", "cistern"]):
        row = latest_tank_level("T1") or {}
        pct = row.get("level_pct")
        vol = row.get("volume_l")
        if pct is None and vol is None:
            return ChatResponse(answer="No tank data available yet.")
        ans = (
            f"Tank level: {pct:.0f}%"
            if isinstance(pct, (int, float))
            else "Tank level: —"
        )
        if isinstance(vol, (int, float)) and vol > 0:
            ans += f", approx {vol:.0f} L"
        sources.append("tank_levels")
        return ChatResponse(answer=ans, sources=sources)

    # 4) Soil pH / EC generic guidance
    if "ph" in ql or "acidity" in ql:
        return ChatResponse(
            answer=(
                "Most crops prefer soil pH 6.0–7.5. If pH is low (<6), add lime; if high (>7.5), add elemental sulfur/organic matter."
            )
        )
    if "ec" in ql or "salinity" in ql:
        return ChatResponse(
            answer=(
                "EC ~1–2 dS/m is generally acceptable. High salinity reduces uptake—leach with good-quality water and improve drainage."
            )
        )

    # 5) Crop suggestion by soil type
    if "best crop" in ql or ("crop" in ql and "soil" in ql):
        # Try to detect simple soil words
        soil = next(
            (
                w
                for w in ["loam", "sandy", "clay", "sandy loam", "clay loam"]
                if w in ql
            ),
            "loam",
        )
        resp = suggest_crop({"soil_type": soil})
        top = (
            ", ".join([c.crop for c in resp.top[:3]])
            if resp.top
            else "(no suggestions)"
        )
        return ChatResponse(answer=f"For {resp.soil_type}: top crops could be {top}.")

    # Fallback
    return ChatResponse(
        answer=(
            "I can help with irrigation, fertilizer, crop info, tank status and soil guidance. Try: "
            "'How much water should I apply today?', 'Recommend NPK for my field', 'Tell me about rice', 'What is my tank level?'"
        )
    )


# --- Rainwater ledger ---
@app.post("/rainwater/log")
def rainwater_log(body: Dict[str, Any]) -> Dict[str, bool]:
    tank_id = str(body.get("tank_id", "T1"))
    collected = float(body.get("collected_liters") or 0.0)
    used = float(body.get("used_liters") or 0.0)
    insert_rainwater_entry(tank_id, collected, used)
    return {"ok": True}


@app.get("/rainwater/summary")
def rainwater_summary_api(tank_id: str = "T1") -> Dict[str, Any]:
    return rainwater_summary(tank_id)


@app.get("/rainwater/recent")
def rainwater_recent_api(tank_id: str = "T1", limit: int = 10) -> Dict[str, Any]:
    return {"items": recent_rainwater(tank_id, limit)}


# --- Alerts ack ---
@app.post("/alerts/ack")
def alerts_ack(body: Dict[str, Any]) -> Dict[str, bool]:
    ts = str(body.get("ts")) if body.get("ts") is not None else None
    if not ts:
        raise HTTPException(status_code=400, detail="ts required")
    mark_alert_ack(ts)
    return {"ok": True}


# Recommendation history endpoints for impact graphs
@app.get("/reco/recent")
def get_reco_recent(zone_id: str = "Z1", limit: int = 200) -> Dict[str, Any]:
    # recent_reco already returns all columns (including water_source if present)
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


# --- IoT compatibility shims ---
@app.get("/sensors/recent")
def iot_sensors_recent(zone_id: str = "Z1", limit: int = 10) -> List[Dict[str, Any]]:
    """Return recent sensor readings as a bare list, matching AGRISENSE_IoT expectations.
    Fields are adapted to the IoT schema: soil_moisture, temperature_c, ph, ec_dS_m, tank_percent, timestamp.
    """
    rows = recent(zone_id, limit)
    # Fetch latest tank level once
    tank = latest_tank_level("T1") or {}
    tank_pct = None
    try:
        tank_pct = float(tank.get("level_pct")) if tank.get("level_pct") is not None else None  # type: ignore[arg-type]
    except Exception:
        tank_pct = None
    out: List[Dict[str, Any]] = []
    for r in rows:
        item: Dict[str, Any] = {
            "timestamp": r.get("ts"),
            "soil_moisture": r.get("moisture_pct"),
            "temperature_c": r.get("temperature_c"),
            "ph": r.get("ph"),
            "ec_dS_m": r.get("ec_dS_m"),
            # Humidity isn't tracked in core readings; omit for now
            "tank_percent": tank_pct,
        }
        out.append(item)
    return out


@app.get("/recommend/latest")
def iot_recommend_latest(zone_id: str = "Z1") -> Dict[str, Any]:
    """Synthesize a latest recommendation document compatible with AGRISENSE_IoT frontend.
    Includes: irrigate, recommended_liters, water_source, and a human "notes" string.
    """
    rows = recent(zone_id, 1)
    if not rows:
        # No data yet; return a neutral recommendation
        src = _select_water_source(0.0)
        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "irrigate": False,
            "recommended_liters": 0.0,
            "water_source": src,
            "notes": "No sensor data yet",
        }
    last = dict(rows[0])
    rec = engine.recommend(last)
    try:
        need_l = float(rec.get("water_liters", 0.0))
    except Exception:
        need_l = 0.0
    src = _select_water_source(need_l)
    irrigate = need_l > 0.0
    note = "Soil dry, irrigate now" if irrigate else "Skip irrigation today"
    return {
        "timestamp": last.get("ts"),
        "irrigate": irrigate,
        "recommended_liters": need_l,
        "water_source": src,
        "notes": note,
    }


# --- ESP32 Edge ingest (HTTP) ---
@app.post("/edge/ingest")
def edge_ingest(payload: Dict[str, Any]) -> Dict[str, bool]:
    """Accept sensor payloads from ESP32 and normalize to SensorReading.
    Flexible keys supported:
      - soil_moisture or moisture_pct
      - temp_c or temperature_c
      - humidity (stored only for ML or future use; ignored for now)
      - ph
      - ec or ec_mScm (mS/cm). If provided in mS/cm, we convert to dS/m by dividing by 10.
      - tank_percent (0..100) and optional tank_id, tank_volume_l
    """
    zone = str(payload.get("zone_id", "Z1"))
    # Normalize moisture
    moisture = payload.get("moisture_pct")
    if moisture is None:
        m_alt1 = payload.get("soil_moisture")
        m_alt2 = payload.get("moisture") if m_alt1 is None else None
        try:
            moisture = float(m_alt1 if m_alt1 is not None else m_alt2)  # type: ignore[arg-type]
        except Exception:
            moisture = 35.0
    # Normalize temperature
    temp = payload.get("temperature_c")
    if temp is None:
        try:
            temp = float(payload.get("temp_c") or payload.get("temperature") or 28.0)
        except Exception:
            temp = 28.0
    # Normalize EC
    ec = payload.get("ec_dS_m")
    if ec is None:
        ec_ms1 = payload.get("ec_mScm")
        ec_ms2 = payload.get("ec") if ec_ms1 is None else None
        try:
            ec_val = float(ec_ms1 if ec_ms1 is not None else ec_ms2)  # type: ignore[arg-type]
            # Convert mS/cm to dS/m (1 mS/cm == 1 dS/m)
            ec = ec_val
        except Exception:
            ec = 1.0
    reading = SensorReading(
        zone_id=zone,
        plant=str(payload.get("plant", "generic")),
        soil_type=str(payload.get("soil_type", "loam")),
        area_m2=float(payload.get("area_m2", engine.defaults.get("area_m2", 100.0))),
        ph=float(payload.get("ph", 6.5)),
        moisture_pct=float(moisture),
        temperature_c=float(temp),
        ec_dS_m=float(ec),
        n_ppm=payload.get("n_ppm"),
        p_ppm=payload.get("p_ppm"),
        k_ppm=payload.get("k_ppm"),
    )
    insert_reading(reading.model_dump())
    # Optionally record tank level from edge
    tank_pct = payload.get("tank_percent")
    if tank_pct is not None:
        try:
            level_pct = float(tank_pct)
            tank_id = str(payload.get("tank_id", "T1"))
            vol_l = float(payload.get("tank_volume_l") or 0.0)
            insert_tank_level(
                tank_id, level_pct, vol_l, float(payload.get("rainfall_mm") or 0.0)
            )
        except Exception:
            pass
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
@app.get("/ui/{path:path}")
def serve_spa(path: str):
    if frontend_root:
        index_file = os.path.join(frontend_root, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="UI not found")


# Accept '/api/*' paths by redirecting to the same path without the '/api' prefix
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])  # type: ignore[list-item]
def api_prefix_redirect(path: str) -> RedirectResponse:
    # Preserve path and querystring; FastAPI/Starlette keeps query intact on redirect
    return RedirectResponse(url=f"/{path}", status_code=307)


## AdminGuard is defined near the top


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


# --------------- Chatbot Retrieval Endpoint -----------------
_chatbot_loaded = False
_chatbot_q_layer = None  # type: ignore
_chatbot_answers: Optional[List[str]] = None
_chatbot_emb: Optional[np.ndarray] = None
# Optional question-side index (improves matching user questions to known QA pairs)
_chatbot_q_emb: Optional[np.ndarray] = None
_chatbot_q_texts: Optional[List[str]] = None
_chatbot_q_tokens: Optional[List[Set[str]]] = None
_chatbot_qa_answers: Optional[List[str]] = None  # aligned to _chatbot_q_texts
_chatbot_cache: "OrderedDict[tuple[str, int], List[Dict[str, Any]]]" = OrderedDict()
_CHATBOT_CACHE_MAX = 64
_chatbot_answer_tokens: Optional[List[Set[str]]] = None
_chatbot_alpha: float = 0.7  # blend weight for embedding vs lexical
_chatbot_min_cos: float = 0.28  # fallback threshold for cosine similarity
_chatbot_metrics_cache: Optional[Dict[str, Any]] = None
_chatbot_lgbm_bundle: Optional[Dict[str, Any]] = (
    None  # {'model': lgb.Booster, 'vectorizer': TfidfVectorizer}
)
_chatbot_artifact_sig: Optional[Dict[str, float]] = None  # mtimes to detect changes


def _tokenize(text: str) -> Set[str]:
    try:
        t = text.lower()
        # keep alphanumerics and spaces
        t = "".join(ch if ch.isalnum() else " " for ch in t)
        raw = [w for w in t.split() if len(w) >= 3]
        norm: Set[str] = set()
        for w in raw:
            base = w
            # very light stemming: plural/tense normalization
            if base.endswith("es") and len(base) > 4:
                base = base[:-2]
            elif base.endswith("s") and len(base) > 3:
                base = base[:-1]
            elif base.endswith("ing") and len(base) > 5:
                base = base[:-3]
            elif base.endswith("ed") and len(base) > 4:
                base = base[:-2]
            norm.add(base)
        return norm
    except Exception:
        return set()


def _clean_text(text: str) -> str:
    try:
        # Fix common encoding artifacts like 'Â°C'
        return text.replace("Â°C", "°C").replace("Â", "").replace("\u00c2\u00b0C", "°C")
    except Exception:
        return text


def _artifact_signature(
    qenc_dir: Path, index_npz: Path, index_json: Path, metrics_path: Path
) -> Dict[str, float]:
    def mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except Exception:
            return 0.0

    # For SavedModel, use the saved_model.pb as freshness signal when present
    saved_pb = qenc_dir / "saved_model.pb"
    return {
        "qenc": mtime(saved_pb if saved_pb.exists() else qenc_dir),
        "npz": mtime(index_npz),
        "json": mtime(index_json),
        "metrics": mtime(metrics_path),
    }


def _load_chatbot_artifacts() -> bool:
    global _chatbot_loaded, _chatbot_q_layer, _chatbot_emb, _chatbot_answers, _chatbot_answer_tokens, _chatbot_alpha, _chatbot_min_cos, _chatbot_metrics_cache, _chatbot_artifact_sig, _chatbot_lgbm_bundle, _chatbot_q_emb, _chatbot_q_texts, _chatbot_q_tokens, _chatbot_qa_answers
    try:
        backend_dir = Path(__file__).resolve().parent
        qenc_dir = backend_dir / "chatbot_question_encoder"
        index_npz = backend_dir / "chatbot_index.npz"
        index_json = backend_dir / "chatbot_index.json"
    metrics_path = backend_dir / "chatbot_metrics.json"
    qindex_npz = backend_dir / "chatbot_q_index.npz"
    qa_pairs_json = backend_dir / "chatbot_qa_pairs.json"
        # If already loaded, only reload when artifacts changed on disk
    if _chatbot_loaded:
            try:
                sig_now = _artifact_signature(
                    qenc_dir, index_npz, index_json, metrics_path
                )
                if _chatbot_artifact_sig == sig_now:
                    return True
            except Exception:
                # if signature calc fails, fall through to attempt reload
                pass
        if not (qenc_dir.exists() and index_npz.exists() and index_json.exists()):
            logger.warning("Chatbot artifacts not found; skipping load.")
            return False
        # Load SavedModel endpoint via Keras TFSMLayer
        from tensorflow.keras.layers import TFSMLayer  # type: ignore

        _chatbot_q_layer = TFSMLayer(str(qenc_dir), call_endpoint="serve")
        with np.load(index_npz, allow_pickle=False) as data:
            arr = data["embeddings"]
        # L2-normalize answer embeddings to use cosine similarity robustly
        try:
            norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
            arr = arr / norms
        except Exception:
            pass
        _chatbot_emb = arr
        with open(index_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
    _chatbot_answers = list(meta.get("answers", []))
        # Pre-tokenize answers for lightweight lexical re-ranking
        _chatbot_answer_tokens = [_tokenize(a) for a in _chatbot_answers]
        # Optionally read metrics and tune blend/threshold
        try:
            if metrics_path.exists():
                with open(metrics_path, "r", encoding="utf-8") as mf:
                    _chatbot_metrics_cache = json.load(mf)
                r1 = float(
                    (_chatbot_metrics_cache or {}).get("val", {}).get("recall@1", 0.0)
                )
                # Adjust alpha and threshold based on quality
                if r1 >= 0.65:
                    _chatbot_alpha = 0.8
                    _chatbot_min_cos = 0.25
                elif r1 >= 0.5:
                    _chatbot_alpha = 0.7
                    _chatbot_min_cos = 0.27
                else:
                    # Low recall@1 -> lean more on lexical and higher threshold
                    _chatbot_alpha = 0.55
                    _chatbot_min_cos = 0.30
            # Tiny env overrides for manual tuning (optional)
            try:
                # Re-read .env to allow runtime tweaks without full restart
                try:
                    from dotenv import load_dotenv  # type: ignore

                    # Prefer a .env placed alongside backend artifacts
                    backend_env = Path(__file__).resolve().parent / ".env"
                    if backend_env.exists():
                        load_dotenv(dotenv_path=str(backend_env), override=True)
                    else:
                        load_dotenv(override=True)
                except Exception:
                    pass
                env_alpha = os.getenv("CHATBOT_ALPHA") or os.getenv(
                    "AGRISENSE_CHATBOT_ALPHA"
                )
                if env_alpha is not None and str(env_alpha).strip() != "":
                    _chatbot_alpha = float(env_alpha)
                    # clamp to safe range
                    _chatbot_alpha = max(0.0, min(1.0, _chatbot_alpha))
                env_min_cos = os.getenv("CHATBOT_MIN_COS") or os.getenv(
                    "AGRISENSE_CHATBOT_MIN_COS"
                )
                if env_min_cos is not None and str(env_min_cos).strip() != "":
                    _chatbot_min_cos = float(env_min_cos)
                    _chatbot_min_cos = max(0.0, min(1.0, _chatbot_min_cos))
            except Exception:
                # Non-fatal if env parsing fails
                pass
        except Exception:
            # Non-fatal
            pass
        # Optionally load LightGBM re-ranker bundle
        try:
            lgbm_path = backend_dir / "chatbot_lgbm_ranker.joblib"
            _chatbot_lgbm_bundle = None
            if lgbm_path.exists():
                _chatbot_lgbm_bundle = joblib.load(lgbm_path)
                logger.info("Loaded LightGBM re-ranker bundle")
        except Exception:
            _chatbot_lgbm_bundle = None
            logger.warning("Failed loading LightGBM bundle", exc_info=True)

        # Optional question-side index and QA mapping
        try:
            _chatbot_q_emb = None
            _chatbot_q_texts = None
            _chatbot_q_tokens = None
            _chatbot_qa_answers = None
            if qindex_npz.exists() and qa_pairs_json.exists():
                with np.load(qindex_npz, allow_pickle=False) as d:
                    qarr = d["embeddings"]
                    # ensure l2-normalized (safety)
                    try:
                        qarr = qarr / (np.linalg.norm(qarr, axis=1, keepdims=True) + 1e-12)
                    except Exception:
                        pass
                    _chatbot_q_emb = qarr
                with open(qa_pairs_json, "r", encoding="utf-8") as fqa:
                    qa_meta = json.load(fqa)
                qtexts = list(qa_meta.get("questions", []))
                aans = list(qa_meta.get("answers", []))
                if qtexts and aans and len(qtexts) == len(aans):
                    _chatbot_q_texts = qtexts
                    _chatbot_qa_answers = aans
                    _chatbot_q_tokens = [_tokenize(t) for t in qtexts]
                    logger.info("Loaded question index with %d QA pairs", len(qtexts))
        except Exception:
            _chatbot_q_emb = None
            _chatbot_q_texts = None
            _chatbot_q_tokens = None
            _chatbot_qa_answers = None
            logger.warning("Failed loading question index; will use answer index only", exc_info=True)

        _chatbot_loaded = True
        try:
            _chatbot_artifact_sig = _artifact_signature(
                qenc_dir, index_npz, index_json, metrics_path
            )
        except Exception:
            _chatbot_artifact_sig = None
    logger.info("Chatbot artifacts loaded: %d answers", len(_chatbot_answers or []))
        try:
            logger.info(
                "Chatbot tuning => alpha=%.3f, min_cos=%.3f",
                _chatbot_alpha,
                _chatbot_min_cos,
            )
        except Exception:
            pass
        return True
    except Exception:
        logger.exception("Failed to load chatbot artifacts")
        return False


class ChatbotQuery(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = 5


@app.post("/chatbot/ask")
def chatbot_ask(q: ChatbotQuery) -> Dict[str, Any]:
    ok = _load_chatbot_artifacts()
    if (
        not ok
        or _chatbot_q_layer is None
        or _chatbot_emb is None
        or _chatbot_answers is None
    ):
        raise HTTPException(
            status_code=503, detail="Chatbot not trained or artifacts missing"
        )
    # Normalize and validate input
    qtext = q.question.strip()
    if not qtext:
        raise HTTPException(status_code=400, detail="question must not be empty")
    topk = int(max(1, min(q.top_k, 20)))

    # LRU cache lookup
    key = (qtext, topk)
    if key in _chatbot_cache:
        results = _chatbot_cache.pop(key)
        _chatbot_cache[key] = results  # move to end (most recent)
        return {"question": qtext, "results": results}

    # If query mentions a known crop, return crop facts directly (better relevance)
    try:
        crop_hit: Optional[CropCard] = _find_crop_in_text(qtext)
        if crop_hit is not None:
            facts: List[str] = [f"Crop: {crop_hit.name}"]
            if crop_hit.category:
                facts.append(f"Category: {crop_hit.category}")
            if crop_hit.season:
                facts.append(f"Season: {crop_hit.season}")
            if crop_hit.waterRequirement:
                facts.append(f"Water need: {crop_hit.waterRequirement}")
            if crop_hit.tempRange:
                facts.append(f"Temperature: {crop_hit.tempRange}")
            if crop_hit.phRange:
                facts.append(f"Soil pH: {crop_hit.phRange}")
            if crop_hit.growthPeriod:
                facts.append(f"Growth period: {crop_hit.growthPeriod}")
            if crop_hit.tips:
                facts.append("Tips: " + "; ".join(crop_hit.tips[:3]))
            ans_txt = "\n".join(facts)
            results = [{"rank": 1, "score": 1.0, "answer": ans_txt}]
            _chatbot_cache[key] = results
            if len(_chatbot_cache) > _CHATBOT_CACHE_MAX:
                _chatbot_cache.popitem(last=False)
            return {"question": qtext, "results": results}
    except Exception:
        pass
    # Compute question embedding
    # SavedModel signature is positional-only (args_0) with name 'text' and dtype tf.string
    vec = _chatbot_q_layer(tf.constant([qtext], dtype=tf.string))
    if isinstance(vec, (list, tuple)):
        vec = vec[0]
    try:
        v = vec.numpy()[0]
    except Exception:
        v = np.array(vec)[0]
    # L2-normalize question vector for cosine similarity
    try:
        v = v / (np.linalg.norm(v) + 1e-12)
    except Exception:
        pass
    qtok = _tokenize(qtext)

    # Prefer question-index retrieval if available (match user question -> dataset question)
    use_qindex = _chatbot_q_emb is not None and _chatbot_q_texts is not None and _chatbot_qa_answers is not None
    reranked: List[tuple[int, float]] = []
    idx_source = "q" if use_qindex else "a"
    if use_qindex:
        qemb = cast(np.ndarray, _chatbot_q_emb)
        scores = qemb @ v
        pool = int(max(topk * 5, 50))
        cand_idx = scores.argsort()[::-1][: min(pool, scores.shape[0])]
        alpha = _chatbot_alpha
        beta = 1.0 - alpha
        q_tokens_list = _chatbot_q_tokens
        for j in cand_idx:
            sim = float(scores[j])
            overlap = 0.0
            if q_tokens_list is not None and qtok:
                inter = qtok.intersection(q_tokens_list[j])
                if qtok:
                    overlap = len(inter) / max(1.0, float(len(qtok)))
            blended = alpha * sim + beta * overlap
            reranked.append((j, blended))
        reranked.sort(key=lambda x: x[1], reverse=True)
    else:
        # Fallback: original answer-index retrieval
        emb: np.ndarray = cast(np.ndarray, _chatbot_emb)
        scores = emb @ v
        pool = int(max(topk * 5, 50))
        cand_idx = scores.argsort()[::-1][: min(pool, scores.shape[0])]
        alpha = _chatbot_alpha
        beta = 1.0 - alpha
        ans_tokens = _chatbot_answer_tokens
        for j in cand_idx:
            sim = float(scores[j])
            overlap = 0.0
            if ans_tokens is not None and qtok:
                inter = qtok.intersection(ans_tokens[j])
                if qtok:
                    overlap = len(inter) / max(1.0, float(len(qtok)))
            blended = alpha * sim + beta * overlap
            reranked.append((j, blended))
        reranked.sort(key=lambda x: x[1], reverse=True)
    # Optional LightGBM re-ranking on top candidates to refine order
    try:
        if _chatbot_lgbm_bundle and len(reranked) > 0:
            take = min(len(reranked), max(20, topk * 4))
            cand = reranked[:take]
            vec = _chatbot_lgbm_bundle.get("vectorizer")  # type: ignore[assignment]
            model = _chatbot_lgbm_bundle.get("model")  # type: ignore[assignment]
            if vec is not None and model is not None:
                q_arr = [qtext] * len(cand)
                cand_answers = [
                    cast(List[str], _chatbot_answers or [""])[j] for (j, _) in cand
                ]
                q_tf = vec.transform(q_arr)
                a_tf = vec.transform(cand_answers)
                cos_proxy = (q_tf.multiply(a_tf)).sum(axis=1)
                cos_proxy = np.asarray(cos_proxy).ravel().astype(np.float32)
                qtok_set = set(qtok)
                jac = np.array(
                    [
                        (
                            len(qtok_set & (ans_tokens[j] if ans_tokens else set()))
                            / max(
                                1,
                                len(
                                    qtok_set | (ans_tokens[j] if ans_tokens else set())
                                ),
                            )
                        )
                        for (j, _) in cand
                    ],
                    dtype=np.float32,
                )
                X = np.vstack([cos_proxy, jac]).T
                lgbm_scores = model.predict(X)
                # Mix with our blended score for final ordering
                # Normalize lgbm scores to 0..1
                lmin, lmax = float(np.min(lgbm_scores)), float(np.max(lgbm_scores))
                lnorm = (lgbm_scores - lmin) / (lmax - lmin + 1e-9)
                merged = [
                    (j, 0.85 * s + 0.15 * float(lnorm[i]))
                    for i, (j, s) in enumerate(cand)
                ]
                merged.sort(key=lambda x: x[1], reverse=True)
                reranked = merged
    except Exception:
        logger.warning("LightGBM re-rank failed; keep blended order", exc_info=True)

    idx = [j for (j, s) in reranked[:topk]]
    if idx_source == "q":
        qa_answers = cast(List[str], _chatbot_qa_answers or [])
        results = [
            {"rank": i + 1, "score": float(scores[j]), "answer": qa_answers[j]}
            for i, j in enumerate(idx)
        ]
    else:
        results = [
            {"rank": i + 1, "score": float(scores[j]), "answer": _chatbot_answers[j]}
            for i, j in enumerate(idx)
        ]
    # Optional LLM re-ranking of top few results (controlled by env keys)
    try:
        if results and (os.getenv("GEMINI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
            # Allow env overrides to tune how many candidates to pass to LLM and how much to blend
            try:
                MAX_LLM_RERANK = int(os.getenv("CHATBOT_LLM_RERANK_TOPN") or 5)
            except Exception:
                MAX_LLM_RERANK = 5
            MAX_LLM_RERANK = max(1, min(25, MAX_LLM_RERANK))
            try:
                LLM_BLEND = float(os.getenv("CHATBOT_LLM_BLEND") or 0.10)
            except Exception:
                LLM_BLEND = 0.10
            LLM_BLEND = max(0.0, min(0.5, LLM_BLEND))
            subset = results[:MAX_LLM_RERANK]
            cand_answers = [r["answer"] for r in subset]
            llm_scores = llm_clients.llm_rerank(qtext, cand_answers)
            if llm_scores:
                for i, sc in enumerate(llm_scores):
                    subset[i]["score"] = (subset[i]["score"] * (1.0 - LLM_BLEND)) + (
                        float(sc) * LLM_BLEND
                    )
                # resort only the subset
                subset.sort(key=lambda r: r["score"], reverse=True)
                results = subset + results[MAX_LLM_RERANK:]
    except Exception:
        # Non-fatal if LLM errors occur
        pass
    # Add a gentle note if the top cosine similarity is below our threshold
    try:
        if results:
            top_cos = float(scores[idx[0]]) if idx else 0.0
            if top_cos < _chatbot_min_cos:
                results[0]["answer"] = (
                    "Note: confidence is low; results may be off. Try rephrasing or add details.\n\n"
                    + str(results[0]["answer"])
                )
    except Exception:
        pass
    # Update LRU cache
    _chatbot_cache[key] = results
    if len(_chatbot_cache) > _CHATBOT_CACHE_MAX:
        _chatbot_cache.popitem(last=False)
    return {"question": qtext, "results": results}


@app.get("/chatbot/metrics")
def chatbot_metrics() -> Dict[str, Any]:
    """Return saved evaluation metrics (e.g., Recall@K) if available."""
    try:
        backend_dir = Path(__file__).resolve().parent
        metrics_path = backend_dir / "chatbot_metrics.json"
        if not metrics_path.exists():
            raise HTTPException(status_code=404, detail="metrics not found")
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"metrics": data}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to read chatbot metrics")
        raise HTTPException(status_code=500, detail="failed to read metrics")


@app.post("/chatbot/reload")
def chatbot_reload(_: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Force reload of chatbot artifacts from disk (after retraining)."""
    global _chatbot_loaded, _chatbot_q_layer, _chatbot_emb, _chatbot_answers, _chatbot_answer_tokens, _chatbot_metrics_cache, _chatbot_artifact_sig, _chatbot_cache
    # Clear current state
    _chatbot_loaded = False
    _chatbot_q_layer = None
    _chatbot_emb = None
    _chatbot_answers = None
    _chatbot_answer_tokens = None
    _chatbot_metrics_cache = None
    _chatbot_artifact_sig = None
    _chatbot_cache.clear()
    ok = _load_chatbot_artifacts()
    return {
        "ok": bool(ok),
        "answers": len(_chatbot_answers or []),
        "alpha": _chatbot_alpha,
        "min_cos": _chatbot_min_cos,
    }
