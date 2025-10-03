#!/usr/bin/env python3
"""
Real-time Sensor Data API Endpoints for AgriSense
Extends the main AgriSense backend with live sensor data access
"""

from typing import Dict, Any, Optional, TYPE_CHECKING  # noqa: F401
import importlib
import logging
from datetime import datetime

# Editor-friendly guarded FastAPI imports. When running inside the project's .venv
# the real FastAPI will be used; editors without the environment won't error.
try:
    from fastapi import APIRouter, HTTPException, Depends  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - fallback for editors
    if TYPE_CHECKING:  # type-checker can still understand types
        from fastapi import APIRouter, HTTPException, Depends  # type: ignore  # noqa: F401

    # Minimal runtime stub used only when FastAPI isn't importable (editor-only)
    class _StubRouter:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            # reference args/kwargs to avoid unused-variable warnings in editors
            _ = args
            _ = kwargs

        def get(self, *args, **kwargs):
            # reference args/kwargs to avoid unused-variable warnings in editors
            _ = args
            _ = kwargs
            def _d(fn):
                return fn
            return _d

        def post(self, *args, **kwargs):
            # mirror get() behaviour for editor-only usage
            _ = args
            _ = kwargs
            def _d(fn):
                return fn
            return _d

    APIRouter = _StubRouter  # type: ignore

    class HTTPException(Exception):  # pragma: no cover
        """Lightweight editor/runtime-compatible HTTPException compatible with FastAPI usage."""
        def __init__(self, status_code: int, detail: Optional[str] = None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    def Depends(*args, **kwargs):  # pragma: no cover
        # mirror FastAPI Depends signature for editor/runtime compatibility
        _ = args
        _ = kwargs
if TYPE_CHECKING:
    # For static analysis only - these modules are loaded dynamically at runtime
    from agrisense_app.backend.engine import RecoEngine  # type: ignore  # noqa: F401
    from agrisense_app.backend.api.mqtt_sensor_bridge import AgriSenseMQTTBridge  # type: ignore  # noqa: F401
logger = logging.getLogger(__name__)

# Try to import the MQTT bridge (try multiple likely module paths and handle instantiation failures)
MQTT_BRIDGE_AVAILABLE = False
mqtt_bridge = None  # type: ignore
_mqtt_import_paths = (
    "agrisense_app.backend.mqtt_bridge",
    "agrisense_app.backend.mqtt_sensor_bridge",
    "agrisense_app.backend.api.mqtt_sensor_bridge",
    "agrisense_app.backend.api.mqtt_bridge",
)

if TYPE_CHECKING:
    # For static analysis only - these modules are loaded dynamically at runtime
    from agrisense_app.backend.engine import RecoEngine  # type: ignore
    from agrisense_app.backend.api.mqtt_sensor_bridge import AgriSenseMQTTBridge  # type: ignore

for _path in _mqtt_import_paths:
    try:
        # dynamic import - may not be present in all deployments
        module = importlib.import_module(_path)  # type: ignore[reportMissingImports]
        AgriSenseMQTTBridge = getattr(module, "AgriSenseMQTTBridge", None)
        if AgriSenseMQTTBridge is None:
            continue
        try:
            mqtt_bridge = AgriSenseMQTTBridge()
            MQTT_BRIDGE_AVAILABLE = True
        except Exception as inst_e:
            logger.warning(f"Found AgriSenseMQTTBridge in {_path} but failed to instantiate: {inst_e}")
            mqtt_bridge = None
            MQTT_BRIDGE_AVAILABLE = False
        break
    except Exception:
        # Try next candidate import path
        continue

if not MQTT_BRIDGE_AVAILABLE:
    logger.warning("MQTT sensor bridge not available")
 
# Create router for sensor endpoints
sensor_router = APIRouter(prefix="/sensors", tags=["Real-time Sensors"])

@sensor_router.get("/live")
async def get_live_sensor_data(device_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get latest live sensor data from connected ESP32 devices
    
    Args:
        device_id: Optional specific device ID to get data for
        
    Returns:
        Latest sensor readings with timestamp
    """
    try:
        if not MQTT_BRIDGE_AVAILABLE or mqtt_bridge is None:
            raise HTTPException(status_code=503, detail="MQTT sensor bridge not available")
        
        data = mqtt_bridge.get_latest_data(device_id)
        
        if not data:
            if device_id:
                raise HTTPException(status_code=404, detail=f"No data found for device {device_id}")
            else:
                return {"message": "No sensor data available", "devices": []}
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
    except Exception as e:
        logger.error(f"Error getting live sensor data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensor data")

@sensor_router.get("/devices/status")
async def get_device_status() -> Dict[str, Any]:
    """
    Get status of all connected sensor devices
    
    Returns:
        Device connection status and last seen times
    """
    try:
        if not MQTT_BRIDGE_AVAILABLE or mqtt_bridge is None:
            raise HTTPException(status_code=503, detail="MQTT sensor bridge not available")
        
        status = mqtt_bridge.get_device_status()
        return {
            "status": "success", 
            "timestamp": datetime.now().isoformat(),
            "devices": status
        }
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve device status")

@sensor_router.post("/pump/control")
async def control_pump(device_id: str, action: str) -> Dict[str, Any]:
    """
    Control irrigation pump on specified device
    
    Args:
        device_id: Target device ID
        action: "on" or "off"
        
    Returns:
        Command status
    """
    try:
        if not MQTT_BRIDGE_AVAILABLE or mqtt_bridge is None:
            raise HTTPException(status_code=503, detail="MQTT sensor bridge not available")
        
        if action.lower() not in ["on", "off"]:
            raise HTTPException(status_code=400, detail="Action must be 'on' or 'off'")
        
        mqtt_action = f"pump_{action.lower()}"
        mqtt_bridge.send_pump_command(device_id, mqtt_action)
        
        return {
            "status": "success",
            "message": f"Pump {action} command sent to {device_id}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error controlling pump: {e}")
        raise HTTPException(status_code=500, detail="Failed to control pump")

@sensor_router.get("/recommendations/live")
async def get_live_recommendations(device_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get crop recommendations based on live sensor data
    
    Args:
        device_id: Optional device ID for specific location data
        
    Returns:
        Crop recommendations based on current sensor readings
    """
    try:
        if not MQTT_BRIDGE_AVAILABLE or mqtt_bridge is None:
            raise HTTPException(status_code=503, detail="MQTT sensor bridge not available")
        
        # Get latest sensor data
        sensor_data = mqtt_bridge.get_latest_data(device_id)

        if not sensor_data:
            raise HTTPException(status_code=404, detail="No live sensor data available")

        # Prepare defaults
        reading = None
        recommendations: Optional[Dict[str, Any]] = None

        # Normalize sensor_data to a single reading dict
        if isinstance(sensor_data, dict):
            # If device_id provided, use it, otherwise pick the first device
            if device_id:
                reading = sensor_data.get(device_id)
            else:
                device_id = list(sensor_data.keys())[0] if sensor_data else None
                reading = sensor_data.get(device_id) if device_id else None
        else:
            # sensor_data might be a single reading dict already
            reading = sensor_data

        if not reading:
            raise HTTPException(status_code=404, detail="No live reading available for the requested device")

        # Build a normalized input for the recommendation engine from the reading
        recommendation_input = {
            "plant": reading.get("plant", "generic"),
            "soil_type": reading.get("soil_type", "loam"),
            "area_m2": reading.get("area_m2", 100),
            "ph": reading.get("ph_level", reading.get("ph", 6.5)),
            "moisture_pct": reading.get("soil_moisture_percentage", reading.get("moisture_pct", 40.0)),
            "temperature_c": reading.get("soil_temperature", reading.get("temperature_c", 25.0)),
            "ec_dS_m": reading.get("ec_dS_m", 1.0),
        }

        # Import and use the recommendation engine (prefer absolute import with a fallback)
        try:
            from agrisense_app.backend.engine import RecoEngine  # type: ignore[reportMissingImports]
        except Exception:
            try:
                # runtime import fallback via importlib to avoid static-analysis complaints
                _mod = importlib.import_module("agrisense_app.backend.engine")  # type: ignore[reportMissingImports]
                RecoEngine = getattr(_mod, "RecoEngine")
            except Exception as import_err:
                logger.error(f"Failed to import RecoEngine: {import_err}")
                raise HTTPException(status_code=500, detail="Recommendation engine not available")

        try:
            engine = RecoEngine()
            recommendations = engine.recommend(recommendation_input)
        except Exception as e:
            logger.exception("Recommendation engine failed: %s", e)
            raise HTTPException(status_code=500, detail="Recommendation engine failed to generate recommendations")

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "sensor_data": reading,
            "recommendations": recommendations or {},
            "data_source": "live_sensors",
            "device_id": device_id,
        }
        
    except Exception as e:
        logger.error(f"Error getting live recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate live recommendations")

@sensor_router.get("/soil-analysis/live")
async def get_live_soil_analysis(device_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get soil analysis based on live sensor data
    
    Args:
        device_id: Optional device ID for specific location data
        
    Returns:
        Soil analysis based on current sensor readings
    """
    try:
        if not MQTT_BRIDGE_AVAILABLE or mqtt_bridge is None:
            raise HTTPException(status_code=503, detail="MQTT sensor bridge not available")
        
        # Get latest sensor data
        sensor_data = mqtt_bridge.get_latest_data(device_id)
        
        if not sensor_data:
            raise HTTPException(status_code=404, detail="No live sensor data available")
        
        # Use first device data if no specific device requested
        if isinstance(sensor_data, dict) and not device_id:
            device_id = list(sensor_data.keys())[0] if sensor_data else None
            if device_id:
                reading = sensor_data[device_id]
            else:
                raise HTTPException(status_code=404, detail="No sensor data available")
        else:
            reading = sensor_data
        
        # Analyze soil conditions
        soil_moisture = reading.get("soil_moisture_percentage", 50.0)
        soil_temp = reading.get("soil_temperature", 25.0)
        ph_level = reading.get("ph_level", 7.0)
        
        # Generate soil analysis
        analysis = {
            "moisture_status": "optimal" if 40 <= soil_moisture <= 80 else "needs_attention",
            "moisture_percentage": soil_moisture,
            "temperature_status": "optimal" if 15 <= soil_temp <= 30 else "suboptimal",
            "temperature_celsius": soil_temp,
            "ph_status": "optimal" if 6.0 <= ph_level <= 7.5 else "needs_adjustment",
            "ph_level": ph_level,
            "recommendations": []
        }
        
        # Add specific recommendations
        if soil_moisture < 40:
            analysis["recommendations"].append("Increase irrigation - soil moisture is low")
        elif soil_moisture > 80:
            analysis["recommendations"].append("Reduce irrigation - soil may be waterlogged")
        
        if ph_level < 6.0:
            analysis["recommendations"].append("Consider adding lime to increase soil pH")
        elif ph_level > 7.5:
            analysis["recommendations"].append("Consider adding sulfur to decrease soil pH")
        
        if soil_temp < 15:
            analysis["recommendations"].append("Soil temperature is low - consider mulching")
        elif soil_temp > 30:
            analysis["recommendations"].append("Soil temperature is high - increase shade/irrigation")
        
        if not analysis["recommendations"]:
            analysis["recommendations"].append("Soil conditions are optimal")
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "sensor_data": reading,
            "soil_analysis": analysis,
            "data_source": "live_sensors",
            "device_id": device_id
        }
        
    except Exception as e:
        logger.error(f"Error getting live soil analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate live soil analysis")