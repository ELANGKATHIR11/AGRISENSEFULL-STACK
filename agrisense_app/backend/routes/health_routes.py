"""
Health Check and System Status Endpoints
Provides monitoring endpoints for system health, readiness, and component status
"""
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Health & Status"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Basic health check - returns 200 if service is running"""
    return HealthResponse(status="ok")


@router.get("/live", response_model=HealthResponse)
def liveness_check() -> HealthResponse:
    """Kubernetes liveness probe - checks if service should be restarted"""
    return HealthResponse(status="live")


@router.get("/ready")
def readiness_check(
    engine = None,  # Will be injected via dependency
) -> Dict[str, Any]:
    """
    Kubernetes readiness probe - checks if service can handle traffic
    Returns details about ML model availability
    """
    from ..config.app_config import DISABLE_ML
    
    # Check if engine is available
    engine_ready = engine is not None
    
    # Check ML models if enabled
    water_model_ready = False
    fert_model_ready = False
    
    if engine_ready and not DISABLE_ML:
        try:
            water_model_ready = hasattr(engine, 'water_model') and engine.water_model is not None
            fert_model_ready = hasattr(engine, 'fert_model') and engine.fert_model is not None
        except Exception:
            pass
    
    return {
        "status": "ready",
        "timestamp": time.time(),
        "engine_available": engine_ready,
        "ml_enabled": not DISABLE_ML,
        "water_model_loaded": water_model_ready,
        "fert_model_loaded": fert_model_ready,
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check including all system components
    Used for monitoring dashboards and alerting
    """
    from ..config.app_config import API_VERSION
    
    health_data: Dict[str, Any] = {
        "status": "ok",
        "timestamp": time.time(),
        "version": API_VERSION,
        "components": {
            "api": {
                "status": "ok",
                "version": API_VERSION,
            },
        },
    }
    
    # Check database (if available)
    try:
        from ..core.data_store import get_conn
        conn = get_conn()
        conn.close()
        health_data["components"]["database"] = {"status": "ok", "type": "sqlite"}
    except Exception as e:
        health_data["components"]["database"] = {"status": "error", "error": str(e)}
    
    # Check Redis (if available)
    try:
        from ..database_enhanced import check_redis_health
        redis_health = await check_redis_health()
        health_data["components"]["redis"] = redis_health
    except ImportError:
        health_data["components"]["redis"] = {"status": "not_configured"}
    except Exception as e:
        health_data["components"]["redis"] = {"status": "error", "error": str(e)}
    
    # Check WebSocket manager (if available)
    try:
        from ..websocket_manager import manager as websocket_manager
        if websocket_manager:
            health_data["components"]["websocket"] = {
                "status": "ok",
                "connected_clients": websocket_manager.get_client_count(),
                "total_connections": websocket_manager.get_connection_count(),
            }
    except ImportError:
        health_data["components"]["websocket"] = {"status": "not_configured"}
    except Exception as e:
        health_data["components"]["websocket"] = {"status": "error", "error": str(e)}
    
    # Determine overall status
    component_statuses = [comp.get("status") for comp in health_data["components"].values()]
    if any(status == "error" for status in component_statuses):
        health_data["status"] = "degraded"
    elif all(status == "ok" for status in component_statuses):
        health_data["status"] = "ok"
    else:
        health_data["status"] = "partial"
    
    return health_data


@router.get("/status/components")
async def component_status() -> Dict[str, Any]:
    """Get detailed status of all optional components"""
    components: Dict[str, Any] = {}
    
    # Check ML components
    from ..config.app_config import DISABLE_ML
    components["ml"] = {
        "enabled": not DISABLE_ML,
        "status": "ok" if not DISABLE_ML else "disabled",
    }
    
    # Check VLM
    try:
        from ..vlm_engine import get_vlm_engine
        vlm_engine = get_vlm_engine()
        components["vlm"] = {
            "available": vlm_engine is not None,
            "status": "ok" if vlm_engine else "unavailable",
        }
    except ImportError:
        components["vlm"] = {"available": False, "status": "not_installed"}
    
    # Check disease detection
    try:
        from ..disease_detection import DiseaseDetectionEngine
        components["disease_detection"] = {"available": True, "status": "ok"}
    except ImportError:
        components["disease_detection"] = {"available": False, "status": "not_installed"}
    
    # Check weed management
    try:
        from ..weed_management import WeedManagementEngine
        components["weed_management"] = {"available": True, "status": "ok"}
    except ImportError:
        components["weed_management"] = {"available": False, "status": "not_installed"}
    
    # Check MQTT
    from ..config.app_config import MQTT_BROKER, MQTT_PORT
    components["mqtt"] = {
        "broker": MQTT_BROKER,
        "port": MQTT_PORT,
        "status": "configured",
    }
    
    return {
        "timestamp": time.time(),
        "components": components,
    }
