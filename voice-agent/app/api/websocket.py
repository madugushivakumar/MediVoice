import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from app.services.event_service import event_service

logger = logging.getLogger("medivoice.ws")
router = APIRouter()

@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await event_service.connect(websocket)
    try:
        while True:
            # Keep connection alive; clients send ping every 25s
            data = await websocket.receive_text()
            if data == "ping":
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_service.disconnect(websocket)
    except Exception as e:
        logger.debug(f"Dashboard WebSocket disconnected: {e}")
        event_service.disconnect(websocket)
