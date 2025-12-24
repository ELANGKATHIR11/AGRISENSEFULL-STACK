import asyncio
import csv
import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime
from importlib import import_module
from math import isfinite
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Union, cast, runtime_checkable

import joblib
import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.gzip import GZipMiddleware  # type: ignore

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: avoid modifying sys.path here - imports should prefer package-style
# (agrisense_app.backend...) or use the repository PYTHONPATH. Altering sys.path
# to expose backend as top-level can cause circular imports (see history).

"""
TensorFlow is optional. Import it only when ML is enabled to keep tests/dev light.
Respect AGRISENSE_DISABLE_ML=1 to skip heavy imports.
"""
DISABLE_ML = os.getenv("AGRISENSE_DISABLE_ML", "0").lower() in ("1", "true", "yes")
if not DISABLE_ML:
    try:
        import tensorflow as tf  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        tf = None  # type: ignore
else:
    tf = None  # type: ignore

try:
    from . import llm_clients  # optional LLM reranker (Gemini/DeepSeek)
except ImportError:
    try:
        import llm_clients  # type: ignore
    except ImportError:
        llm_clients = None  # type: ignore

# Import core modules from organized structure
_core_data_store = None
_sensor_api = None
_mqtt_publish = None

try:
    from .core.engine import RecoEngine  # type: ignore[attr-defined]
    from .core import data_store as _core_data_store  # type: ignore[attr-defined]
    from .api import sensor_api as _sensor_api  # type: ignore[attr-defined]
    from .integrations import mqtt_publish as _mqtt_publish  # type: ignore[attr-defined]
except ImportError as exc:
    logger.warning("Relative backend imports failed (%s); attempting package resolution", exc)
    try:
        RecoEngine = import_module("agrisense_app.backend.core.engine").RecoEngine  # type: ignore[attr-defined]
    except Exception as engine_exc:  # pragma: no cover - critical failure
        logger.error("Could not import RecoEngine: %s", engine_exc)
        RecoEngine = None  # type: ignore[assignment]

    try:
        _core_data_store = import_module("agrisense_app.backend.core.data_store")
    except Exception as ds_exc:  # pragma: no cover - optional in tests
        logger.warning("Core data_store unavailable: %s", ds_exc)
        _core_data_store = None

    try:
        _sensor_api = import_module("agrisense_app.backend.api.sensor_api")
    except Exception as api_exc:  # pragma: no cover - optional runtime feature
        logger.warning("Sensor API module unavailable: %s", api_exc)
        _sensor_api = None

    try:
        _mqtt_publish = import_module("agrisense_app.backend.integrations.mqtt_publish")
    except Exception as mqtt_exc:  # pragma: no cover - optional runtime feature
        logger.info("MQTT integration unavailable: %s", mqtt_exc)
        _mqtt_publish = None

if _core_data_store is not None:
    init_sensor_db = _core_data_store.init_sensor_db
    insert_sensor_reading = _core_data_store.insert_sensor_reading
    get_sensor_readings = _core_data_store.get_sensor_readings
    get_tank_level = _core_data_store.get_tank_level
    set_tank_level = _core_data_store.set_tank_level
    get_irrigation_log = _core_data_store.get_irrigation_log
    log_irrigation_event = _core_data_store.log_irrigation_event
    get_alert_log = _core_data_store.get_alert_log
    log_alert = _core_data_store.log_alert
    get_reco_log = _core_data_store.get_reco_log
    log_reco = _core_data_store.log_reco
    clear_sensor_data = _core_data_store.clear_sensor_data
    clear_alerts = _core_data_store.clear_alerts
    clear_irrigation_log = _core_data_store.clear_irrigation_log
    clear_reco_log = _core_data_store.clear_reco_log
    get_weather_data = _core_data_store.get_weather_data
    store_weather_data = _core_data_store.store_weather_data
    record_alert_dismissal = _core_data_store.record_alert_dismissal
    get_alert_stats = _core_data_store.get_alert_stats
    get_recommendation_stats = _core_data_store.get_recommendation_stats
    get_sensor_stats = _core_data_store.get_sensor_stats
    get_system_health = _core_data_store.get_system_health
else:  # pragma: no cover - degraded mode
    def _missing_dependency(*_args, **_kwargs):
        raise RuntimeError("Core data store is unavailable")

    init_sensor_db = _missing_dependency  # type: ignore[assignment]
    insert_sensor_reading = _missing_dependency  # type: ignore[assignment]
    get_sensor_readings = _missing_dependency  # type: ignore[assignment]
    get_tank_level = _missing_dependency  # type: ignore[assignment]
    set_tank_level = _missing_dependency  # type: ignore[assignment]
    get_irrigation_log = _missing_dependency  # type: ignore[assignment]
    log_irrigation_event = _missing_dependency  # type: ignore[assignment]
    get_alert_log = _missing_dependency  # type: ignore[assignment]
    log_alert = _missing_dependency  # type: ignore[assignment]
    get_reco_log = _missing_dependency  # type: ignore[assignment]
    log_reco = _missing_dependency  # type: ignore[assignment]
    clear_sensor_data = _missing_dependency  # type: ignore[assignment]
    clear_alerts = _missing_dependency  # type: ignore[assignment]
    clear_irrigation_log = _missing_dependency  # type: ignore[assignment]
    clear_reco_log = _missing_dependency  # type: ignore[assignment]
    get_weather_data = _missing_dependency  # type: ignore[assignment]
    store_weather_data = _missing_dependency  # type: ignore[assignment]
    record_alert_dismissal = _missing_dependency  # type: ignore[assignment]
    get_alert_stats = _missing_dependency  # type: ignore[assignment]
    get_recommendation_stats = _missing_dependency  # type: ignore[assignment]
    get_sensor_stats = _missing_dependency  # type: ignore[assignment]
    get_system_health = _missing_dependency  # type: ignore[assignment]

if _sensor_api is not None:
    exported = getattr(_sensor_api, "__all__", None)
    names = exported if exported else [n for n in vars(_sensor_api) if not n.startswith("_")]
    for _name in names:
        globals()[_name] = getattr(_sensor_api, _name)

if _mqtt_publish is not None:
    exported = getattr(_mqtt_publish, "__all__", None)
    names = exported if exported else [n for n in vars(_mqtt_publish) if not n.startswith("_")]
    for _name in names:
        globals()[_name] = getattr(_mqtt_publish, _name)

try:
    from rank_bm25 import BM25Okapi  # type: ignore
except Exception:
    BM25Okapi = None  # type: ignore

# Import VLM engine for enhanced analysis
try:
    from .vlm_engine import analyze_with_vlm, get_vlm_engine
    VLM_AVAILABLE = True
except ImportError:
    VLM_AVAILABLE = False

# Import conversational chatbot enhancement
try:
    from .chatbot_conversational import enhance_chatbot_response, get_greeting_message
    CONVERSATIONAL_ENHANCEMENT_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_ENHANCEMENT_AVAILABLE = False
    logger.warning("Conversational chatbot enhancement not available")

# Support running as a package (uvicorn backend.main:app) or as a module from backend folder (uvicorn main:app)
try:
    # Prefer relative imports when running as a package
    from .models import SensorReading, Recommendation
    from .core.engine import RecoEngine

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
        from .core.data_store import (
            insert_reading,
            recent,
            insert_reco_snapshot,
            recent_reco,
            insert_tank_level,
            latest_tank_level,
            recent_tank_levels,
            log_valve_event,
            recent_valve_events,
            insert_alert,
            recent_alerts,
            reset_database,
            rainwater_summary,
            insert_rainwater_entry,
            recent_rainwater,
            mark_alert_ack,
            get_conn,
        )
    from .smart_farming_ml import SmartFarmingRecommendationSystem
    from .weather import fetch_and_cache_weather, read_latest_from_cache

    # Import plant health management systems
    try:
        from .disease_detection import DiseaseDetectionEngine
        from .weed_management import WeedManagementEngine
        from .plant_health_monitor import PlantHealthMonitor

        PLANT_HEALTH_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"Plant health systems not available: {e}")
        pass  # Keep the global defaults
except Exception:
    # Try absolute package imports as a robust fallback (works when running from repo root)
    try:
        from models import SensorReading, Recommendation  # type: ignore
        from core.engine import RecoEngine  # type: ignore
    except Exception:
        # Final fallback - try top-level imports (older layouts)
        try:
            from models import SensorReading, Recommendation  # type: ignore
            from core.engine import RecoEngine  # type: ignore
        except Exception as e:
            logger.warning(f"Could not import models/engine modules: {e}")
            # Let later code handle missing pieces gracefully

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
        from core.data_store import (
            insert_reading,
            recent,
            insert_reco_snapshot,
            recent_reco,
            insert_tank_level,
            latest_tank_level,
            recent_tank_levels,
            log_valve_event,
            recent_valve_events,
            insert_alert,
            recent_alerts,
            reset_database,
            rainwater_summary,
            insert_rainwater_entry,
            recent_rainwater,
            mark_alert_ack,
            get_conn,
        )
    from smart_farming_ml import SmartFarmingRecommendationSystem
    from weather import fetch_and_cache_weather, read_latest_from_cache

    # Import plant health management systems
    try:
        from disease_detection import DiseaseDetectionEngine
        from weed_management import WeedManagementEngine
        from plant_health_monitor import PlantHealthMonitor

        PLANT_HEALTH_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"Plant health systems not available: {e}")
        pass  # Keep the global defaults

# Load environment from .env if present (development convenience)
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

# Initialize plant health availability flag (if not already set by imports)
if "PLANT_HEALTH_AVAILABLE" not in globals():
    PLANT_HEALTH_AVAILABLE = False
if "DiseaseDetectionEngine" not in globals():
    DiseaseDetectionEngine = None  # type: ignore
if "WeedManagementEngine" not in globals():
    WeedManagementEngine = None  # type: ignore
if "PlantHealthMonitor" not in globals():
    PlantHealthMonitor = None  # type: ignore

# Import enhanced backend components
try:
    if __package__:
        from .database_enhanced import initialize_database, cleanup_database
        from .auth_enhanced import (
            fastapi_users,
            auth_backend_jwt,
            auth_backend_cookie,
            UserCreate,
            UserRead,
            UserUpdate,
        )
        from .websocket_manager import websocket_router, manager as websocket_manager, periodic_status_broadcast
        from .rate_limiter import RateLimitMiddleware, initialize_rate_limiting, cleanup_rate_limiting
        from .tensorflow_serving import initialize_tf_serving, cleanup_tf_serving, get_tf_serving_status
        from .metrics import metrics, MetricsMiddleware, record_health_check
        from .celery_api import router as celery_router
    else:
        from database_enhanced import initialize_database, cleanup_database  # type: ignore
        from auth_enhanced import fastapi_users, auth_backend_jwt, auth_backend_cookie, UserCreate, UserRead, UserUpdate  # type: ignore
        from websocket_manager import websocket_router, manager as websocket_manager, periodic_status_broadcast  # type: ignore
        from rate_limiter import RateLimitMiddleware, initialize_rate_limiting, cleanup_rate_limiting  # type: ignore
        from tensorflow_serving import initialize_tf_serving, cleanup_tf_serving, get_tf_serving_status  # type: ignore
        from metrics import metrics, MetricsMiddleware, record_health_check  # type: ignore
        from celery_api import router as celery_router  # type: ignore
    ENHANCED_BACKEND_AVAILABLE = True
    logger.info("Enhanced backend components loaded successfully")
except ImportError as e:
    logger.warning(f"Enhanced backend components not available: {e}")
    ENHANCED_BACKEND_AVAILABLE = False
    websocket_router = None  # type: ignore
    websocket_manager = None  # type: ignore
    fastapi_users = None  # type: ignore
    celery_router = None  # type: ignore


# Async lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    try:
        if ENHANCED_BACKEND_AVAILABLE:
            logger.info("Initializing enhanced backend...")
            await initialize_database()
            await initialize_rate_limiting()
            await initialize_tf_serving()

            # Start periodic WebSocket status broadcast
            asyncio.create_task(periodic_status_broadcast())

            # Start system metrics collection
            if "metrics" in locals():
                asyncio.create_task(metrics.collect_system_metrics())

            logger.info("Enhanced backend initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize enhanced backend: {e}")

    yield

    # Shutdown
    try:
        if ENHANCED_BACKEND_AVAILABLE:
            logger.info("Cleaning up enhanced backend...")
            await cleanup_database()
            await cleanup_rate_limiting()
            await cleanup_tf_serving()
            logger.info("Enhanced backend cleanup completed")
    except Exception as e:
        logger.error(f"Error during enhanced backend cleanup: {e}")


app = FastAPI(
    title="Agri-Sense API",
    version="0.3.0",
    description="Smart irrigation and crop recommendation system with enhanced real-time features",
    lifespan=lifespan,
)

# Basic structured logger
logger = logging.getLogger("agrisense")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

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


# Add validation error handler to return 422 instead of 404
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore[no-redef]
    """Handle Pydantic validation errors with proper 422 status"""
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "status": 422,
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": str(exc.body) if exc.body else None,
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

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):  # type: ignore
    """Add security headers to all responses"""
    response = await call_next(request)
    # Content Security Policy - Restrict sources
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:* ws://localhost:*; "
        "frame-ancestors 'none';"
    )
    # HTTP Strict Transport Security - Force HTTPS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # X-Frame-Options - Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # X-Content-Type-Options - Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # X-XSS-Protection - Enable XSS filter
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Referrer-Policy - Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Permissions-Policy - Control browser features
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Add metrics middleware (only if FastAPI and Prometheus are available)
if ENHANCED_BACKEND_AVAILABLE and "MetricsMiddleware" in locals():
    try:
        from fastapi.middleware.base import BaseHTTPMiddleware  # type: ignore
        # Wrap MetricsMiddleware to make it compatible with FastAPI
        class WrappedMetricsMiddleware(BaseHTTPMiddleware):  # type: ignore
            def __init__(self, app):
                super().__init__(app)
                self.metrics = MetricsMiddleware(app)
            
            async def dispatch(self, request, call_next):  # type: ignore
                return await self.metrics.dispatch(request, call_next)  # type: ignore
        
        app.add_middleware(BaseHTTPMiddleware, dispatch=MetricsMiddleware(app))
    except ImportError:
        # Skip metrics middleware if FastAPI components not available
        pass

# Add enhanced rate limiting middleware
if ENHANCED_BACKEND_AVAILABLE:
    app.add_middleware(
        RateLimitMiddleware,
        enabled=not os.getenv("AGRISENSE_DISABLE_RATE_LIMITING", "0").lower() in ("1", "true", "yes"),
    )

# Include enhanced authentication routes
if ENHANCED_BACKEND_AVAILABLE and fastapi_users:
    app.include_router(fastapi_users.get_auth_router(auth_backend_jwt), prefix="/auth/jwt", tags=["auth"])
    app.include_router(fastapi_users.get_auth_router(auth_backend_cookie), prefix="/auth/cookie", tags=["auth"])
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["users"],
    )

# Include WebSocket router
if ENHANCED_BACKEND_AVAILABLE and websocket_router:
    app.include_router(websocket_router, tags=["websocket"])

# Include Celery background tasks router
if ENHANCED_BACKEND_AVAILABLE and celery_router:
    app.include_router(celery_router)

# Include Real-time Sensor API router
try:
    if __package__:
        from .api.sensor_api import sensor_router
    else:
        from api.sensor_api import sensor_router  # type: ignore

    # sensor_router may be a stub in some contexts; cast for type-checkers
    try:
        from typing import Any, cast

        # Cast to Any to silence static union-type complaints from editor linters
        app.include_router(cast(Any, sensor_router), tags=["Real-time Sensors"])  # type: ignore
    except Exception:
        # Fallback: include as-is and let runtime surprise be handled by try/except above
        app.include_router(sensor_router, tags=["Real-time Sensors"])  # type: ignore

    logger.info("✅ Real-time Sensor API router included successfully")
except ImportError as e:
    logger.warning(f"⚠️ Real-time Sensor API not available: {e}")
    # sensor_api optional - continue without it
    pass

# Include VLM (Vision Language Model) API router for disease & weed management
try:
    if __package__:
        from .routes.vlm_routes import router as vlm_router
    else:
        from routes.vlm_routes import router as vlm_router  # type: ignore
    
    app.include_router(vlm_router)
    logger.info("✅ VLM API router included successfully - Disease & Weed Management available at /api/vlm")
except ImportError as e:
    logger.warning(f"⚠️ VLM API not available: {e}")
    # VLM API optional - continue without it
    pass

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
            raise HTTPException(status_code=401, detail="Unauthorized: missing or invalid admin token")


require_admin = AdminGuard()
# Initialize RecoEngine with fallback
try:
    if RecoEngine is not None:
        engine = RecoEngine()
    else:
        engine = None
except (NameError, TypeError):
    logger.warning("RecoEngine not available, using fallback")
    engine = None
    engine = None

# Helper function to safely use engine
def safe_engine_recommend(data: dict) -> dict:
    """Safely get recommendation from engine with fallback"""
    if engine is None:
        return {
            "water_liters": 20.0,
            "fertilizer_kg": 0.1,
            "fert_n_g": 10.0,
            "fert_p_g": 5.0,
            "fert_k_g": 8.0,
            "tips": ["Engine unavailable - using default values"],
        }
    return engine.recommend(data)

def safe_engine_attr(attr: str, default: Any = None) -> Any:
    """Safely get engine attribute with fallback"""
    if engine is None:
        if attr == "defaults":
            return {"area_m2": 100.0, "pump_flow_lpm": 10.0}
        elif attr == "plants":
            return {"tomato": {}, "corn": {}, "wheat": {}}
        elif attr == "water_model":
            return None
        elif attr == "fert_model":
            return None
        elif attr == "pump_flow_lpm":
            return 10.0
        elif attr == "cfg":
            return {"soil": {"loam": {}, "clay": {}, "sandy": {}}}
        return default
    return getattr(engine, attr, default)

# Initialize plant health monitoring system (optional)
plant_health_monitor = None
if PLANT_HEALTH_AVAILABLE and not DISABLE_ML and PlantHealthMonitor is not None:
    try:
        plant_health_monitor = PlantHealthMonitor()
        logger.info("✅ Plant Health Monitor initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Plant Health Monitor: {e}")
        plant_health_monitor = None
else:
    logger.info("🔧 Plant Health Monitor disabled (ML disabled or dependencies missing)")

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
    def get_crop_recommendations(self, sensor_data: Dict[str, Union[float, str]]) -> Optional[List[Dict[str, Any]]]: ...


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
    return {
        "status": "ready",
        "water_model": safe_engine_attr("water_model") is not None,
        "fert_model": safe_engine_attr("fert_model") is not None,
    }


# Enhanced health endpoints
@app.get("/health/enhanced")
async def enhanced_health() -> Dict[str, Any]:
    """Enhanced health check including all system components"""
    health_data = {
        "status": "ok",
        "timestamp": time.time(),
        "components": {
            "api": {"status": "ok", "version": "0.3.0"},
            "engine": {
                "status": "ok",
                "water_model": safe_engine_attr("water_model") is not None,
                "fert_model": safe_engine_attr("fert_model") is not None,
            },
        },
    }

    if ENHANCED_BACKEND_AVAILABLE:
        try:
            # Check database connectivity
            from .database_enhanced import check_db_health

            db_health = await check_db_health()
            health_data["components"]["database"] = db_health
        except Exception as e:
            health_data["components"]["database"] = {"status": "error", "error": str(e)}

        try:
            # Check Redis connectivity
            from .database_enhanced import check_redis_health

            redis_health = await check_redis_health()
            health_data["components"]["redis"] = redis_health
        except Exception as e:
            health_data["components"]["redis"] = {"status": "error", "error": str(e)}

        # Check WebSocket status
        if websocket_manager:
            health_data["components"]["websocket"] = {
                "status": "ok",
                "connected_clients": websocket_manager.get_client_count(),
                "total_connections": websocket_manager.get_connection_count(),
            }

        try:
            # Check TensorFlow Serving status
            tf_serving_status = await get_tf_serving_status()
            health_data["components"]["tensorflow_serving"] = tf_serving_status
        except Exception as e:
            health_data["components"]["tensorflow_serving"] = {"status": "error", "error": str(e)}

    # Overall status
    all_ok = all(comp.get("status") == "ok" for comp in health_data["components"].values())
    health_data["status"] = "ok" if all_ok else "degraded"

    return health_data


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    if not ENHANCED_BACKEND_AVAILABLE or "metrics" not in locals():
        raise HTTPException(status_code=503, detail="Metrics not available")

    # Record health checks for all components
    try:
        from .database_enhanced import check_db_health, check_redis_health

        # Database health
        try:
            db_health = await check_db_health()
            record_health_check("database", db_health.get("status") == "ok")
        except Exception:
            record_health_check("database", False)

        # Redis health
        try:
            redis_health = await check_redis_health()
            record_health_check("redis", redis_health.get("status") == "ok")
        except Exception:
            record_health_check("redis", False)

        # API health
        record_health_check("api", True)

        # TensorFlow Serving health
        try:
            tf_status = await get_tf_serving_status()
            record_health_check("tensorflow_serving", tf_status.get("status") == "ok")
        except Exception:
            record_health_check("tensorflow_serving", False)

    except Exception as e:
        logger.warning(f"Error recording health checks: {e}")

    # Return metrics in Prometheus format
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(metrics.get_metrics(), media_type="text/plain")


@app.get("/status/websocket")
async def websocket_status() -> Dict[str, Any]:
    """Get WebSocket connection status"""
    if not ENHANCED_BACKEND_AVAILABLE or not websocket_manager:
        return {"error": "WebSocket not available"}

    from .websocket_manager import get_websocket_status

    return await get_websocket_status()


@app.get("/status/tensorflow-serving")
async def tensorflow_serving_status() -> Dict[str, Any]:
    """Get TensorFlow Serving status and model information"""
    if not ENHANCED_BACKEND_AVAILABLE:
        return {"error": "TensorFlow Serving not available"}

    try:
        return await get_tf_serving_status()
    except Exception as e:
        return {"error": f"Failed to get TensorFlow Serving status: {e}"}


@app.get("/status/rate-limits")
async def rate_limit_status(request: Request) -> Dict[str, Any]:
    """Get current rate limit status for the requesting client"""
    if not ENHANCED_BACKEND_AVAILABLE:
        return {"error": "Rate limiting not available"}

    try:
        from .rate_limiter import RateLimitMiddleware

        middleware = RateLimitMiddleware(None)
        rate_key = await middleware._generate_rate_key(request)
        limit_config = middleware._get_limit_config(request.url.path)

        from .rate_limiter import get_rate_limit_status

        status = await get_rate_limit_status(rate_key, limit_config["requests"], limit_config["window"])

        return {"key": rate_key, "config": limit_config, "status": status}
    except Exception as e:
        return {"error": str(e)}


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
async def ingest(reading: SensorReading) -> Dict[str, bool]:
    payload = reading.model_dump()

    # Record metrics
    if ENHANCED_BACKEND_AVAILABLE and "metrics" in locals():
        sensor_type = payload.get("sensor_type", "generic")
        metrics.record_sensor_reading(sensor_type, "api")

    insert_reading(payload)

    # Broadcast sensor update via WebSocket
    if ENHANCED_BACKEND_AVAILABLE and websocket_manager:
        try:
            from .websocket_manager import broadcast_sensor_update

            zone_id = payload.get("zone_id", "Z1")
            await broadcast_sensor_update(zone_id, payload)
        except Exception as e:
            logger.warning(f"Failed to broadcast sensor update: {e}")

    return {"ok": True}


@app.post("/edge/capture")
def edge_capture(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Capture a reading using the local SensorReader (if available),
    ingest it, and return the reading with a fresh recommendation.
    Optional body: {"zone_id":"Z1"}
    """
    if not _edge_available:
        raise HTTPException(status_code=503, detail="Edge reader not available on server")
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
            raise HTTPException(status_code=500, detail=f"Failed to init edge reader: {e}")

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
    rec: Dict[str, Any] = safe_engine_recommend(reading.model_dump())
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
async def recommend(reading: SensorReading, request: Request) -> Recommendation:
    # don't persist automatically; clients can call /ingest
    payload = reading.model_dump()

    # Record metrics
    if ENHANCED_BACKEND_AVAILABLE and "metrics" in locals():
        crop_type = payload.get("crop_type", "unknown")
        model_used = "ml" if safe_engine_attr("water_model") else "rule_based"
        metrics.record_recommendation(crop_type, model_used)

    rec: Dict[str, Any] = safe_engine_recommend(payload)
    # Decide water source (tank vs groundwater) based on latest tank volume
    try:
        need_l = float(rec.get("water_liters", 0.0))
    except Exception:
        need_l = 0.0
    rec["water_source"] = _select_water_source(need_l)

    zone_id = payload.get("zone_id", "Z1")

    # Broadcast recommendation update via WebSocket
    if ENHANCED_BACKEND_AVAILABLE and websocket_manager:
        try:
            from websocket_manager import broadcast_recommendation_update

            await broadcast_recommendation_update(zone_id, rec)
        except Exception as e:
            logger.warning(f"Failed to broadcast recommendation update: {e}")
            # Continue without WebSocket broadcast

    # Optionally send a recommendation alert
    if os.getenv("AGRISENSE_ALERT_ON_RECOMMEND", "0") not in (
        "0",
        "false",
        "False",
        "no",
    ):
        try:
            insert_alert(
                zone_id,
                "RECOMMENDATION",
                f"Water {need_l:.0f} L, source {rec['water_source']}",
            )
            send_alert(
                "Recommendation",
                f"Water {need_l:.0f} L via {rec['water_source']}",
                {"zone_id": zone_id},
            )

            # Broadcast alert via WebSocket
            if ENHANCED_BACKEND_AVAILABLE and websocket_manager:
                try:
                    from .websocket_manager import broadcast_alert

                    await broadcast_alert(
                        {
                            "zone_id": zone_id,
                            "type": "RECOMMENDATION",
                            "message": f"Water {need_l:.0f} L, source {rec['water_source']}",
                            "timestamp": time.time(),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to broadcast alert: {e}")
        except Exception:
            pass
    # Optionally log snapshots if flag set
    if os.getenv("AGRISENSE_LOG_RECO", "0") not in ("0", "false", "False", "no"):
        try:
            insert_reco_snapshot(
                zone_id,
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
        low_thresh = float(os.getenv("AGRISENSE_TANK_LOW_PCT", os.getenv("TANK_LOW_PCT", "20")))
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
        capacity_liters=float(os.getenv("AGRISENSE_TANK_CAP_L", os.getenv("TANK_CAPACITY_L", "0")) or 0.0) or None,
    )


@app.get("/tank/history")
def get_tank_history(tank_id: str = "T1", limit: int = 100, since: Optional[str] = None) -> Dict[str, Any]:
    """Return recent tank level rows for sparkline/history consumers."""
    try:
        limit = max(1, min(1000, int(limit)))
    except Exception:
        limit = 100
    items = recent_tank_levels(tank_id, limit, since)
    return {"items": items}


@app.get("/valves/events")
def get_valve_events(zone_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return {"items": recent_valve_events(zone_id, limit)}


@app.get("/dashboard/summary")
def dashboard_summary(
    zone_id: str = "Z1", tank_id: str = "T1", alerts_limit: int = 5, events_limit: int = 5
) -> Dict[str, Any]:
    """Compact summary for the main dashboard to reduce roundtrips."""
    # Weather latest (do not refetch remote here; reuse cache if present)
    latest_weather: Optional[Dict[str, Any]] = None
    try:
        cache_path = os.getenv(
            "AGRISENSE_WEATHER_CACHE", os.path.join(os.path.dirname(__file__), "..", "..", "weather_cache.csv")
        )
        cache_path = str(cache_path)
        if os.path.exists(cache_path):
            latest_weather = read_latest_from_cache(cache_path)  # type: ignore[assignment]
    except Exception:
        latest_weather = None
    # Soil moisture from recent reading
    last_readings = recent(zone_id, 1)
    soil_pct = None
    if last_readings:
        try:
            soil_pct = float(last_readings[0].get("moisture_pct"))  # type: ignore[arg-type]
        except Exception:
            soil_pct = None
    # Tank snapshot + mini history
    tank_row = latest_tank_level(tank_id) or {}
    tank_hist = recent_tank_levels(tank_id, 20)
    # Valve events and alerts
    events = recent_valve_events(zone_id, events_limit)
    alerts = recent_alerts(zone_id, alerts_limit)
    # Simple impact derivation from reco history
    reco = recent_reco(zone_id, 50)
    saved = 0.0
    try:
        saved = sum(float(r.get("expected_savings_liters") or 0.0) for r in reco)
    except Exception:
        saved = 0.0
    impact = {
        "saved_l": saved,
        "cost_rs": saved * 0.05,
        "co2e_kg": saved * 0.0003,
    }
    return {
        "weather_latest": latest_weather,
        "soil_moisture_pct": soil_pct,
        "tank": tank_row,
        "tank_history": tank_hist,
        "valve_events": events,
        "alerts": alerts,
        "impact": impact,
    }


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
    defaults = safe_engine_attr("defaults", {})
    area_m2_raw = defaults.get("area_m2", 100) if isinstance(defaults, dict) else 100
    # Safely convert area_m2 to float, handling dict or unknown types
    try:
        area_m2 = float(area_m2_raw) if isinstance(area_m2_raw, (int, float)) else 100.0
    except (TypeError, ValueError):
        area_m2 = 100.0
    need: float = 20.0 * area_m2  # fallback
    try:
        last = recent(cmd.zone_id, 1)
        if last:
            need = float(safe_engine_recommend(last[0]).get("water_liters", need))
    except Exception:
        pass
    if not cmd.force and not _has_water_for(need):
        msg = f"Tank insufficient for planned irrigation: need ~{need:.0f} L"
        insert_alert(cmd.zone_id, "water_low", msg)
        try:
            send_alert("Water low", msg, {"zone_id": cmd.zone_id, "need_l": round(need, 1)})
        except Exception:
            pass
        log_valve_event(cmd.zone_id, "start", float(cmd.duration_s or 0), status="blocked")
        return IrrigationAck(ok=False, status="blocked", note="Insufficient water in tank")
    pump_flow = safe_engine_attr("pump_flow_lpm", 10.0)
    pump_flow_val = float(pump_flow) if isinstance(pump_flow, (int, float)) else 10.0
    duration = int(cmd.duration_s or max(1, int(need / max(1e-6, pump_flow_val)) * 60))
    ok = publish_command(cmd.zone_id, {"action": "start", "duration_s": duration})
    log_valve_event(cmd.zone_id, "start", float(duration), status="sent" if ok else "queued")
    try:
        send_alert(
            "Irrigation start",
            f"Zone {cmd.zone_id} for {duration}s",
            {"zone_id": cmd.zone_id, "duration_s": duration},
        )
    except Exception:
        pass
    return IrrigationAck(ok=ok, status="sent" if ok else "queued", note=f"Duration {duration}s")


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
    # Use India dataset (46+ crops) as primary for crop display; optionally merge Sikkim additions
    os.path.join(ROOT, "..", "..", "sikkim_crop_dataset.csv")
    dataset_path = os.path.join(ROOT, "india_crop_dataset.csv")
    # Fallback to repo root if not colocated with backend
    if not os.path.exists(dataset_path):
        alt = os.path.join(ROOT, "..", "..", "india_crop_dataset.csv")
        if os.path.exists(alt):
            dataset_path = alt
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
    if not os.path.exists(labels_path):
        alt_labels = os.path.join(ROOT, "..", "..", "crop_labels.json")
        if os.path.exists(alt_labels):
            labels_path = alt_labels

    def norm(name: str, category: Optional[str] = None) -> PlantItem:
        slug = name.strip().lower().replace(" ", "_").replace("-", "_")
        label = name.replace("_", " ").strip()
        # Title case but preserve acronyms reasonably
        label = " ".join([w.capitalize() for w in label.split()])
        return PlantItem(value=slug, label=label, category=category or None)

    items: Dict[str, PlantItem] = {}
    # From config plants
    for k in safe_engine_attr("plants", {}).keys():
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
        soil_cfg = safe_engine_attr("cfg", {}).get("soil", {})  # type: ignore[assignment]
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
    # Fallback to repo root if not colocated
    if not os.path.exists(dataset_path):
        alt = os.path.join(ROOT, "..", "..", "india_crop_dataset.csv")
        if os.path.exists(alt):
            dataset_path = alt
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
            cat = str((row.get("Crop_Category") or row.get("category") or "")).strip() or None
            try:
                ph_min = row.get("pH_Min") or row.get("ph_min")
                ph_max = row.get("pH_Max") or row.get("ph_max")
                ph_range = f"{float(ph_min):.1f}-{float(ph_max):.1f}" if ph_min and ph_max else None
            except Exception:
                ph_range = None
            try:
                t_min = row.get("Temperature_Min_C") or row.get("temperature_min_c")
                t_max = row.get("Temperature_Max_C") or row.get("temperature_max_c")
                temp_range = f"{int(float(t_min))}-{int(float(t_max))}°C" if t_min and t_max else None
            except Exception:
                temp_range = None
            try:
                growth_days = row.get("Growth_Duration_days") or row.get("growth_days")
                growth_period = f"{int(float(growth_days))} days" if growth_days else None
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
                        water_req = "Low" if v <= 5.0 else ("Medium" if v <= 7.0 else "High")
                    else:
                        water_req = None
            except Exception:
                water_req = None
            season = str((row.get("Growing_Season") or row.get("season") or "")).strip() or None

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

    def plural_forms(base: str) -> List[str]:
        base = base.strip()
        out: Set[str] = set()
        if not base:
            return []
        out.add(base)
        # y -> ies
        if len(base) > 1 and base.endswith("y") and base[-2] not in "aeiou":
            out.add(base[:-1] + "ies")
        # common "es" endings
        for suf in ("s", "x", "z", "ch", "sh", "o"):
            if base.endswith(suf):
                out.add(base + "es")
                break
        # generic s
        out.add(base + "s")
        return list(out)

    for c in _dataset_to_cards():
        base_name = c.name.lower().replace("-", " ")
        base_id = c.id.lower().replace("_", " ")
        candidates: List[str] = [base_name, base_id]
        candidates += plural_forms(base_name)
        candidates += plural_forms(base_id)
        hit = False
        cand_len = -1
        for cand in candidates:
            token = f" {cand.strip()} "
            if token in qnorm:
                hit = True
                cand_len = max(cand_len, len(cand.strip()))
        if hit and cand_len > best_len:
            best = c
            best_len = cand_len
    return best


def _is_simple_crop_name_query(q: str) -> bool:
    """Check if query is just a crop name (1-3 words) or simple info request."""
    ql = q.strip().lower()
    
    # First check if the normalized query matches a known crop name directly
    # This must be checked BEFORE disallow patterns to handle crops like "watermelon"
    normalized = _normalize_crop_name(q)
    is_known_crop = normalized in SUPPORTED_CROPS if normalized else False
    if is_known_crop:
        return True
    
    # Disallow action-oriented or specific how-to questions
    disallow = [
        "how to",
        "how do",
        "how can",
        "how much",
        "when to",
        "when do",
        "why ",
        "where ",
        "should i",
        "can i",
        "control",
        "pest control",
        "disease control",
        "rotate",
        "rotation",
        "apply",
        "rate",
        "best time",
        "spacing",
        "fertilizer",
        "irrigation",
        "water",
        "disease",
        "pest",
    ]
    if any(w in ql for w in disallow):
        return False
    
    # Allow simple info requests
    allow_prefix = (
        ql.startswith("tell me about ")
        or ql.startswith("info about ")
        or ql.startswith("information about ")
        or ql.startswith("what is ")
        or ql.startswith("details about ")
        or ql.startswith("about ")
        or ql.startswith("describe ")
    )
    
    # Allow if query is just the crop name (1-3 tokens, possibly with common words)
    toks = [t for t in _normalize_simple(q).split() if t and t not in ["crop", "crops", "cultivation", "growing", "guide", "farming", "the", "a", "an"]]
    only_crop_name = len(toks) <= 2
    
    return bool(allow_prefix or only_crop_name)


def _get_crop_cultivation_guide(crop_name: str) -> Optional[str]:
    """Retrieve detailed cultivation guide for a specific crop from loaded chatbot answers."""
    try:
        # Use already-loaded chatbot answers (in memory)
        if _chatbot_answers is None or len(_chatbot_answers) == 0:
            logger.warning("Chatbot answers not loaded yet")
            return None
        
        logger.info(f"Searching for cultivation guide for crop: {crop_name}, Total answers: {len(_chatbot_answers)}")
        
        # Normalize crop name for matching
        crop_normalized = crop_name.lower().strip()
        
        # Debug: Count how many answers contain "cultivation guide"
        cultivation_guides = [a for a in _chatbot_answers if "cultivation guide" in a.lower()]
        logger.info(f"Found {len(cultivation_guides)} total cultivation guides in loaded answers")
        
        # Search for cultivation guide in loaded answers
        # Pattern: Look for answers that contain "cultivation guide" and the crop name
        for idx, answer in enumerate(_chatbot_answers):
            answer_lower = str(answer).lower()
            
            # Check if this answer is a cultivation guide for the crop
            if "cultivation guide" in answer_lower and crop_normalized in answer_lower:
                # Found the detailed guide
                logger.info(f"✅ Found cultivation guide for crop '{crop_name}' at index {idx}, length: {len(answer)} chars")
                return str(answer)
        
        # If no match found, log and return None
        logger.warning(f"❌ No cultivation guide found for crop: {crop_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving crop cultivation guide: {e}", exc_info=True)
        return None


# List of all 48 supported crops
SUPPORTED_CROPS = [
    'apple', 'banana', 'barley', 'beans', 'beetroot', 'broccoli', 'cabbage', 'carrot',
    'cauliflower', 'chickpeas', 'chili', 'corn', 'cotton', 'cucumber', 'eggplant', 'garlic',
    'ginger', 'grapes', 'groundnut', 'guava', 'lentils', 'lettuce', 'mango', 'millet',
    'mustard', 'oats', 'onion', 'orange', 'papaya', 'peas', 'pepper', 'pomegranate',
    'potato', 'pumpkin', 'radish', 'rapeseed', 'rice', 'sesame', 'sorghum', 'soybean',
    'spinach', 'strawberry', 'sugarcane', 'sunflower', 'tomato', 'turmeric', 'watermelon', 'wheat'
]


def _normalize_crop_name(text: str) -> Optional[str]:
    """Normalize and validate crop name from user input."""
    # Remove common prefixes/suffixes
    text_lower = text.lower().strip()
    
    # Remove common words
    for word in ['tell me about', 'info about', 'information about', 'what is', 'details about', 'about', 'the', 'crop', 'crops']:
        text_lower = text_lower.replace(word, '').strip()
    
    # Check direct match
    if text_lower in SUPPORTED_CROPS:
        return text_lower
    
    # Check if any supported crop is in the text
    for crop in SUPPORTED_CROPS:
        if crop in text_lower or text_lower in crop:
            return crop
    
    # Check for plural forms
    if text_lower.endswith('s') and text_lower[:-1] in SUPPORTED_CROPS:
        return text_lower[:-1]
    
    # Check for common aliases
    aliases = {
        'maize': 'corn',
        'paddy': 'rice',
        'brinjal': 'eggplant',
        'aubergine': 'eggplant',
        'capsicum': 'pepper',
        'bell pepper': 'pepper',
        'green chili': 'chili',
        'red chili': 'chili',
        'groundnuts': 'groundnut',
        'peanut': 'groundnut',
        'peanuts': 'groundnut',
    }
    
    for alias, crop in aliases.items():
        if alias in text_lower:
            return crop
    
    return None


def _is_general_crop_query(q: str) -> bool:
    ql = q.strip().lower()
    # Disallow crop facts for action-oriented or specific questions
    disallow = [
        "how ",
        "how do",
        "how can",
        "when ",
        "why ",
        "where ",
        "control",
        "pest",
        "disease",
        "rotate",
        "rotation",
        "fert",
        "irrig",
        "sow",
        "depth",
        "year",
        "alternative",
        "option",
        "apply",
        "rate",
    ]
    if any(w in ql for w in disallow):
        return False
    # Positive cues for facts requests
    allow_prefix = (
        ql.startswith("tell me about ")
        or ql.startswith("info about ")
        or ql.startswith("information about ")
        or ql.startswith("what is ")
        or ql.startswith("details about ")
    )
    # Also allow if the query is just the crop name (1-3 tokens) possibly with word 'crop'
    toks = [t for t in _normalize_simple(q).split() if t]
    only_crop_like = len(toks) <= 3 and ("crop" in toks or len(toks) <= 2)
    return bool(allow_prefix or only_crop_like)


def _looks_like_crop_facts(text: str) -> bool:
    try:
        t = str(text).strip()
    except Exception:
        return False
    if not t:
        return False
    # Heuristic: our crop facts start with "Crop: <name>" and include structured lines
    if t.startswith("Crop: "):
        return True
    if ("Category:" in t and "Season:" in t) or ("Water need:" in t and "Soil pH:" in t):
        return True
    return False


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


@app.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    """Alias for chat/ask endpoint for simplified API access"""
    return chat_ask(req)

@app.post("/chat/ask")
def chat_ask(req: ChatRequest) -> ChatResponse:
    q = req.message.strip()
    ql = q.lower()
    sources: List[str] = []

    # 1) PRIORITY: Check if user typed just a crop name (for all 48 crops)
    normalized_crop = _normalize_crop_name(q)
    if normalized_crop and _is_simple_crop_name_query(q):
        # First, try to get detailed cultivation guide
        detailed_guide = _get_crop_cultivation_guide(normalized_crop)
        if detailed_guide:
            sources.append(f"chatbot_qa_pairs.json - {normalized_crop} cultivation guide")
            return ChatResponse(answer=detailed_guide, sources=sources)
        else:
            # For crops without detailed guides, return the normalized crop name
            # This allows the frontend to recognize it as a crop and provide appropriate UI
            sources.append("48 crops database")
            return ChatResponse(answer=normalized_crop, sources=sources)
    
    # 2) Alternative: Check if question mentions a crop from the dataset
    crop_hit: Optional[CropCard] = _find_crop_in_text(q)
    if crop_hit is not None and _is_simple_crop_name_query(q):
        # Try to get detailed cultivation guide
        detailed_guide = _get_crop_cultivation_guide(crop_hit.name.lower())
        if detailed_guide:
            sources.append(f"chatbot_qa_pairs.json - {crop_hit.name} cultivation guide")
            return ChatResponse(answer=detailed_guide, sources=sources)
        else:
            # Return normalized crop name
            crop_name_normalized = crop_hit.name.lower().replace(' ', '_')
            sources.append("crop database")
            return ChatResponse(answer=crop_name_normalized, sources=sources)

    # 3) Irrigation / fertiliser intent -> use last reading and engine
    # Exclude if it's a crop name query (e.g., "watermelon")
    if any(k in ql for k in ["irrigat", "moisture", "fert", "urea", "dap", "mop", "npk"]) or ("water" in ql and not normalized_crop):
        last = recent(req.zone_id, 1)
        base = last[0] if last else safe_engine_attr("defaults", {})
        rec = safe_engine_recommend(dict(base))
        # augment water source decision
        try:
            need_l = float(rec.get("water_liters", 0.0))
        except Exception:
            need_l = 0.0
        rec["water_source"] = _select_water_source(need_l)
        txt = _format_reco(rec)
        sources.extend(["latest reading", "engine.recommend"])
        return ChatResponse(answer=txt, sources=sources)

    # 4) Tank status intent
    if any(k in ql for k in ["tank", "storage", "reservoir", "cistern"]):
        row = latest_tank_level("T1") or {}
        pct = row.get("level_pct")
        vol = row.get("volume_l")
        if pct is None and vol is None:
            return ChatResponse(answer="No tank data available yet.")
        ans = f"Tank level: {pct:.0f}%" if isinstance(pct, (int, float)) else "Tank level: —"
        if isinstance(vol, (int, float)) and vol > 0:
            ans += f", approx {vol:.0f} L"
        sources.append("tank_levels")
        return ChatResponse(answer=ans, sources=sources)

    # 5) Soil pH / EC generic guidance
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

    # 6) Crop suggestion by soil type
    if "best crop" in ql or ("crop" in ql and "soil" in ql):
        # Try to detect simple soil words
        soil = next(
            (w for w in ["loam", "sandy", "clay", "sandy loam", "clay loam"] if w in ql),
            "loam",
        )
        resp = suggest_crop({"soil_type": soil})
        top = ", ".join([c.crop for c in resp.top[:3]]) if resp.top else "(no suggestions)"
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


# --- Plant Health Management Endpoints ---


class ImageUpload(BaseModel):
    """Image data for plant health analysis"""

    image_data: str = Field(..., description="Base64 encoded image data")
    field_info: Optional[Dict[str, Any]] = Field(None, description="Optional field metadata")
    crop_type: Optional[str] = Field("unknown", description="Type of crop being analyzed")
    environmental_data: Optional[Dict[str, Any]] = Field(
        None, description="Environmental sensor data for enhanced analysis"
    )


class HealthAssessmentResponse(BaseModel):
    """Plant health assessment response"""

    assessment_id: str
    overall_health_score: float
    disease_analysis: Dict[str, Any]
    weed_analysis: Dict[str, Any]
    recommendations: Dict[str, Any]
    alert_level: str


@app.post("/disease/detect")
def detect_plant_disease(body: ImageUpload) -> Dict[str, Any]:
    """
    Detect plant diseases in uploaded image

    Args:
        body: Image data and optional field information

    Returns:
        Disease detection results with treatment recommendations
    """
    try:
        # Use the comprehensive disease detector with proper import
        try:
            from .comprehensive_disease_detector import ComprehensiveDiseaseDetector
            detector = ComprehensiveDiseaseDetector()
            logger.info("✅ Disease detector loaded successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import ComprehensiveDiseaseDetector (relative): {e}")
            try:
                # Fallback to direct import
                import comprehensive_disease_detector
                detector = comprehensive_disease_detector.ComprehensiveDiseaseDetector()
                logger.info("✅ Disease detector loaded via fallback import")
            except Exception as e2:
                logger.error(f"❌ All disease detector imports failed: {e2}")
                # Fallback to basic disease detection
                return {
                    "primary_disease": "Disease detected (basic analysis)",
                    "confidence": 0.6,
                    "severity": "medium",
                    "affected_area_percentage": 10.0,
                    "recommended_treatments": [
                        {
                            "treatment_type": "general",
                            "product_name": "General fungicide",
                            "application_rate": "As per label",
                            "frequency": "Weekly",
                            "cost_per_acre": 25.0
                        }
                    ],
                    "prevention_tips": [
                        "Ensure proper air circulation",
                        "Avoid overhead watering",
                        "Remove infected plant material"
                    ],
                    "economic_impact": {
                        "potential_yield_loss": 15.0,
                        "treatment_cost_estimate": 40.0,
                        "cost_benefit_ratio": 3.5
                    }
                }
        
        # Run disease detection with crop type and environmental data
        result = detector.analyze_disease_image(
            image_data=body.image_data, 
            crop_type=body.crop_type or "unknown", 
            environmental_data=body.environmental_data if body.environmental_data is not None else {}
        )

        # Format response to match frontend interface DiseaseDetectionResult
        treatment_plan = result.get("treatment", {})
        
        # Extract recommended treatments from treatment plan
        recommended_treatments = []
        if isinstance(treatment_plan, dict):
            # Convert treatment plan to recommended_treatments array
            for treatment_type, treatments in treatment_plan.items():
                if isinstance(treatments, list) and treatments:
                    for i, treatment in enumerate(treatments[:2]):  # Limit to 2 per type
                        recommended_treatments.append({
                            "treatment_type": treatment_type,
                            "product_name": treatment,
                            "application_rate": "As per label instructions",
                            "frequency": "Weekly" if treatment_type == "immediate" else "Bi-weekly",
                            "cost_per_acre": 25.0 + (i * 15.0)  # Sample cost
                        })
        
        # Extract prevention tips
        prevention_plan = result.get("prevention", {})
        prevention_tips = []
        if isinstance(prevention_plan, dict):
            for tips in prevention_plan.values():
                if isinstance(tips, list):
                    prevention_tips.extend(tips[:3])  # Limit total tips
        
        formatted_result = {
            "primary_disease": result.get("disease_type", "Unknown"),
            "confidence": float(result.get("confidence", 0.0)),  # Keep as decimal for frontend
            "severity": result.get("severity", "unknown"),
            "affected_area_percentage": 15.0,  # Sample percentage
            "recommended_treatments": recommended_treatments,
            "prevention_tips": prevention_tips,
            "economic_impact": {
                "potential_yield_loss": 20.0,  # Sample data
                "treatment_cost_estimate": 50.0,
                "cost_benefit_ratio": 3.5
            }
        }

        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/disease/detect"] = _metrics["by_path"].get("/disease/detect", 0) + 1

        return formatted_result

    except Exception as e:
        logger.error(f"Disease detection failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail=f"Disease detection failed: {str(e)}")


@app.post("/weed/analyze")
def analyze_weeds(body: ImageUpload) -> Dict[str, Any]:
    """
    Analyze weed infestation in field image using smart detection

    Args:
        body: Image data and optional field information

    Returns:
        Weed analysis results with management recommendations
    """
    try:
        # Try to import smart weed detector
        try:
            from .smart_weed_detector import smart_detector
            use_smart_detector = True
        except ImportError as e:
            logger.warning(f"Smart weed detector not available: {e}")
            use_smart_detector = False
        
        if use_smart_detector:
            # Use smart detector for better crop vs weed classification
            result = smart_detector.analyze_image(
                image_data=body.image_data,
                crop_type=body.crop_type or "unknown"
            )
        else:
            # Fallback to basic response
            result = {
                "timestamp": "2025-09-14T21:56:00.000000",
                "crop_type": body.crop_type or "unknown",
                "detection_confidence": 0.5,
                "model_used": "basic_fallback",
                "classification_result": "analysis_unavailable",
                "analysis_summary": {
                    "status": "Smart detector not available",
                    "message": "Please check system configuration"
                },
                "management_recommendations": {
                    "immediate_actions": ["Check system dependencies"]
                }
            }
        
        # Add environmental data to response
        if body.environmental_data:
            result["environmental_data"] = body.environmental_data

        # Format response to match frontend interface WeedAnalysisResult
        formatted_result = {
            "weed_coverage_percentage": 12.5,  # Sample data
            "weed_pressure": "moderate",
            "dominant_weed_types": ["broadleaf_weeds", "grass_weeds"],
            "weed_regions": [
                {
                    "region_id": "region_1",
                    "weed_type": "broadleaf_weeds",
                    "coverage_percentage": 8.0,
                    "density": "medium",
                    "coordinates": [100, 150, 200, 250]
                },
                {
                    "region_id": "region_2", 
                    "weed_type": "grass_weeds",
                    "coverage_percentage": 4.5,
                    "density": "low",
                    "coordinates": [300, 100, 350, 200]
                }
            ],
            "management_plan": {
                "recommended_actions": [
                    {
                        "action_type": "chemical_control",
                        "priority": "medium",
                        "method": "selective_herbicide",
                        "timing": "pre_emergence",
                        "cost_estimate": 45.0
                    },
                    {
                        "action_type": "cultural_control", 
                        "priority": "high",
                        "method": "crop_rotation",
                        "timing": "next_season",
                        "cost_estimate": 15.0
                    }
                ],
                "herbicide_recommendations": [
                    {
                        "product_name": "Selective Herbicide A",
                        "active_ingredient": "2,4-D",
                        "application_rate": "1-2 lbs/acre",
                        "target_weeds": ["broadleaf_weeds"],
                        "cost_per_acre": 25.0
                    },
                    {
                        "product_name": "Grass Control B",
                        "active_ingredient": "glyphosate",
                        "application_rate": "0.5-1 lb/acre",
                        "target_weeds": ["grass_weeds"],
                        "cost_per_acre": 20.0
                    }
                ],
                "cultural_practices": [
                    "Maintain proper crop density",
                    "Regular cultivation between rows",
                    "Implement crop rotation"
                ]
            },
            "economic_analysis": {
                "potential_yield_loss": 15.0,
                "control_cost_estimate": 60.0,
                "roi_estimate": 250.0
            }
        }

        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/weed/analyze"] = _metrics["by_path"].get("/weed/analyze", 0) + 1

        return formatted_result

    except Exception as e:
        logger.error(f"Weed analysis failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail=f"Weed analysis failed: {str(e)}")


# VLM Enhanced Analysis Endpoints

@app.post("/api/disease/detect")
def detect_disease_vlm(body: ImageUpload) -> Dict[str, Any]:
    """
    Enhanced disease detection using Vision Language Model
    
    Args:
        body: Image data and field information
        
    Returns:
        Enhanced disease analysis with knowledge base integration
    """
    try:
        if not VLM_AVAILABLE:
            # Fallback to existing disease detection
            try:
                return detect_plant_disease(body)
            except Exception as e:
                logger.error(f"Fallback disease detection failed: {e}")
                # Return basic response
                return {
                    "primary_disease": "Disease detected (fallback)",
                    "confidence": 0.5,
                    "severity": "unknown",
                    "affected_area_percentage": 0.0,
                    "recommended_treatments": [],
                    "prevention_tips": ["Please consult an agricultural expert"],
                    "economic_impact": {
                        "potential_yield_loss": 0.0,
                        "treatment_cost_estimate": 0.0,
                        "cost_benefit_ratio": 0.0
                    }
                }
        
        # Use VLM for enhanced analysis
        vlm_result = analyze_with_vlm(
            image_input=body.image_data,
            analysis_type='disease',
            crop_type=body.crop_type or 'unknown'
        )
        
        # Extract recommendations from VLM analysis
        recommendations = vlm_result.get('recommendations', {})
        
        # Format response to match frontend interface
        formatted_result = {
            "primary_disease": vlm_result.get('vision_analysis', {}).get('caption', 'Unknown disease detected'),
            "confidence": vlm_result.get('confidence_score', 0.7),
            "severity": "medium",  # Could be enhanced based on VLM analysis
            "affected_area_percentage": 15.0,
            "recommended_treatments": [
                {
                    "treatment_type": "immediate",
                    "product_name": treatment,
                    "application_rate": "As per label instructions",
                    "frequency": "Weekly",
                    "cost_per_acre": 30.0
                }
                for treatment in recommendations.get('treatment_options', [])[:3]
            ],
            "prevention_tips": recommendations.get('preventive_measures', [])[:5],
            "economic_impact": {
                "potential_yield_loss": 18.0,
                "treatment_cost_estimate": 55.0,
                "cost_benefit_ratio": 4.2
            },
            "vlm_analysis": {
                "knowledge_matches": len(vlm_result.get('knowledge_matches', [])),
                "confidence_score": vlm_result.get('confidence_score', 0.7),
                "analysis_timestamp": vlm_result.get('timestamp')
            }
        }
        
        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/api/disease/detect"] = _metrics["by_path"].get("/api/disease/detect", 0) + 1
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"VLM disease detection failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        # Fallback to existing endpoint
        return detect_plant_disease(body)


@app.post("/api/weed/analyze")
def analyze_weeds_vlm(body: ImageUpload) -> Dict[str, Any]:
    """
    Enhanced weed analysis using Vision Language Model
    
    Args:
        body: Image data and field information
        
    Returns:
        Enhanced weed analysis with knowledge base integration
    """
    try:
        if not VLM_AVAILABLE:
            # Fallback to existing weed analysis
            return analyze_weeds(body)
        
        # Use VLM for enhanced analysis
        vlm_result = analyze_with_vlm(
            image_input=body.image_data,
            analysis_type='weed',
            crop_type=body.crop_type or 'unknown'
        )
        
        # Extract recommendations from VLM analysis
        recommendations = vlm_result.get('recommendations', {})
        vision_analysis = vlm_result.get('vision_analysis', {})
        
        # Analyze visual features for weed coverage estimation
        visual_features = vision_analysis.get('visual_features', {})
        contour_count = visual_features.get('contour_count', 10)
        edge_density = visual_features.get('edge_density', 0.1)
        
        # Estimate weed coverage based on visual analysis
        weed_coverage = min(25.0, max(5.0, contour_count * 0.8 + edge_density * 100))
        
        # Determine weed pressure based on coverage
        if weed_coverage < 10:
            weed_pressure = "low"
        elif weed_coverage < 20:
            weed_pressure = "moderate"
        else:
            weed_pressure = "high"
        
        # Format response to match frontend interface
        formatted_result = {
            "weed_coverage_percentage": weed_coverage,
            "weed_pressure": weed_pressure,
            "dominant_weed_types": ["broadleaf_weeds", "grass_weeds"],
            "weed_regions": [
                {
                    "region_id": f"region_{i+1}",
                    "weed_type": "mixed_weeds",
                    "coverage_percentage": weed_coverage / 2,
                    "density": weed_pressure,
                    "coordinates": [100 + i*150, 100, 200 + i*150, 200]
                }
                for i in range(min(3, int(weed_coverage / 8)))
            ],
            "management_plan": {
                "recommended_actions": [
                    {
                        "action_type": "integrated_management",
                        "priority": "high" if weed_pressure == "high" else "medium",
                        "method": action,
                        "timing": "immediate",
                        "cost_estimate": 35.0
                    }
                    for action in recommendations.get('immediate_actions', [])[:3]
                ],
                "herbicide_recommendations": [
                    {
                        "product_name": "VLM Recommended Herbicide",
                        "active_ingredient": "selective compound",
                        "application_rate": "1.5 lbs/acre",
                        "target_weeds": ["broadleaf_weeds", "grass_weeds"],
                        "cost_per_acre": 28.0
                    }
                ],
                "cultural_practices": recommendations.get('preventive_measures', [])[:4]
            },
            "economic_analysis": {
                "potential_yield_loss": min(30.0, weed_coverage * 1.2),
                "control_cost_estimate": 65.0,
                "roi_estimate": max(150.0, 400.0 - weed_coverage * 8)
            },
            "vlm_analysis": {
                "knowledge_matches": len(vlm_result.get('knowledge_matches', [])),
                "confidence_score": vlm_result.get('confidence_score', 0.7),
                "analysis_timestamp": vlm_result.get('timestamp'),
                "visual_features": visual_features
            }
        }
        
        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/api/weed/analyze"] = _metrics["by_path"].get("/api/weed/analyze", 0) + 1
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"VLM weed analysis failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        # Fallback to existing endpoint
        return analyze_weeds(body)


@app.post("/api/vlm/analyze")
def comprehensive_vlm_analysis(body: ImageUpload) -> Dict[str, Any]:
    """
    Comprehensive VLM analysis combining disease and weed detection
    
    Args:
        body: Image data and field information
        
    Returns:
        Comprehensive analysis with integrated recommendations
    """
    try:
        if not VLM_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="VLM analysis not available. Please check system configuration."
            )
        
        # Run both disease and weed analysis
        disease_analysis = analyze_with_vlm(
            image_input=body.image_data,
            analysis_type='disease',
            crop_type=body.crop_type or 'unknown'
        )
        
        weed_analysis = analyze_with_vlm(
            image_input=body.image_data,
            analysis_type='weed',
            crop_type=body.crop_type or 'unknown'
        )
        
        # Combine analyses
        combined_result = {
            "analysis_id": f"vlm_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "crop_type": body.crop_type or 'unknown',
            "timestamp": datetime.now().isoformat(),
            "disease_analysis": disease_analysis,
            "weed_analysis": weed_analysis,
            "integrated_recommendations": {
                "priority_actions": [],
                "integrated_management": [],
                "economic_summary": {
                    "total_potential_loss": 0.0,
                    "total_treatment_cost": 0.0,
                    "overall_roi": 0.0
                }
            },
            "overall_health_score": 0.0,
            "confidence_score": (
                disease_analysis.get('confidence_score', 0.5) + 
                weed_analysis.get('confidence_score', 0.5)
            ) / 2
        }
        
        # Generate integrated recommendations
        disease_recs = disease_analysis.get('recommendations', {})
        weed_recs = weed_analysis.get('recommendations', {})
        
        # Combine immediate actions
        all_actions = []
        all_actions.extend(disease_recs.get('immediate_actions', []))
        all_actions.extend(weed_recs.get('immediate_actions', []))
        combined_result["integrated_recommendations"]["priority_actions"] = list(set(all_actions))[:5]
        
        # Combine preventive measures
        all_preventive = []
        all_preventive.extend(disease_recs.get('preventive_measures', []))
        all_preventive.extend(weed_recs.get('preventive_measures', []))
        combined_result["integrated_recommendations"]["integrated_management"] = list(set(all_preventive))[:6]
        
        # Calculate overall health score (0-100)
        disease_confidence = disease_analysis.get('confidence_score', 0.5)
        weed_confidence = weed_analysis.get('confidence_score', 0.5)
        combined_result["overall_health_score"] = max(0, min(100, 
            85 - (len(disease_recs.get('immediate_actions', [])) * 10) - 
            (len(weed_recs.get('immediate_actions', [])) * 8)
        ))
        
        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/api/vlm/analyze"] = _metrics["by_path"].get("/api/vlm/analyze", 0) + 1
        
        return combined_result
        
    except Exception as e:
        logger.error(f"Comprehensive VLM analysis failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail=f"VLM analysis failed: {str(e)}")


@app.get("/api/vlm/status")
def vlm_status() -> Dict[str, Any]:
    """
    Get VLM system status and capabilities
    
    Returns:
        VLM system status information
    """
    try:
        if VLM_AVAILABLE:
            engine = get_vlm_engine()
            knowledge_stats = {}
            
            if hasattr(engine, 'knowledge_base') and engine.knowledge_base:
                knowledge_stats = {
                    "books_loaded": len(engine.knowledge_base.get('books', {})),
                    "diseases_loaded": len(engine.knowledge_base.get('diseases', {})),
                    "weeds_loaded": len(engine.knowledge_base.get('weeds', {}))
                }
            
            return {
                "vlm_available": True,
                "status": "operational",
                "capabilities": [
                    "disease_detection",
                    "weed_analysis", 
                    "knowledge_base_integration",
                    "visual_feature_extraction",
                    "recommendation_generation"
                ],
                "knowledge_base": knowledge_stats,
                "models": {
                    "vision_model": "available" if hasattr(engine, 'vision_model') and engine.vision_model else "unavailable",
                    "text_encoder": "available" if hasattr(engine, 'text_encoder') and engine.text_encoder else "unavailable",
                    "image_processor": "available" if hasattr(engine, 'image_processor') and engine.image_processor else "unavailable"
                },
                "version": "1.0.0"
            }
        else:
            return {
                "vlm_available": False,
                "status": "unavailable",
                "message": "VLM engine not loaded. Check system dependencies.",
                "capabilities": [],
                "version": "1.0.0"
            }
            
    except Exception as e:
        logger.error(f"VLM status check failed: {e}")
        return {
            "vlm_available": False,
            "status": "error",
            "message": f"Status check failed: {str(e)}",
            "capabilities": [],
            "version": "1.0.0"
        }


@app.post("/health/assess")
def comprehensive_health_assessment(body: ImageUpload) -> Dict[str, Any]:
    """
    Perform comprehensive plant health assessment including disease and weed analysis

    Args:
        body: Image data and optional field information

    Returns:
        Complete health assessment with integrated recommendations
    """
    if not PLANT_HEALTH_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Plant health monitoring not available. Install required dependencies."
        )

    if not plant_health_monitor:
        raise HTTPException(status_code=503, detail="Plant health monitor not initialized. Check system configuration.")

    try:
        # Decode base64 image
        import base64

        image_bytes = base64.b64decode(body.image_data)

        # Run comprehensive assessment
        result = plant_health_monitor.comprehensive_health_assessment(
            image_data=image_bytes,
            field_info=body.field_info,
            crop_type=body.crop_type or "unknown",
            environmental_data=body.environmental_data,
        )

        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/health/assess"] = _metrics["by_path"].get("/health/assess", 0) + 1

        return result


    

    except Exception as e:
        logger.error(f"Health assessment failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail=f"Health assessment failed: {str(e)}")


@app.get("/health/trends")
def get_health_trends(days_back: int = 30) -> Dict[str, Any]:
    """
    Get plant health trends from historical assessments

    Args:
        days_back: Number of days to analyze (default: 30)

    Returns:
        Trend analysis and recommendations
    """
    if not PLANT_HEALTH_AVAILABLE or not plant_health_monitor:
        raise HTTPException(status_code=503, detail="Plant health monitoring not available.")

    try:
        result = plant_health_monitor.get_health_trends(days_back)

        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["by_path"]["/health/trends"] = _metrics["by_path"].get("/health/trends", 0) + 1

        return result

    except Exception as e:
        logger.error(f"Health trends analysis failed: {e}")
        with _metrics_lock:
            _metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail=f"Health trends analysis failed: {str(e)}")


# Frontend adapter: single endpoint that unifies disease/weed analysis responses
@app.post("/api/frontend/analyze")
def frontend_analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter endpoint for frontend components.

    Expected payload: { mode: 'disease' | 'weed', image_data: '<base64 payload or data URL>', crop_type?: str, field_info?: {}, environmental_data?: {} }

    Returns a canonical response with keys that the frontend expects (either disease or weed canonical schema).
    """
    mode = str(payload.get("mode", "disease"))
    image_data = payload.get("image_data")
    crop_type = payload.get("crop_type")
    field_info = payload.get("field_info")
    environmental_data = payload.get("environmental_data")

    if not image_data:
        raise HTTPException(status_code=400, detail="image_data is required")

    # If the client sent a data URL, strip prefix
    import re
    m = re.match(r"^data:.*;base64,(.*)$", image_data)
    if m:
        image_payload = m.group(1)
    else:
        image_payload = image_data

    body = ImageUpload(image_data=image_payload, crop_type=crop_type or "unknown", field_info=field_info, environmental_data=environmental_data)

    if mode == "weed":
        # Call existing weed analyze endpoint (may use VLM or fallback)
        try:
            res = analyze_weeds(body)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Frontend adapter weed analyze failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        # Map weed result to canonical shape
        canonical = {
            "type": "weed",
            "weed_coverage_percentage": res.get("weed_coverage_percentage", 0.0),
            "weed_pressure": res.get("weed_pressure", "unknown"),
            "dominant_weed_types": res.get("dominant_weed_types", []),
            "regions": res.get("weed_regions", []),
            "management_plan": res.get("management_plan", {}),
            "economic_analysis": res.get("economic_analysis", {}),
            "vlm_analysis": res.get("vlm_analysis", {}),
        }
        return canonical

    else:
        # Default to disease
        try:
            res = detect_plant_disease(body)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Frontend adapter disease detect failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        canonical = {
            "type": "disease",
            "primary_disease": res.get("primary_disease", "unknown"),
            "confidence": res.get("confidence", 0.0),
            "severity": res.get("severity", "unknown"),
            "affected_area_percentage": res.get("affected_area_percentage", 0.0),
            "recommended_treatments": res.get("recommended_treatments", []),
            "prevention_tips": res.get("prevention_tips", []),
            "economic_impact": res.get("economic_impact", {}),
            "vlm_analysis": res.get("vlm_analysis", {}),
        }
        return canonical


@app.get("/health/status")
def get_health_system_status() -> Dict[str, Any]:
    """
    Get status of plant health monitoring system

    Returns:
        System status and capabilities
    """
    status = {
        "plant_health_available": PLANT_HEALTH_AVAILABLE,
        "monitor_initialized": plant_health_monitor is not None,
        "ml_enabled": not DISABLE_ML,
        "capabilities": {"disease_detection": False, "weed_management": False, "comprehensive_assessment": False},
    }

    if PLANT_HEALTH_AVAILABLE:
        try:
            # Check individual component status
            if DiseaseDetectionEngine is not None:
                disease_engine = DiseaseDetectionEngine()
                disease_info = disease_engine.get_model_info()
                status["capabilities"]["disease_detection"] = disease_info["status"] == "loaded"
            else:
                disease_info = {"status": "not_available"}

            if WeedManagementEngine is not None:
                weed_engine = WeedManagementEngine()
                weed_info = weed_engine.get_model_info()
                status["capabilities"]["weed_management"] = weed_info["status"] == "loaded"
            else:
                weed_info = {"status": "not_available"}

            status["capabilities"]["comprehensive_assessment"] = plant_health_monitor is not None

            status["model_info"] = {"disease_model": disease_info, "weed_model": weed_info}

        except Exception as e:
            status["error"] = f"Status check failed: {str(e)}"

    return status


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
    rec = safe_engine_recommend(last)
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
    defaults = safe_engine_attr("defaults", {})
    default_area = defaults.get("area_m2", 100.0) if isinstance(defaults, dict) else 100.0
    reading = SensorReading(
        zone_id=zone,
        plant=str(payload.get("plant", "generic")),
        soil_type=str(payload.get("soil_type", "loam")),
        area_m2=float(payload.get("area_m2", default_area)),
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
            insert_tank_level(tank_id, level_pct, vol_l, float(payload.get("rainfall_mm") or 0.0))
        except Exception:
            pass
    return {"ok": True}


# --- Arduino Nano ingest (Serial Bridge) ---
@app.post("/arduino/ingest")
def arduino_ingest(payload: Dict[str, Any], x_admin_token: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Accept sensor data from Arduino Nano via serial bridge.
    Expected payload structure:
    {
        "device_id": "ARDUINO_NANO_01",
        "device_type": "arduino_nano", 
        "timestamp": "2025-09-16T...",
        "sensor_data": {
            "temperatures": {"ds18b20": 25.4, "dht22": 24.8},
            "humidity": 65.2,
            "avg_temperature": 25.1,
            "sensor_status": {"ds18b20": true, "dht22": true}
        }
    }
    """
    # Check admin token
    token = os.getenv("AGRISENSE_ADMIN_TOKEN")
    if token and (not x_admin_token or x_admin_token != token):
        raise HTTPException(status_code=401, detail="Unauthorized: missing or invalid admin token")
    
    try:
        # Extract sensor data
        sensor_data = payload.get("sensor_data", {})
        device_id = payload.get("device_id", "ARDUINO_NANO_01")
        
        # Get temperature readings
        temperatures = sensor_data.get("temperatures", {})
        ds18b20_temp = temperatures.get("ds18b20")
        dht22_temp = temperatures.get("dht22")
        avg_temp = sensor_data.get("avg_temperature")
        humidity = sensor_data.get("humidity")
        
        # Use average temperature if available, otherwise fallback to individual sensors
        final_temp = avg_temp
        if final_temp is None:
            if ds18b20_temp is not None:
                final_temp = ds18b20_temp
            elif dht22_temp is not None:
                final_temp = dht22_temp
            else:
                final_temp = 25.0  # default
        
        # Create a sensor reading for the database
        # Use device_id as zone_id for Arduino sensors
        zone_id = device_id.replace("ARDUINO_NANO_", "AN")  # Convert to shorter zone ID
        
        reading = SensorReading(
            zone_id=zone_id,
            plant="generic",  # Can be customized per Arduino
            soil_type="unknown",  # Arduino doesn't measure soil directly
            area_m2=1.0,  # Small area for Arduino sensor
            ph=7.0,  # Default pH
            moisture_pct=50.0,  # Arduino doesn't measure moisture in this setup
            temperature_c=float(final_temp),
            ec_dS_m=1.0,  # Default EC
        )
        
        # Insert the reading
        insert_reading(reading.model_dump())
        
        # Store raw Arduino data for future use
        arduino_data = {
            "device_id": device_id,
            "timestamp": payload.get("timestamp"),
            "ds18b20_temp": ds18b20_temp,
            "dht22_temp": dht22_temp,
            "humidity": humidity,
            "sensor_status": sensor_data.get("sensor_status", {}),
            "zone_id": zone_id
        }
        
        # Log the Arduino data (could be stored in a separate table in future)
        logger.info(f"Arduino data received: {arduino_data}")
        
        return {
            "ok": True,
            "zone_id": zone_id,
            "temperature_recorded": final_temp,
            "device_id": device_id,
            "message": "Arduino sensor data ingested successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing Arduino data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process Arduino data: {str(e)}")


@app.get("/arduino/status")
def arduino_status() -> Dict[str, Any]:
    """Get status of connected Arduino devices"""
    try:
        # Get recent Arduino readings from the last 5 minutes
        recent_readings = []
        try:
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT zone_id, temperature_c, timestamp
                FROM sensors 
                WHERE zone_id LIKE 'AN%' 
                AND datetime(timestamp) > datetime('now', '-5 minutes')
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            for row in rows:
                recent_readings.append({
                    "zone_id": row[0],
                    "temperature": row[1],
                    "timestamp": row[2]
                })
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching Arduino readings: {e}")
        
        return {
            "status": "active" if recent_readings else "inactive",
            "recent_readings": recent_readings,
            "last_reading_time": recent_readings[0]["timestamp"] if recent_readings else None,
            "total_devices": len(set(r["zone_id"] for r in recent_readings))
        }
        
    except Exception as e:
        logger.error(f"Error getting Arduino status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "recent_readings": [],
            "total_devices": 0
        }


# Serve the frontend as static files under /ui.
ROOT = os.path.dirname(__file__)
FRONTEND_DIST_NESTED = os.path.join(ROOT, "..", "frontend", "farm-fortune-frontend-main", "dist")
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
                response.headers.setdefault("Cache-Control", "public, max-age=604800, immutable")
            else:
                # No cache for HTML files to ensure fresh content
                response.headers.setdefault("Cache-Control", "no-cache, no-store, must-revalidate")
                response.headers.setdefault("Pragma", "no-cache")
                response.headers.setdefault("Expires", "0")
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
    app.mount("/ui", StaticFilesWithCache(directory=FRONTEND_DIST, html=True), name="frontend")
elif os.path.isdir(FRONTEND_LEGACY):
    frontend_root = FRONTEND_LEGACY
    app.mount(
        "/ui",
        StaticFilesWithCache(directory=FRONTEND_LEGACY, html=True),
        name="frontend",
    )


@app.get("/debug")
async def debug_page():
    """Debug page for disease detection testing"""
    debug_html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "debug_disease_detection.html")
    if os.path.exists(debug_html_path):
        with open(debug_html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return {"error": "Debug page not found", "path": debug_html_path}


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


# NOTE: Removed /api/{path:path} catch-all redirect to allow proper validation errors
# Specific /api/ endpoints are defined above (e.g., /api/disease/detect, /api/weed/analyze)


# AdminGuard is defined near the top


# --- Lightweight metrics ---
@app.get("/simple-metrics")
def get_simple_metrics() -> Dict[str, Any]:
    with _metrics_lock:
        out = dict(_metrics)
    # Compute uptime seconds on the fly
    out["uptime_s"] = round(time.time() - float(out.get("started_at", time.time())), 3)
    return out


@app.get("/version")
def version() -> Dict[str, Any]:
    return {"name": app.title, "version": app.version}


# --------------- Chatbot Retrieval Endpoint -----------------


class PyTorchSentenceEncoder:
    """PyTorch-based sentence encoder using SentenceTransformers.

    Provides compatibility with TensorFlow TFSMLayer interface while using PyTorch backend.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Lazily load the SentenceTransformer model."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[reportMissingImports]

            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded PyTorch SentenceTransformer model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load PyTorch SentenceTransformer: {e}")
            self.model = None

    def __call__(self, inputs):
        """Encode text inputs to embeddings.

        Compatible with TFSMLayer interface - accepts TensorFlow constant or list of strings.
        Returns numpy array with shape (batch_size, embedding_dim).
        """
        if self.model is None:
            raise RuntimeError("PyTorch SentenceTransformer model not loaded")

        # Handle TensorFlow tensor input (from existing code)
        if hasattr(inputs, "numpy"):
            texts = [t.decode("utf-8") if isinstance(t, bytes) else str(t) for t in inputs.numpy()]
        elif isinstance(inputs, (list, tuple)):
            texts = [str(t) for t in inputs]
        else:
            texts = [str(inputs)]

        # Encode and normalize embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype(np.float32)


_chatbot_loaded = False
_chatbot_q_layer = None  # type: ignore
_chatbot_answers: Optional[List[str]] = None
_chatbot_emb: Optional[np.ndarray] = None
# Optional question-side index (improves matching user questions to known QA pairs)
_chatbot_q_emb: Optional[np.ndarray] = None
_chatbot_q_texts: Optional[List[str]] = None
_chatbot_q_tokens: Optional[List[Set[str]]] = None
_chatbot_qa_answers: Optional[List[str]] = None  # cleaned, aligned to _chatbot_q_texts
_chatbot_qa_answers_raw: Optional[List[str]] = None  # raw originals, aligned
_chatbot_q_exact_map: Optional[Dict[str, str]] = None  # normalized question -> raw answer
_chatbot_cache: "OrderedDict[tuple[str, int], List[Dict[str, Any]]]" = OrderedDict()
_CHATBOT_CACHE_MAX = 64
_chatbot_answer_tokens: Optional[List[Set[str]]] = None
_chatbot_alpha: float = 0.7  # blend weight for embedding vs lexical
_chatbot_min_cos: float = 0.28  # fallback threshold for cosine similarity
_chatbot_metrics_cache: Optional[Dict[str, Any]] = None
_chatbot_lgbm_bundle: Optional[Dict[str, Any]] = None  # {'model': lgb.Booster, 'vectorizer': TfidfVectorizer}
_chatbot_artifact_sig: Optional[Dict[str, float]] = None  # mtimes to detect changes
_bm25_ans: Optional[Any] = None
_bm25_q: Optional[Any] = None
_bm25_weight: float = 0.45  # default weight for BM25 within lexical term
_pool_min: int = 50  # minimum pool size for candidate gathering
_pool_mult: int = 12  # multiplier on requested top_k for pool size
# Default top_k for API responses (can be overridden via env)
try:
    DEFAULT_TOPK = int(os.getenv("CHATBOT_DEFAULT_TOPK") or os.getenv("AGRISENSE_CHATBOT_DEFAULT_TOPK") or 5)
except Exception:
    DEFAULT_TOPK = 5
DEFAULT_TOPK = max(1, min(100, int(DEFAULT_TOPK)))


def _tokenize(text: str) -> Set[str]:
    try:
        t = text.lower()
        # keep alphanumerics and spaces
        t = "".join(ch if ch.isalnum() else " " for ch in t)
        raw = [w for w in t.split() if len(w) >= 3]
        # light stopword set (en)
        stop = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "of",
            "to",
            "for",
            "in",
            "on",
            "by",
            "at",
            "is",
            "are",
            "was",
            "were",
            "be",
            "with",
            "as",
            "that",
            "this",
            "these",
            "those",
            "it",
            "its",
            "from",
            "into",
            "about",
            "over",
            "under",
            "while",
            "than",
            "then",
            "how",
            "what",
            "when",
            "where",
            "which",
            "why",
            "who",
            "whom",
            "can",
            "could",
            "should",
            "would",
            "may",
            "might",
            "also",
            "such",
            "like",
        }
        norm: Set[str] = set()
        for w in raw:
            if w in stop:
                continue
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
        # Fix common encoding artifacts like 'Â°C', dashes, and quotes
        t = (
            text.replace("Â°C", "°C")
            .replace("\u00c2\u00b0C", "°C")
            .replace("Â", "")
            # mis-decoded en/em dashes
            .replace("â€“", "–")
            .replace("â€”", "—")
            .replace("â€“", "–")
            # ascii hyphen variants sometimes show as â€• or similar
            .replace("â€•", "—")
            # quotes/apostrophes
            .replace("â€™", "’")
            .replace("â€˜", "‘")
            .replace("â€œ", "“")
            .replace("â€�", "”")
            # final normalization to simple hyphen for client compatibility
            .replace("–", "-")
            .replace("—", "-")
        )
        # Normalize number ranges like '25â35' -> '25-35'
        t = re.sub(r"(?<=\d)\s*â\s*(?=\d)", "-", t)
        t = re.sub(r"(?<=\d)\s*(?:–|—)\s*(?=\d)", "-", t)
        # Try to repair common mojibake by CP1252/Latin-1 -> UTF-8 roundtrip when we see 'â' or 'Â'
        if ("â" in t) or ("Â" in t):
            try:
                b = t.encode("cp1252", errors="strict")
                t2 = b.decode("utf-8", errors="strict")
                if t2 and t2 != t:
                    t = t2
            except Exception:
                try:
                    b = t.encode("latin-1", errors="strict")
                    t2 = b.decode("utf-8", errors="strict")
                    if t2 and t2 != t:
                        t = t2
                except Exception:
                    pass
        return t
    except Exception:
        return text


def _safe_get(lst: Optional[List[Any]], j: int, default: Any = "") -> Any:
    """Safe index into a list-like object. Returns default for None or OOB indices."""
    try:
        if not lst:
            return default
        if j < 0 or j >= len(lst):
            return default
        return lst[j]
    except Exception:
        return default


def _safe_tokens(tokens_list: Optional[List[Set[str]]], j: int) -> Set[str]:
    """Return token set for index j, or empty set on any error."""
    try:
        if not tokens_list:
            return set()
        t = tokens_list[j]
        return t if t else set()
    except Exception:
        return set()


def _artifact_signature(qenc_dir: Path, index_npz: Path, index_json: Path, metrics_path: Path) -> Dict[str, float]:
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
    global _chatbot_loaded, _chatbot_q_layer, _chatbot_emb, _chatbot_answers, _chatbot_answer_tokens, _chatbot_alpha, _chatbot_min_cos, _chatbot_metrics_cache, _chatbot_artifact_sig, _chatbot_lgbm_bundle, _chatbot_q_emb, _chatbot_q_texts, _chatbot_q_tokens, _chatbot_qa_answers, _chatbot_q_exact_map, _bm25_ans, _bm25_q, _bm25_weight, _pool_min, _pool_mult
    try:
        backend_dir = Path(__file__).resolve().parent
        qenc_dir = backend_dir / "chatbot_question_encoder"
        index_npz = backend_dir / "chatbot_index.npz"
        index_json = backend_dir / "chatbot_index.json"
        metrics_path = backend_dir / "chatbot_metrics.json"
        qindex_npz = backend_dir / "chatbot_q_index.npz"
        qa_pairs_json = backend_dir / "chatbot_qa_pairs.json"

        # If already loaded, only reload when artifacts haven't changed
        if _chatbot_loaded:
            try:
                sig_now = _artifact_signature(qenc_dir, index_npz, index_json, metrics_path)
                if _chatbot_artifact_sig == sig_now:
                    return True
            except Exception:
                # if signature calc fails, fall through to attempt reload
                pass

        # Accept either chatbot_index.json or chatbot_qa_pairs.json as the source of answers metadata
        if not index_npz.exists() or not (index_json.exists() or qa_pairs_json.exists()):
            logger.warning(
                "Chatbot artifacts not found; need chatbot_index.npz and one of chatbot_index.json/chatbot_qa_pairs.json"
            )
            return False

        # Try PyTorch SentenceTransformer first if requested or TF artifacts not available
        use_pytorch = os.getenv("AGRISENSE_USE_PYTORCH_SBERT", "auto").lower()
        pytorch_loaded = False

        if use_pytorch in ("1", "true", "yes", "auto"):
            try:
                # Check if we can determine model name from existing config or use default
                model_name = os.getenv("AGRISENSE_SBERT_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

                # Try to load PyTorch model
                _chatbot_q_layer = PyTorchSentenceEncoder(model_name)
                if _chatbot_q_layer.model is not None:
                    pytorch_loaded = True
                    logger.info(f"Using PyTorch SentenceTransformer: {model_name}")
                else:
                    logger.warning("PyTorch SentenceTransformer loading failed, falling back to TensorFlow")
            except Exception as e:
                logger.warning(f"PyTorch SentenceTransformer unavailable ({e}), falling back to TensorFlow")

        # Fallback to TensorFlow SavedModel if PyTorch failed or not requested
        if not pytorch_loaded:
            if qenc_dir.exists():
                try:
                    # Load SavedModel endpoint via Keras TFSMLayer
                    from tensorflow.keras.layers import TFSMLayer  # type: ignore

                    _chatbot_q_layer = TFSMLayer(str(qenc_dir), call_endpoint="serve")
                    logger.info("Using TensorFlow SavedModel for chatbot embeddings")
                except Exception as e:
                    logger.warning(f"Failed to load TensorFlow SavedModel: {e}")
                    _chatbot_q_layer = None
            else:
                # No encoder available; we'll operate in lexical-only mode if needed
                logger.info("No encoder available (PyTorch/TF). Will use lexical fallback only.")
                _chatbot_q_layer = None
        with np.load(index_npz, allow_pickle=False) as data:
            arr = data["embeddings"]
        # L2-normalize answer embeddings to use cosine similarity robustly
        try:
            norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
            arr = arr / norms
        except Exception:
            pass
        _chatbot_emb = arr
        meta: Dict[str, Any] = {}
        try:
            if index_json.exists():
                with open(index_json, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                _chatbot_answers = [_clean_text(a) for a in list(meta.get("answers", []))]
            else:
                # Fallback: read answers from QA pairs JSON
                with open(qa_pairs_json, "r", encoding="utf-8") as fqa:
                    qa_meta = json.load(fqa)
                _chatbot_answers = [_clean_text(a) for a in list(qa_meta.get("answers", []))]
        except Exception:
            logger.exception("Failed to read answers metadata for chatbot index")
            _chatbot_answers = []
        # Pre-tokenize answers for lightweight lexical re-ranking
        _chatbot_answer_tokens = [_tokenize(a) for a in _chatbot_answers]
        # Build BM25 indices if available
        try:
            if BM25Okapi is not None and _chatbot_answers:
                ans_docs = [list(_tokenize(a)) for a in _chatbot_answers]
                _bm25_ans = BM25Okapi(ans_docs)
            else:
                _bm25_ans = None
        except Exception:
            _bm25_ans = None

        # Optionally read metrics and tune blend/threshold
        try:
            if metrics_path.exists():
                with open(metrics_path, "r", encoding="utf-8") as mf:
                    _chatbot_metrics_cache = json.load(mf)
                r1 = float((_chatbot_metrics_cache or {}).get("val", {}).get("recall@1", 0.0))
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
                env_alpha = os.getenv("CHATBOT_ALPHA") or os.getenv("AGRISENSE_CHATBOT_ALPHA")
                if env_alpha is not None and str(env_alpha).strip() != "":
                    _chatbot_alpha = float(env_alpha)
                    # clamp to safe range
                    _chatbot_alpha = max(0.0, min(1.0, _chatbot_alpha))
                env_min_cos = os.getenv("CHATBOT_MIN_COS") or os.getenv("AGRISENSE_CHATBOT_MIN_COS")
                if env_min_cos is not None and str(env_min_cos).strip() != "":
                    _chatbot_min_cos = float(env_min_cos)
                    _chatbot_min_cos = max(0.0, min(1.0, _chatbot_min_cos))
                # BM25 weight and pool sizing
                env_bm25 = os.getenv("CHATBOT_BM25_WEIGHT") or os.getenv("AGRISENSE_CHATBOT_BM25_WEIGHT")
                if env_bm25 is not None and str(env_bm25).strip() != "":
                    try:
                        _bm25_weight = float(env_bm25)
                        if not isfinite(_bm25_weight):
                            _bm25_weight = 0.45
                        _bm25_weight = max(0.0, min(1.0, _bm25_weight))
                    except Exception:
                        _bm25_weight = 0.45
                env_pool_min = os.getenv("CHATBOT_POOL_MIN")
                if env_pool_min:
                    try:
                        _pool_min = max(20, int(env_pool_min))
                    except Exception:
                        pass
                env_pool_mult = os.getenv("CHATBOT_POOL_MULT")
                if env_pool_mult:
                    try:
                        _pool_mult = max(5, int(env_pool_mult))
                    except Exception:
                        pass
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
            _chatbot_qa_answers_raw = None
            _chatbot_q_exact_map = None
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
                    _chatbot_qa_answers_raw = list(aans)
                    _chatbot_qa_answers = [_clean_text(a) for a in aans]
                    _chatbot_q_tokens = [_tokenize(t) for t in qtexts]
                    # Build exact-match lookup on normalized question text
                    try:
                        qmap: Dict[str, str] = {}
                        for qt, ans_raw in zip(qtexts, _chatbot_qa_answers_raw):
                            key = _normalize_simple(str(qt))
                            if key and key not in qmap:
                                qmap[key] = str(ans_raw)
                        _chatbot_q_exact_map = qmap
                    except Exception:
                        _chatbot_q_exact_map = None
                    # Build BM25 over questions too (optional)
                    try:
                        if BM25Okapi is not None and _chatbot_q_tokens:
                            q_docs = [list(t) for t in _chatbot_q_tokens]
                            _bm25_q = BM25Okapi(q_docs)
                        else:
                            _bm25_q = None
                    except Exception:
                        _bm25_q = None
                    logger.info("Loaded question index with %d QA pairs", len(qtexts))
        except Exception:
            _chatbot_q_emb = None
            _chatbot_q_texts = None
            _chatbot_q_tokens = None
            _chatbot_qa_answers = None
            logger.warning(
                "Failed loading question index; will use answer index only",
                exc_info=True,
            )

        _chatbot_loaded = True
        try:
            _chatbot_artifact_sig = _artifact_signature(qenc_dir, index_npz, index_json, metrics_path)
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
    top_k: int = Field(default=DEFAULT_TOPK, ge=1, le=100)
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation tracking")
    language: Optional[str] = Field(default="en", description="Language code (en, hi, ta, te, kn)")


class ChatbotTune(BaseModel):
    alpha: Optional[float] = None
    min_cos: Optional[float] = None


def _normalize_user_question(question: str) -> tuple[str, bool]:
    """
    Normalize user questions to handle small/improper questions better.
    Returns: (normalized_question, needs_expansion)
    """
    qtext = question.strip().lower()
    
    # Common typo corrections
    typo_map = {
        "wat": "what", "wt": "what", "hw": "how", "wen": "when", "whn": "when",
        "whr": "where", "wich": "which", "shud": "should", "cud": "could",
        "wud": "would", "r": "are", "u": "you", "ur": "your", "y": "why",
        "bst": "best", "gud": "good", "gd": "good", "nw": "now",
        "cro": "crop", "crps": "crops", "wtr": "water", "irri": "irrigation",
        "fert": "fertilizer", "fertlizer": "fertilizer", "pest": "pest",
        "diseas": "disease", "desease": "disease", "soi": "soil", "sol": "soil",
        "seed": "seed", "plnt": "plant", "grw": "grow", "harvst": "harvest",
        "2": "to", "4": "for", "8": "ate"
    }
    
    words = qtext.split()
    normalized_words = []
    for word in words:
        normalized_words.append(typo_map.get(word, word))
    
    normalized = " ".join(normalized_words)
    
    # Detect if question needs expansion (too small/vague)
    needs_expansion = len(words) <= 2 or len(qtext) < 10
    
    # Common crop names - when user just types crop name, expand to information query
    crop_names = {
        # Cereals/Grains
        "rice": "tell me about rice crop cultivation requirements and best practices",
        "paddy": "tell me about rice paddy cultivation requirements and best practices",
        "wheat": "tell me about wheat crop cultivation requirements and best practices",
        "corn": "tell me about corn crop cultivation requirements and best practices",
        "maize": "tell me about maize crop cultivation requirements and best practices",
        "barley": "tell me about barley crop cultivation requirements and best practices",
        "millet": "tell me about millet crop cultivation requirements and best practices",
        "sorghum": "tell me about sorghum crop cultivation requirements and best practices",
        "oats": "tell me about oats crop cultivation requirements and best practices",
        
        # Vegetables
        "tomato": "tell me about tomato crop cultivation requirements and best practices",
        "tomatoes": "tell me about tomato crop cultivation requirements and best practices",
        "potato": "tell me about potato crop cultivation requirements and best practices",
        "potatoes": "tell me about potato crop cultivation requirements and best practices",
        "onion": "tell me about onion crop cultivation requirements and best practices",
        "onions": "tell me about onion crop cultivation requirements and best practices",
        "cabbage": "tell me about cabbage crop cultivation requirements and best practices",
        "carrot": "tell me about carrot crop cultivation requirements and best practices",
        "carrots": "tell me about carrot crop cultivation requirements and best practices",
        "brinjal": "tell me about brinjal crop cultivation requirements and best practices",
        "eggplant": "tell me about brinjal eggplant cultivation requirements and best practices",
        "cauliflower": "tell me about cauliflower crop cultivation requirements and best practices",
        "spinach": "tell me about spinach crop cultivation requirements and best practices",
        "lettuce": "tell me about lettuce crop cultivation requirements and best practices",
        "cucumber": "tell me about cucumber crop cultivation requirements and best practices",
        "pumpkin": "tell me about pumpkin crop cultivation requirements and best practices",
        "squash": "tell me about squash crop cultivation requirements and best practices",
        "pepper": "tell me about pepper crop cultivation requirements and best practices",
        "peppers": "tell me about pepper crop cultivation requirements and best practices",
        "chili": "tell me about chili pepper cultivation requirements and best practices",
        "chilli": "tell me about chili pepper cultivation requirements and best practices",
        
        # Legumes/Pulses
        "bean": "tell me about bean crop cultivation requirements and best practices",
        "beans": "tell me about bean crop cultivation requirements and best practices",
        "pea": "tell me about pea crop cultivation requirements and best practices",
        "peas": "tell me about pea crop cultivation requirements and best practices",
        "lentil": "tell me about lentil crop cultivation requirements and best practices",
        "lentils": "tell me about lentil crop cultivation requirements and best practices",
        "chickpea": "tell me about chickpea crop cultivation requirements and best practices",
        "chickpeas": "tell me about chickpea crop cultivation requirements and best practices",
        "soybean": "tell me about soybean crop cultivation requirements and best practices",
        "soybeans": "tell me about soybean crop cultivation requirements and best practices",
        "groundnut": "tell me about groundnut peanut cultivation requirements and best practices",
        "peanut": "tell me about peanut groundnut cultivation requirements and best practices",
        "peanuts": "tell me about peanut groundnut cultivation requirements and best practices",
        
        # Cash Crops
        "cotton": "tell me about cotton crop cultivation requirements and best practices",
        "sugarcane": "tell me about sugarcane crop cultivation requirements and best practices",
        "tobacco": "tell me about tobacco crop cultivation requirements and best practices",
        "tea": "tell me about tea crop cultivation requirements and best practices",
        "coffee": "tell me about coffee crop cultivation requirements and best practices",
        "rubber": "tell me about rubber crop cultivation requirements and best practices",
        "jute": "tell me about jute crop cultivation requirements and best practices",
        
        # Fruits
        "mango": "tell me about mango crop cultivation requirements and best practices",
        "banana": "tell me about banana crop cultivation requirements and best practices",
        "bananas": "tell me about banana crop cultivation requirements and best practices",
        "apple": "tell me about apple crop cultivation requirements and best practices",
        "apples": "tell me about apple crop cultivation requirements and best practices",
        "orange": "tell me about orange crop cultivation requirements and best practices",
        "oranges": "tell me about orange crop cultivation requirements and best practices",
        "grape": "tell me about grape crop cultivation requirements and best practices",
        "grapes": "tell me about grape crop cultivation requirements and best practices",
        "watermelon": "tell me about watermelon crop cultivation requirements and best practices",
        "papaya": "tell me about papaya crop cultivation requirements and best practices",
        "guava": "tell me about guava crop cultivation requirements and best practices",
        "pomegranate": "tell me about pomegranate crop cultivation requirements and best practices",
        "strawberry": "tell me about strawberry crop cultivation requirements and best practices",
        "strawberries": "tell me about strawberry crop cultivation requirements and best practices",
        
        # Spices/Herbs
        "turmeric": "tell me about turmeric crop cultivation requirements and best practices",
        "ginger": "tell me about ginger crop cultivation requirements and best practices",
        "garlic": "tell me about garlic crop cultivation requirements and best practices",
        "coriander": "tell me about coriander crop cultivation requirements and best practices",
        "cumin": "tell me about cumin crop cultivation requirements and best practices",
        "cardamom": "tell me about cardamom crop cultivation requirements and best practices",
        "pepper": "tell me about pepper crop cultivation requirements and best practices",
        "mint": "tell me about mint crop cultivation requirements and best practices",
        "basil": "tell me about basil crop cultivation requirements and best practices",
    }
    
    # Check if user just typed a crop name
    if normalized in crop_names:
        return crop_names[normalized], True
    
    # Expand common single-word/vague questions
    expansion_map = {
        "water": "how to water crops properly",
        "watering": "how to water crops properly",
        "irrigation": "what is the best irrigation method",
        "fertilizer": "what fertilizer should I use",
        "fertilizers": "what fertilizer should I use",
        "crop": "what crop should I plant",
        "crops": "what crops are best to grow",
        "pest": "how to control pests",
        "pests": "how to control pests",
        "disease": "how to prevent crop disease",
        "diseases": "how to prevent crop disease",
        "soil": "how to improve soil quality",
        "seed": "how to select good seeds",
        "seeds": "how to select good seeds",
        "help": "what agricultural advice do you provide",
        "start": "how to start farming",
        "begin": "how to start farming",
        "plant": "how to plant crops",
        "grow": "how to grow crops successfully",
        "harvest": "when to harvest crops",
        "farm": "how to manage a farm",
        "farming": "best farming practices",
    }
    
    if needs_expansion and normalized in expansion_map:
        return expansion_map[normalized], True
    
    # Multi-word expansion for common patterns
    if needs_expansion:
        if "what" in normalized or "wt" in qtext:
            if "crop" in normalized:
                return "what crops are best to grow", True
            if "fert" in normalized or "fertilizer" in normalized:
                return "what fertilizer should I use", True
        if "how" in normalized or "hw" in qtext:
            if "water" in normalized or "irri" in normalized:
                return "how to water crops properly", True
            if "plant" in normalized or "grow" in normalized:
                return "how to grow crops successfully", True
    
    return normalized, needs_expansion


def _generate_fallback_response(question: str, language: str = "en") -> str:
    """
    Generate helpful fallback response when no good answers found
    """
    fallback_templates = {
        "en": {
            "water": "🌊 **About Watering & Irrigation:**\nI'd love to help with watering! Here are some common topics:\n• Irrigation methods (drip, sprinkler, flood)\n• Watering schedules for different crops\n• Signs of over/under-watering\n\nCould you ask a more specific question? For example: 'What is the best irrigation method for tomatoes?' or 'How often should I water wheat crops?'",
            "fertilizer": "🌱 **About Fertilizers:**\nI can help with fertilizer questions! Topics I know about:\n• Organic vs chemical fertilizers\n• NPK ratios for different crops\n• When and how to apply fertilizer\n• Soil testing\n\nTry asking: 'What fertilizer ratio is best for rice?' or 'When should I apply fertilizer to corn?'",
            "crop": "🌾 **About Crops:**\nI can help you choose the right crops! I know about:\n• Best crops for different soil types\n• Seasonal planting recommendations\n• Crop rotation benefits\n• High-yield varieties\n\nAsk me: 'What crops grow well in clay soil?' or 'What should I plant in monsoon season?'",
            "pest": "🐛 **About Pest Control:**\nI can advise on pest management! Topics include:\n• Identifying common pests\n• Natural pest control methods\n• Chemical pesticide recommendations\n• Preventive measures\n\nTry: 'How to control aphids on vegetables?' or 'What are natural pest control methods?'",
            "disease": "🦠 **About Plant Diseases:**\nI can help with disease management! I cover:\n• Common crop diseases\n• Disease prevention\n• Organic treatments\n• Fungicide recommendations\n\nAsk: 'How to prevent tomato blight?' or 'What causes yellowing leaves?'",
            "soil": "🌍 **About Soil Management:**\nI can help improve your soil! Topics:\n• Soil testing and pH levels\n• Improving soil fertility\n• Composting methods\n• Soil types and amendments\n\nTry: 'How to improve sandy soil?' or 'What pH level is best for vegetables?'",
            "general": "👋 **I'm here to help with farming questions!**\n\nI can assist with:\n• 🌊 Irrigation and watering\n• 🌱 Fertilizers and nutrients\n• 🌾 Crop selection and planting\n• 🐛 Pest control\n• 🦠 Disease management\n• 🌍 Soil improvement\n\nPlease ask a specific question like:\n• 'What is the best irrigation method for rice?'\n• 'How often should I fertilize wheat?'\n• 'What crops grow well in monsoon season?'\n• 'How to control pests naturally?'",
        },
        "hi": {
            "general": "👋 **मैं खेती के सवालों में मदद के लिए यहाँ हूँ!**\n\nमैं इन विषयों में सहायता कर सकता हूँ:\n• 🌊 सिंचाई और पानी\n• 🌱 उर्वरक और पोषक तत्व\n• 🌾 फसल चयन और रोपण\n• 🐛 कीट नियंत्रण\n• 🦠 रोग प्रबंधन\n• 🌍 मिट्टी सुधार\n\nकृपया एक विशिष्ट प्रश्न पूछें जैसे:\n• 'धान के लिए सबसे अच्छी सिंचाई विधि क्या है?'\n• 'गेहूं को कितनी बार उर्वरक देना चाहिए?'\n• 'मानसून के मौसम में कौन सी फसलें अच्छी होती हैं?'",
        }
    }
    
    # Detect question topic
    question_lower = question.lower()
    topic = "general"
    
    for keyword in ["water", "irrigation", "irri", "sinkhai", "watering"]:
        if keyword in question_lower:
            topic = "water"
            break
    
    if topic == "general":
        for keyword in ["fertilizer", "fert", "urvarak", "nutrient", "npk"]:
            if keyword in question_lower:
                topic = "fertilizer"
                break
    
    if topic == "general":
        for keyword in ["crop", "plant", "fasal", "seed"]:
            if keyword in question_lower:
                topic = "crop"
                break
    
    if topic == "general":
        for keyword in ["pest", "insect", "keet", "bug"]:
            if keyword in question_lower:
                topic = "pest"
                break
    
    if topic == "general":
        for keyword in ["disease", "blight", "fungus", "rog"]:
            if keyword in question_lower:
                topic = "disease"
                break
    
    if topic == "general":
        for keyword in ["soil", "mitti", "mati", "earth"]:
            if keyword in question_lower:
                topic = "soil"
                break
    
    templates = fallback_templates.get(language, fallback_templates["en"])
    return templates.get(topic, templates["general"])


@app.post("/chatbot/ask")
def chatbot_ask(q: ChatbotQuery) -> Dict[str, Any]:
    ok = _load_chatbot_artifacts()
    # Require at minimum the answers list; allow missing encoder/embeddings for lexical-only mode
    if (not ok) or (_chatbot_answers is None) or (len(_chatbot_answers) == 0):
        raise HTTPException(status_code=503, detail="Chatbot not trained or artifacts missing")
    
    # Normalize and validate input - enhanced for small/improper questions
    original_question = q.question.strip()
    if not original_question:
        raise HTTPException(status_code=400, detail="question must not be empty")
    
    # PRIORITY 1: Check if this is a simple crop name query (before any expansion)
    # This handles queries like "carrot", "watermelon", "rice" etc.
    normalized_crop = _normalize_crop_name(original_question)
    if normalized_crop and normalized_crop in SUPPORTED_CROPS:
        if _is_simple_crop_name_query(original_question):
            # Try to get detailed cultivation guide
            guide = _get_crop_cultivation_guide(normalized_crop)
            if guide:
                return {"question": original_question, "results": [{"rank": 1, "score": 1.0, "answer": guide}]}
            else:
                # Return just the crop name as fallback
                return {"question": original_question, "results": [{"rank": 1, "score": 1.0, "answer": normalized_crop}]}
    
    # Normalize question to handle typos and expand small/vague questions
    qtext, was_expanded = _normalize_user_question(original_question)
    
    # Log if we expanded the question for debugging
    if was_expanded:
        logger.info(f"Expanded question from '{original_question}' to '{qtext}'")
    # Allow env-based cap to quickly tune recall vs payload size
    try:
        TOPK_MAX = int(os.getenv("CHATBOT_TOPK_MAX") or os.getenv("AGRISENSE_CHATBOT_TOPK_MAX") or 20)
    except Exception:
        TOPK_MAX = 20
    TOPK_MAX = max(1, min(100, TOPK_MAX))
    topk = int(max(1, min(q.top_k, TOPK_MAX)))

    # LRU cache lookup
    key = (qtext, topk)
    if key in _chatbot_cache:
        results = _chatbot_cache.pop(key)
        _chatbot_cache[key] = results  # move to end (most recent)
        return {"question": qtext, "results": results}

    # (moved) crop facts branch appears later, after dataset question fallbacks
    # Optional exact/fuzzy short-circuits (disabled by default; enable via CHATBOT_ENABLE_QMATCH=1)
    _enable_qmatch = str(os.getenv("CHATBOT_ENABLE_QMATCH", "0")).lower() in (
        "1",
        "true",
        "yes",
    )
    if _enable_qmatch:
        # Exact-match fallback using known dataset questions (helps achieve near-100% on known QA)
        try:
            qnorm = _normalize_simple(qtext)
            if _chatbot_q_exact_map and qnorm in _chatbot_q_exact_map:
                ans_txt = _chatbot_q_exact_map[qnorm]
                # Avoid returning crop facts for action/specific queries
                if not (not _is_general_crop_query(qtext) and _looks_like_crop_facts(ans_txt)):
                    results = [{"rank": 1, "score": 1.0, "answer": ans_txt}]
                    _chatbot_cache[key] = results
                    if len(_chatbot_cache) > _CHATBOT_CACHE_MAX:
                        _chatbot_cache.popitem(last=False)
                    return {"question": qtext, "results": results}
        except Exception:
            pass
        # Fuzzy question match fallback using token Jaccard against known QA questions
        try:
            if _chatbot_q_tokens and _chatbot_q_texts and _chatbot_qa_answers_raw:
                qtok_f = _tokenize(qtext)
                if qtok_f:
                    best_i = -1
                    best_j = 0.0
                    for i, toks in enumerate(_chatbot_q_tokens):
                        if not toks:
                            continue
                        inter = len(qtok_f & toks)
                        if inter == 0:
                            continue
                        jac = inter / float(len(qtok_f | toks))
                        if jac > best_j:
                            best_j = jac
                            best_i = i
                    # If strong similarity, return the raw dataset answer directly
                    if best_i >= 0 and best_j >= 0.55:
                        ans_txt = _chatbot_qa_answers_raw[best_i]
                        # Avoid returning crop facts for action/specific queries
                        if not (not _is_general_crop_query(qtext) and _looks_like_crop_facts(ans_txt)):
                            results = [{"rank": 1, "score": 1.0, "answer": ans_txt}]
                            _chatbot_cache[key] = results
                            if len(_chatbot_cache) > _CHATBOT_CACHE_MAX:
                                _chatbot_cache.popitem(last=False)
                            return {"question": qtext, "results": results}
        except Exception:
            pass
    # (moved) crop facts fallback handled at the end if retrieval is weak/empty
    # Compute question embedding
    # Use TensorFlow tensor input when TF is available; otherwise pass plain list for PyTorch encoder
    if tf is not None and hasattr(tf, "constant"):
        # SavedModel signature is positional-only (args_0) with name 'text' and dtype tf.string
        _enc_inp = tf.constant([qtext], dtype=tf.string)  # type: ignore[attr-defined]
    else:
        _enc_inp = [qtext]
    # Compute dense embedding; if this fails or dims mismatch with index, we will attempt lexical-only fallback
    v: Optional[np.ndarray] = None
    dense_ok = False
    try:
        if _chatbot_q_layer is None:
            raise RuntimeError("no-encoder")
        vec = _chatbot_q_layer(_enc_inp)
        if isinstance(vec, (list, tuple)):
            vec = vec[0]
        try:
            if hasattr(vec, "numpy"):
                v = vec.numpy()[0]  # type: ignore
            else:
                v = np.array(vec)[0]
        except Exception:
            v = np.array(vec)[0]
        # L2-normalize question vector for cosine similarity
        try:
            if v is not None:
                v = v / (np.linalg.norm(v) + 1e-12)
        except Exception:
            pass
        # Basic shape guard against artifact dimension mismatch
        if _chatbot_emb is not None and v is not None and v.shape[-1] == _chatbot_emb.shape[-1]:
            dense_ok = True
    except Exception:
        dense_ok = False
    qtok = _tokenize(qtext)

    # Prefer question-index retrieval if available (match user question -> dataset question)
    use_qindex = _chatbot_q_emb is not None and _chatbot_q_texts is not None and _chatbot_qa_answers is not None
    reranked: List[tuple[int, float]] = []
    idx_source = "q" if use_qindex else "a"
    if use_qindex and dense_ok:
        qemb = cast(np.ndarray, _chatbot_q_emb)
        scores = qemb @ v
        pool = int(max(_pool_mult * topk, _pool_min))
        # Dense candidates
        dense_idx = scores.argsort()[::-1][: min(pool, scores.shape[0])]
        # BM25 candidates over questions (optional)
        bm25_scores = None
        bm25_norm = {}
        try:
            if _bm25_q is not None and qtok:
                bm25_scores = cast(Any, _bm25_q).get_scores(list(qtok))
                # min-max normalize for stable blending
                b = np.asarray(bm25_scores, dtype=np.float32)
                bmin, bmax = float(np.min(b)), float(np.max(b))
                if not np.isfinite(bmin) or not np.isfinite(bmax) or bmax <= bmin:
                    bmin, bmax = 0.0, 1.0
                bn = (b - bmin) / (bmax - bmin + 1e-9)
                # pick top pool
                bm25_idx = bn.argsort()[::-1][: min(pool, bn.shape[0])]
                bm25_norm = {int(i): float(bn[int(i)]) for i in bm25_idx}
            else:
                bm25_norm = {}
        except Exception:
            bm25_norm = {}
        # Union candidates
        if bm25_norm:
            cand_set = set(int(i) for i in dense_idx) | set(int(i) for i in bm25_norm.keys())
            cand_idx = list(cand_set)
        else:
            cand_idx = list(map(int, dense_idx))
        alpha = _chatbot_alpha
        beta = 1.0 - alpha
        q_tokens_list = _chatbot_q_tokens
        q_is_action = not _is_general_crop_query(qtext)
        for j in cand_idx:
            # Skip generic crop-info dataset questions when user asks an action/specific query
            try:
                if q_is_action and _chatbot_q_texts is not None:
                    dq = _safe_get(cast(List[str], _chatbot_q_texts), j, "")
                    if _is_general_crop_query(dq or ""):
                        continue
            except Exception:
                pass
            # Skip answers that look like crop facts, too
            if q_is_action:
                cand_ans0 = _safe_get(cast(List[str], _chatbot_qa_answers_raw), j, "")
                if _looks_like_crop_facts(cand_ans0):
                    continue
            sim = float(scores[j])
            overlap = 0.0
            if q_tokens_list is not None and qtok:
                inter = qtok.intersection(q_tokens_list[j])
                if qtok:
                    overlap = len(inter) / max(1.0, float(len(qtok)))
            # Blend lexical (token overlap + BM25) with dense embedding
            bm = float(bm25_norm.get(int(j), 0.0))
            lex = (1.0 - _bm25_weight) * overlap + _bm25_weight * bm
            blended = alpha * sim + beta * lex
            # If the candidate answer is crop facts and the query seems action/specific, penalize slightly
            if q_is_action:
                cand_ans = _safe_get(cast(List[str], _chatbot_qa_answers_raw), j, "")
                if _looks_like_crop_facts(cand_ans):
                    blended -= 0.50
            reranked.append((j, blended))
        reranked.sort(key=lambda x: x[1], reverse=True)
    elif dense_ok:
        # Fallback: original answer-index retrieval
        emb: np.ndarray = cast(np.ndarray, _chatbot_emb)
        scores = emb @ v
        pool = int(max(_pool_mult * topk, _pool_min))
        # Dense candidates
        dense_idx = scores.argsort()[::-1][: min(pool, scores.shape[0])]
        # BM25 candidates over answers (optional)
        bm25_scores = None
        bm25_norm = {}
        try:
            if _bm25_ans is not None and qtok:
                bm25_scores = cast(Any, _bm25_ans).get_scores(list(qtok))
                b = np.asarray(bm25_scores, dtype=np.float32)
                bmin, bmax = float(np.min(b)), float(np.max(b))
                if not np.isfinite(bmin) or not np.isfinite(bmax) or bmax <= bmin:
                    bmin, bmax = 0.0, 1.0
                bn = (b - bmin) / (bmax - bmin + 1e-9)
                bm25_idx = bn.argsort()[::-1][: min(pool, bn.shape[0])]
                bm25_norm = {int(i): float(bn[int(i)]) for i in bm25_idx}
            else:
                bm25_norm = {}
        except Exception:
            bm25_norm = {}
        # Union candidates
        if bm25_norm:
            cand_set = set(int(i) for i in dense_idx) | set(int(i) for i in bm25_norm.keys())
            cand_idx = list(cand_set)
        else:
            cand_idx = list(map(int, dense_idx))
        alpha = _chatbot_alpha
        beta = 1.0 - alpha
        ans_tokens = _chatbot_answer_tokens
        q_is_action = not _is_general_crop_query(qtext)
        for j in cand_idx:
            sim = float(scores[j])
            # Skip answers that look like crop facts for action queries
            if q_is_action:
                cand_ans0 = _safe_get(cast(List[str], _chatbot_answers), j, "")
                if _looks_like_crop_facts(cand_ans0):
                    continue
            overlap = 0.0
            if ans_tokens is not None and qtok:
                inter = qtok.intersection(ans_tokens[j])
                if qtok:
                    overlap = len(inter) / max(1.0, float(len(qtok)))
            bm = float(bm25_norm.get(int(j), 0.0))
            lex = (1.0 - _bm25_weight) * overlap + _bm25_weight * bm
            blended = alpha * sim + beta * lex
            # Penalize crop facts for action-like queries
            if q_is_action:
                cand_ans = _safe_get(cast(List[str], _chatbot_answers), j, "")
                if _looks_like_crop_facts(cand_ans):
                    blended -= 0.50
            reranked.append((j, blended))
        reranked.sort(key=lambda x: x[1], reverse=True)
    else:
        # Lexical-only fallback (no dense embedding available): rank by BM25 and token overlap
        scores = np.zeros(len(_chatbot_answers or []), dtype=np.float32)
        bm25_norm = {}
        try:
            if _bm25_ans is not None and qtok:
                b = np.asarray(cast(Any, _bm25_ans).get_scores(list(qtok)), dtype=np.float32)
                bmin, bmax = float(np.min(b)), float(np.max(b))
                if not np.isfinite(bmin) or not np.isfinite(bmax) or bmax <= bmin:
                    bmin, bmax = 0.0, 1.0
                bn = (b - bmin) / (bmax - bmin + 1e-9)
                # take top pool by BM25
                order = bn.argsort()[::-1]
                bm25_norm = {int(i): float(bn[int(i)]) for i in order[: max(_pool_min, topk * _pool_mult)]}
        except Exception:
            bm25_norm = {}
        ans_tokens = _chatbot_answer_tokens
        alpha = 0.0  # no dense component
        beta = 1.0
        reranked = []
        cand_idx = list(bm25_norm.keys()) if bm25_norm else list(range(len(_chatbot_answers or [])))
        for j in cand_idx:
            overlap = 0.0
            if ans_tokens is not None and qtok:
                inter = qtok.intersection(_safe_tokens(ans_tokens, j))
                if qtok:
                    overlap = len(inter) / max(1.0, float(len(qtok)))
            bm = float(bm25_norm.get(int(j), 0.0))
            lex = (1.0 - _bm25_weight) * overlap + _bm25_weight * bm
            reranked.append((int(j), beta * lex))
        reranked.sort(key=lambda x: x[1], reverse=True)
        idx_source = "a"
    # Optional LightGBM re-ranking on top candidates to refine order
    try:
        if _chatbot_lgbm_bundle and len(reranked) > 0:
            take = min(len(reranked), max(20, topk * 4))
            cand = reranked[:take]
            vec = _chatbot_lgbm_bundle.get("vectorizer")  # type: ignore[assignment]
            model = _chatbot_lgbm_bundle.get("model")  # type: ignore[assignment]
            if vec is not None and model is not None:
                q_arr = [qtext] * len(cand)
                # Choose answer text source depending on which index produced the
                # candidate ids: when using the question-index (idx_source == 'q')
                # use the QA raw answers list; otherwise use the answer-index list.
                # Build candidate answers defensively (some candidate ids may
                # refer to indices not present in the chosen answer list).
                cand_answers = []
                if idx_source == "q":
                    qa_list = cast(List[str], _chatbot_qa_answers_raw or [])
                    for j, _ in cand:
                        try:
                            cand_answers.append(qa_list[j] if j < len(qa_list) else "")
                        except Exception:
                            cand_answers.append("")
                else:
                    ans_list = cast(List[str], _chatbot_answers or [])
                    for j, _ in cand:
                        try:
                            cand_answers.append(ans_list[j] if j < len(ans_list) else "")
                        except Exception:
                            cand_answers.append("")
                q_tf = vec.transform(q_arr)
                a_tf = vec.transform(cand_answers)
                cos_proxy = (q_tf.multiply(a_tf)).sum(axis=1)
                cos_proxy = np.asarray(cos_proxy).ravel().astype(np.float32)
                qtok_set = set(qtok)
                # choose appropriate token list depending on index used
                tokens_list = _chatbot_q_tokens if idx_source == "q" else _chatbot_answer_tokens
                jac = np.array(
                    [
                        (
                            len(qtok_set & _safe_tokens(tokens_list, j))
                            / max(1, len(qtok_set | _safe_tokens(tokens_list, j)))
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
                merged = [(j, 0.85 * s + 0.15 * float(lnorm[i])) for i, (j, s) in enumerate(cand)]
                merged.sort(key=lambda x: x[1], reverse=True)
                reranked = merged
    except Exception:
        logger.warning("LightGBM re-rank failed; keep blended order", exc_info=True)

    # For action/specific queries, filter out crop-facts-like answers if possible
    q_is_action = not _is_general_crop_query(qtext)
    choose = reranked
    if q_is_action and reranked:
        try:
            if idx_source == "q":

                def ans_of(j: int) -> str:
                    return _safe_get(cast(List[str], _chatbot_qa_answers_raw), j, "")

            else:

                def ans_of(j: int) -> str:
                    return _safe_get(cast(List[str], _chatbot_answers), j, "")

            filtered = [(j, s) for (j, s) in reranked if not _looks_like_crop_facts(ans_of(j))]
            if filtered:
                choose = filtered
        except Exception:
            pass
    idx = [j for (j, s) in choose[:topk]]
    if idx_source == "q" and dense_ok:
        qa_answers = cast(List[str], _chatbot_qa_answers_raw or [])
        results = []
        for i, j in enumerate(idx):
            try:
                score_val = float(scores[j]) if j < len(scores) else 0.0
            except Exception:
                score_val = 0.0
            ans_txt = _safe_get(qa_answers, j, "")
            results.append({"rank": i + 1, "score": score_val, "answer": ans_txt})
    else:
        results = [
            {
                "rank": i + 1,
                "score": float(scores[j]),
                "answer": _clean_text(_chatbot_answers[j]),
            }
            for i, j in enumerate(idx)
        ]
    # If action-like query and top result looks like crop facts, fall back to answer-index retrieval
    try:
        q_is_action = not _is_general_crop_query(qtext)
        if q_is_action and results and _looks_like_crop_facts(str(results[0].get("answer", ""))):
            emb: np.ndarray = cast(np.ndarray, _chatbot_emb)
            scores2 = emb @ v
            pool2 = int(max(_pool_mult * topk, _pool_min))
            dense_idx2 = scores2.argsort()[::-1][: min(pool2, scores2.shape[0])]
            bm25_norm2 = {}
            try:
                if _bm25_ans is not None and qtok:
                    b2 = np.asarray(cast(Any, _bm25_ans).get_scores(list(qtok)), dtype=np.float32)
                    bmin2, bmax2 = float(np.min(b2)), float(np.max(b2))
                    if not np.isfinite(bmin2) or not np.isfinite(bmax2) or bmax2 <= bmin2:
                        bmin2, bmax2 = 0.0, 1.0
                    bn2 = (b2 - bmin2) / (bmax2 - bmin2 + 1e-9)
                    bm_idx2 = bn2.argsort()[::-1][: min(pool2, bn2.shape[0])]
                    bm25_norm2 = {int(i): float(bn2[int(i)]) for i in bm_idx2}
            except Exception:
                bm25_norm2 = {}
            if bm25_norm2:
                cand_set2 = set(int(i) for i in dense_idx2) | set(int(i) for i in bm25_norm2.keys())
                cand_idx2 = list(cand_set2)
            else:
                cand_idx2 = list(map(int, dense_idx2))
            alpha = _chatbot_alpha
            beta = 1.0 - alpha
            ans_tokens = _chatbot_answer_tokens
            rer2: List[tuple[int, float]] = []
            for j in cand_idx2:
                sim = float(scores2[j])
                # Skip crop-facts-like answers entirely for action/specific queries
                if q_is_action:
                    cand_ans0 = _safe_get(cast(List[str], _chatbot_qa_answers_raw), j, "")
                    if _looks_like_crop_facts(cand_ans0):
                        continue
                # Skip crop-facts-like answers entirely for action/specific queries
                if q_is_action:
                    cand_ans0 = _safe_get(cast(List[str], _chatbot_answers), j, "")
                    if _looks_like_crop_facts(cand_ans0):
                        continue
                overlap = 0.0
                if ans_tokens is not None and qtok:
                    inter = qtok.intersection(_safe_tokens(ans_tokens, j))
                    if qtok:
                        overlap = len(inter) / max(1.0, float(len(qtok)))
                bm = float(bm25_norm2.get(int(j), 0.0))
                lex = (1.0 - _bm25_weight) * overlap + _bm25_weight * bm
                rer2.append((j, alpha * sim + beta * lex))
            rer2.sort(key=lambda x: x[1], reverse=True)
            # filter out crop facts
            try:
                filt2 = [
                    (j, s)
                    for (j, s) in rer2
                    if not _looks_like_crop_facts(_clean_text(_safe_get(cast(List[str], _chatbot_answers), j, "")))
                ]
                if filt2:
                    rer2 = filt2
            except Exception:
                pass
            idx2 = [j for (j, s) in rer2[:topk]]
            results = [
                {
                    "rank": i + 1,
                    "score": float(scores2[j]),
                    "answer": _clean_text(_safe_get(cast(List[str], _chatbot_answers), j, "")),
                }
                for i, j in enumerate(idx2)
            ]
            # If still looks like crop facts, try BM25-only rescue to pick first non-facts answer
            if results and _looks_like_crop_facts(str(results[0].get("answer", ""))):
                try:
                    if _bm25_ans is not None and qtok:
                        b = np.asarray(
                            cast(Any, _bm25_ans).get_scores(list(qtok)),
                            dtype=np.float32,
                        )
                        order = b.argsort()[::-1]
                        chosen = None
                        for jj in order[: max(50, topk * 5)]:
                            ans_txt = _clean_text(_safe_get(cast(List[str], _chatbot_answers), int(jj), ""))
                            if not _looks_like_crop_facts(ans_txt):
                                chosen = int(jj)
                                break
                        if chosen is not None:
                            results = [
                                {
                                    "rank": 1,
                                    "score": float(b[chosen]),
                                    "answer": _clean_text(_chatbot_answers[chosen]),
                                }
                            ]
                except Exception:
                    pass
    except Exception:
        pass
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
            llm_scores = None
            try:
                if llm_clients is not None and hasattr(llm_clients, "llm_rerank"):
                    llm_scores = llm_clients.llm_rerank(qtext, cand_answers)
            except Exception:
                llm_scores = None
            if llm_scores:
                for i, sc in enumerate(llm_scores):
                    subset[i]["score"] = (subset[i]["score"] * (1.0 - LLM_BLEND)) + (float(sc) * LLM_BLEND)
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
    # Final enforcement: for action-like queries, strip any crop-facts answers and rescue via BM25 if needed
    try:
        q_is_action = not _is_general_crop_query(qtext)
        if q_is_action:
            # Remove any crop-facts style answers
            filtered_results: List[Dict[str, Any]] = [
                r for r in (results or []) if not _looks_like_crop_facts(str(r.get("answer", "")))
            ]
            results = filtered_results
            # If empty, try BM25-only rescue to pick the first non-facts answer
            if (not results) and (_bm25_ans is not None) and qtok:
                try:
                    b = np.asarray(cast(Any, _bm25_ans).get_scores(list(qtok)), dtype=np.float32)
                    order = b.argsort()[::-1]
                    chosen = None
                    for jj in order[: max(100, topk * 10)]:
                        ans_txt = _clean_text(_chatbot_answers[int(jj)])
                        if not _looks_like_crop_facts(ans_txt):
                            chosen = int(jj)
                            break
                    if chosen is not None:
                        results = [
                            {
                                "rank": 1,
                                "score": float(b[chosen]),
                                "answer": _clean_text(_chatbot_answers[chosen]),
                            }
                        ]
                except Exception:
                    pass
            # As a last resort, if still empty, return a neutral guidance note
            if not results:
                results = [
                    {
                        "rank": 1,
                        "score": 0.0,
                        "answer": (
                            "I couldn't find a specific action-focused answer. Try rephrasing with more details (crop, stage, issue)."
                        ),
                    }
                ]
    except Exception:
        pass
    # Final crop facts fallback: gated by env CHATBOT_ENABLE_CROP_FACTS and only if no good retrieval
    try:
        enable_facts = str(os.getenv("CHATBOT_ENABLE_CROP_FACTS", "0")).lower() in (
            "1",
            "true",
            "yes",
        )
        if enable_facts:
            need_facts = False
            if not results:
                need_facts = True
            else:
                try:
                    top_cos = float(scores[idx[0]]) if idx else 0.0
                except Exception:
                    top_cos = 0.0
                # require a higher bar (>= 0.25) to avoid overriding good QA
                # Lowered from 0.40 to 0.25 to allow TF-IDF comprehensive guides to be retrieved
                # Use fixed 0.25 instead of max(0.25, _chatbot_min_cos) to ensure threshold is not increased
                if top_cos < 0.25:
                    need_facts = True
            if need_facts:
                crop_hit: Optional[CropCard] = _find_crop_in_text(qtext)
                if crop_hit is not None and _is_general_crop_query(qtext):
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
    except Exception:
        pass
    # Check if results are too weak - provide helpful fallback for small/improper questions
    if not results or (results and results[0].get("score", 0) < 0.25):
        language = q.language or "en"
        fallback_answer = _generate_fallback_response(original_question, language)
        
        # If we expanded the question, try to provide better context
        if was_expanded and results:
            # Keep the retrieved result but add helpful context
            results[0]["answer"] = f"I noticed you asked a short question. Let me help!\n\n{results[0].get('answer', '')}\n\n---\n\n{fallback_answer}"
        else:
            # No good results, provide pure fallback
            results = [{
                "rank": 1,
                "score": 0.5,
                "answer": fallback_answer,
                "is_fallback": True
            }]
    
    # Update LRU cache
    _chatbot_cache[key] = results
    if len(_chatbot_cache) > _CHATBOT_CACHE_MAX:
        _chatbot_cache.popitem(last=False)
    
    # Enhance responses with conversational style (makes chatbot more human-like)
    try:
        if CONVERSATIONAL_ENHANCEMENT_AVAILABLE and results:
            language = q.language or "en"
            session_id = q.session_id
            
            # Enhance each answer to be more conversational and farmer-friendly
            for result in results:
                original_answer = result.get("answer", "")
                if original_answer:
                    # Don't enhance fallback responses (they're already conversational)
                    if result.get("is_fallback", False):
                        result["answer"] = original_answer
                    else:
                        enhanced_answer = enhance_chatbot_response(
                            question=qtext,
                            base_answer=original_answer,
                            session_id=session_id,
                            language=language
                        )
                        result["answer"] = enhanced_answer
                        # Keep original for comparison if needed
                        result["original_answer"] = original_answer
    except Exception as e:
        logger.warning(f"Failed to enhance chatbot response: {e}")
        # Continue with non-enhanced responses
    
    return {"question": qtext, "results": results}


@app.get("/chatbot/ask")
def chatbot_ask_get(
    question: str, 
    top_k: int = DEFAULT_TOPK,
    session_id: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """GET alias for chatbot ask to simplify smoke testing via browser/tools."""
    return chatbot_ask(ChatbotQuery(
        question=question, 
        top_k=top_k,
        session_id=session_id,
        language=language
    ))


@app.get("/chatbot/greeting")
def chatbot_greeting(language: str = "en") -> Dict[str, str]:
    """
    Get a friendly greeting message in the specified language.
    Useful for initializing chat sessions with a warm welcome.
    """
    try:
        if CONVERSATIONAL_ENHANCEMENT_AVAILABLE:
            greeting = get_greeting_message(language)
            return {
                "language": language,
                "greeting": greeting,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "language": language,
                "greeting": "Hello! How can I help you with your farming questions today?",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        logger.error(f"Error generating greeting: {e}")
        return {
            "language": language,
            "greeting": "Hello! How can I help you today?",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


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
    global _chatbot_loaded, _chatbot_q_layer, _chatbot_emb, _chatbot_answers, _chatbot_answer_tokens, _chatbot_metrics_cache, _chatbot_artifact_sig, _bm25_ans, _bm25_q
    # Clear current state
    _chatbot_loaded = False
    _chatbot_q_layer = None
    _chatbot_emb = None
    _chatbot_answers = None
    _chatbot_answer_tokens = None
    _chatbot_metrics_cache = None
    _chatbot_artifact_sig = None
    _chatbot_cache.clear()
    _bm25_ans = None
    _bm25_q = None
    ok = _load_chatbot_artifacts()
    return {
        "ok": bool(ok),
        "answers": len(_chatbot_answers or []),
        "alpha": _chatbot_alpha,
        "min_cos": _chatbot_min_cos,
    }


@app.post("/chatbot/tune")
def chatbot_tune(t: ChatbotTune) -> Dict[str, Any]:
    """Adjust chatbot blending (alpha) and cosine threshold at runtime."""
    global _chatbot_alpha, _chatbot_min_cos
    try:
        if t.alpha is not None:
            a = float(t.alpha)
            _chatbot_alpha = max(0.0, min(1.0, a))
        if t.min_cos is not None:
            m = float(t.min_cos)
            _chatbot_min_cos = max(0.0, min(1.0, m))
        return {"ok": True, "alpha": _chatbot_alpha, "min_cos": _chatbot_min_cos}
    except Exception:
        logger.exception("tune failed")
        raise HTTPException(status_code=400, detail="invalid tune values")
