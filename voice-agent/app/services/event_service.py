import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("medivoice.events")

class EventService:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
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
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                to_remove.add(connection)
        for dead_conn in to_remove:
            self.active_connections.discard(dead_conn)

event_service = EventService()
