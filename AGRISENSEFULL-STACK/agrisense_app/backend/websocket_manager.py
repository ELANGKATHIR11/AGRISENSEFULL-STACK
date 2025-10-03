"""
WebSocket implementation for real-time updates in AgriSense
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import logging

logger = logging.getLogger(__name__)

# WebSocket connection manager


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Accept WebSocket connection and add to pool"""
        await websocket.accept()

        if not client_id:
            client_id = f"client_{datetime.utcnow().timestamp()}"

        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()

        self.active_connections[client_id].add(websocket)
        self.user_connections[websocket] = client_id

        logger.info(f"WebSocket connected: {client_id}")

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "message": "Connected to AgriSense real-time updates",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        return client_id

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection from pool"""
        client_id = self.user_connections.get(websocket)
        if client_id and client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        if websocket in self.user_connections:
            del self.user_connections[websocket]

        logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def send_to_client(self, message: Dict[str, Any], client_id: str):
        """Send message to all connections of a specific client"""
        if client_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected.add(connection)

            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast(self, message: Dict[str, Any], exclude_client: Optional[str] = None):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for client_id, connections in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue

            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.add(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_channel(self, channel: str, payload: Any, exclude_client: Optional[str] = None):
        """Broadcast message to specific channel subscribers"""
        message = {"channel": channel, "payload": payload, "timestamp": datetime.utcnow().isoformat()}

        await self.broadcast(message, exclude_client)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_client_count(self) -> int:
        """Get number of unique clients"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()

# WebSocket router
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication"""
    client_id = None
    try:
        client_id = await manager.connect(websocket)

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_client_message(websocket, client_id, message)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format", "timestamp": datetime.utcnow().isoformat()},
                    websocket,
                )
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": "Internal server error", "timestamp": datetime.utcnow().isoformat()},
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle incoming messages from WebSocket clients"""
    message_type = message.get("type")

    if message_type == "ping":
        # Handle ping/pong for connection keep-alive
        await manager.send_personal_message({"type": "pong", "timestamp": datetime.utcnow().isoformat()}, websocket)

    elif message_type == "subscribe":
        # Handle channel subscription
        channel = message.get("channel")
        if channel:
            await manager.send_personal_message(
                {
                    "type": "subscribed",
                    "channel": channel,
                    "message": f"Subscribed to {channel}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                websocket,
            )

    elif message_type == "request_data":
        # Handle data requests
        data_type = message.get("data_type")
        if data_type:
            await handle_data_request(websocket, client_id, data_type, message)
        else:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "data_type is required for request_data",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                websocket,
            )

    else:
        await manager.send_personal_message(
            {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )


async def handle_data_request(websocket: WebSocket, client_id: str, data_type: str, message: Dict[str, Any]):
    """Handle specific data requests from clients"""
    from .database_enhanced import get_cached_sensor_reading, get_cached_recommendation, get_cached_weather_data

    if data_type == "sensor_data":
        zone_id = message.get("zone_id", "default")
        data = await get_cached_sensor_reading(zone_id)

        await manager.send_personal_message(
            {
                "type": "data_response",
                "data_type": "sensor_data",
                "zone_id": zone_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

    elif data_type == "recommendation":
        zone_id = message.get("zone_id", "default")
        data = await get_cached_recommendation(zone_id)

        await manager.send_personal_message(
            {
                "type": "data_response",
                "data_type": "recommendation",
                "zone_id": zone_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

    elif data_type == "weather":
        location = message.get("location", "default")
        data = await get_cached_weather_data(location)

        await manager.send_personal_message(
            {
                "type": "data_response",
                "data_type": "weather",
                "location": location,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

    else:
        await manager.send_personal_message(
            {"type": "error", "message": f"Unknown data type: {data_type}", "timestamp": datetime.utcnow().isoformat()},
            websocket,
        )


# Broadcasting functions for different data types


async def broadcast_sensor_update(zone_id: str, sensor_data: Dict[str, Any]):
    """Broadcast sensor data update to all connected clients"""
    await manager.broadcast_to_channel("sensor_data", {"zone_id": zone_id, "data": sensor_data})


async def broadcast_recommendation_update(zone_id: str, recommendation: Dict[str, Any]):
    """Broadcast recommendation update to all connected clients"""
    await manager.broadcast_to_channel("recommendation", {"zone_id": zone_id, "data": recommendation})


async def broadcast_tank_level_update(tank_id: str, level_data: Dict[str, Any]):
    """Broadcast tank level update to all connected clients"""
    await manager.broadcast_to_channel("tank_level", {"tank_id": tank_id, "data": level_data})


async def broadcast_alert(alert_data: Dict[str, Any]):
    """Broadcast alert to all connected clients"""
    await manager.broadcast_to_channel("alerts", alert_data)


async def broadcast_weather_update(location: str, weather_data: Dict[str, Any]):
    """Broadcast weather update to all connected clients"""
    await manager.broadcast_to_channel("weather", {"location": location, "data": weather_data})


async def broadcast_irrigation_status(zone_id: str, status: Dict[str, Any]):
    """Broadcast irrigation status change to all connected clients"""
    await manager.broadcast_to_channel("irrigation", {"zone_id": zone_id, "status": status})


async def broadcast_system_status(status: Dict[str, Any]):
    """Broadcast system status update to all connected clients"""
    await manager.broadcast_to_channel("system_status", status)


# Background task for periodic updates


async def periodic_status_broadcast():
    """Send periodic status updates to maintain connection health"""
    while True:
        try:
            await asyncio.sleep(30)  # Send status every 30 seconds

            status = {
                "type": "system_heartbeat",
                "connected_clients": manager.get_client_count(),
                "total_connections": manager.get_connection_count(),
                "timestamp": datetime.utcnow().isoformat(),
            }

            await manager.broadcast(status)

        except Exception as e:
            logger.error(f"Error in periodic status broadcast: {e}")
            await asyncio.sleep(10)


# WebSocket utilities


async def send_notification(client_id: str, title: str, message: str, type: str = "info"):
    """Send notification to specific client"""
    notification = {
        "type": "notification",
        "notification": {"title": title, "message": message, "type": type, "timestamp": datetime.utcnow().isoformat()},
    }

    await manager.send_to_client(notification, client_id)


async def broadcast_notification(title: str, message: str, type: str = "info", exclude_client: Optional[str] = None):
    """Broadcast notification to all clients"""
    notification = {
        "type": "notification",
        "notification": {"title": title, "message": message, "type": type, "timestamp": datetime.utcnow().isoformat()},
    }

    await manager.broadcast(notification, exclude_client)


# Connection status endpoint


async def get_websocket_status() -> Dict[str, Any]:
    """Get WebSocket connection status"""
    return {
        "status": "active",
        "connected_clients": manager.get_client_count(),
        "total_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }
