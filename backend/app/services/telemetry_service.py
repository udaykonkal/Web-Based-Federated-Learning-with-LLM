from datetime import datetime, timezone
from typing import Dict, Any, List, Set
from collections import deque
import json
from fastapi import WebSocket

class TelemetryManager:
    """
    Real-Time WebSocket & Telemetry Event Manager (Rules 20, 35).
    Maintains active WebSocket subscriber connections and an in-memory audit log of the most recent 50 events.
    """
    def __init__(self, max_history: int = 50):
        self.active_connections: Set[WebSocket] = set()
        self.history: deque = deque(maxlen=max_history)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Send initial event history snapshot upon connecting
        try:
            initial_payload = {
                "type": "INITIAL_SYNC",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "events": list(self.history)
            }
            await websocket.send_text(json.dumps(initial_payload))
        except Exception:
            pass

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast a telemetry event to all active WebSocket clients."""
        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        self.history.append(event)

        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(event))
            except Exception:
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.history)[-limit:]

telemetry_manager = TelemetryManager()

async def emit_telemetry(event_type: str, data: Dict[str, Any]):
    """Global helper to broadcast an authentic round or client telemetry event."""
    await telemetry_manager.broadcast(event_type, data)
