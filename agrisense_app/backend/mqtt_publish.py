"""Optional MQTT publisher: publish valve control commands to microcontrollers.
Topics: agrisense/<zone_id>/command
Payload example: {"action":"open","duration_s":120}
"""
import os
from typing import Dict, Any
try:
    import paho.mqtt.client as mqtt  # type: ignore
except Exception:
    mqtt = None  # type: ignore

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))

def publish_command(zone_id: str, payload: Dict[str, Any]) -> bool:
    if mqtt is None:
        return False
    try:
        from typing import Any as _Any
        # Create a short-lived client to publish the command
        client: _Any = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # type: ignore[attr-defined]
        client.connect(BROKER, PORT, 60)  # type: ignore[call-arg]
        topic = f"agrisense/{zone_id}/command"
        client.publish(topic, json_dumps(payload))  # type: ignore[call-arg]
        client.disconnect()  # type: ignore[call-arg]
        return True
    except Exception:
        return False

def json_dumps(d: Dict[str, Any]) -> str:
    try:
        import json
        return json.dumps(d)
    except Exception:
        return "{}"
