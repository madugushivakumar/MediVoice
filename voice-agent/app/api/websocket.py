import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.event_service import event_service

logger = logging.getLogger("medivoice.ws")
router = APIRouter()

@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await event_service.connect(websocket)
    try:
        while True:
            # Keep connection alive; clients may send ping or subscribe messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_service.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        event_service.disconnect(websocket)
