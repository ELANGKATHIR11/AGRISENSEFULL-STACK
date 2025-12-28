"""Minimal MQTT bridge stub used when the real MQTT bridge is not available.

This stub provides the same public API used by sensor_api.py so static analysis
and runtime imports succeed in lightweight dev environments.
"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AgriSenseMQTTBridge:
    def __init__(self):
        logger.info("Using MQTT stub bridge (no broker configured)")
        self.client = None

    def get_latest_data(self, device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Return no data by default; callers should handle 404/empty results
        return None

    def get_latest_reading(self, device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return None

    def get_device_status(self) -> Dict[str, Any]:
        return {}

    def publish_reading(self, payload: Dict[str, Any]) -> str:
        logger.debug("MQTT stub received reading publish request")
        return "stub-msg-id"

    def send_pump_command(self, device_id: str, action: str) -> None:
        logger.info(f"MQTT stub: pretend sending {action} to {device_id}")
