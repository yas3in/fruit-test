"""Real-time event broadcasting and WebSocket connection manager."""

import asyncio
from datetime import datetime, timezone
import json
from typing import Dict, List, Any, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections for real-time dashboard updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast JSON payload to all connected clients."""
        async with self._lock:
            dead_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)


class EventBus:
    """Central event bus for publishing activities, worker status, and alerts."""

    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager
        self.subscribers: List[asyncio.Queue] = []

    async def publish(
        self,
        event_type: str,
        account_id: Optional[str] = None,
        account_name: Optional[str] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "INFO"
    ):
        event_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "account_id": account_id,
            "account_name": account_name or "System",
            "message": message,
            "metadata": metadata or {},
            "priority": priority
        }

        # Send over WebSockets
        await self.ws_manager.broadcast(event_payload)

        # Broadcast to local subscribers (e.g. background listeners)
        for queue in self.subscribers:
            await queue.put(event_payload)


ws_manager = ConnectionManager()
event_bus = EventBus(ws_manager)
