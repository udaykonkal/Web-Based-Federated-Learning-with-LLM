from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.telemetry_service import telemetry_manager

router = APIRouter(tags=["Real-Time Telemetry & Monitoring"])

@router.get("/telemetry/recent", response_model=List[Dict[str, Any]])
async def get_recent_telemetry_events():
    """Fetch recent circular buffer telemetry events for immediate UI synchronization."""
    return telemetry_manager.get_recent_events(limit=50)

@router.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """
    Live WebSocket telemetry stream for Admin & Client monitoring (Rule 20).
    Broadcasts real-time events: ROUND_STARTED, CLIENT_TRAINING, AGGREGATION, EVALUATION.
    """
    await telemetry_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and allow client to ping or send commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "PONG"}')
    except WebSocketDisconnect:
        telemetry_manager.disconnect(websocket)
    except Exception:
        telemetry_manager.disconnect(websocket)
