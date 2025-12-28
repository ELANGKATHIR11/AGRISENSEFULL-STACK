"""Optional MQTT bridge: subscribe to sensor topics and write to DB."""

import os
import json
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from ..core.data_store import insert_reading

load_dotenv()

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "agrisense/+/telemetry")  # + = zone wildcard


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        if "zone_id" not in data:
            # assume topic agrisense/<zone>/telemetry
            parts = msg.topic.split("/")
            if len(parts) >= 2:
                data["zone_id"] = parts[1]
        insert_reading(data)
        print("Saved reading:", data)
    except Exception as e:
        print("Failed to process message:", e)


# Use VERSION2 when present, else default constructor to avoid private import warnings in type checkers
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # type: ignore[attr-defined]
except Exception:
    client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

print(f"Subscribing to {TOPIC} on {BROKER}:{PORT}")
client.loop_forever()
