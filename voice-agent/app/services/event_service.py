import json
import logging
from typing import Set, Dict, Any
from starlette.websockets import WebSocket, WebSocketState

logger = logging.getLogger("medivoice.events")

class EventService:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        if websocket.client_state != WebSocketState.CONNECTED:
            await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Dashboard client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Dashboard client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        message = json.dumps({"type": event_type, "data": data})
        to_remove = set()
        for connection in list(self.active_connections):
            try:
                if connection.client_state == WebSocketState.CONNECTED and connection.application_state != WebSocketState.DISCONNECTED:
                    await connection.send_text(message)
                else:
                    to_remove.add(connection)
            except Exception as e:
                logger.warning(f"Error broadcasting to dashboard client: {e}")
                to_remove.add(connection)
        for dead_conn in to_remove:
            self.active_connections.discard(dead_conn)

event_service = EventService()
