"""
WebSocket endpoints for real-time event streaming.
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.core.event_bus import event_bus
from app.core.security import TokenManager

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"✓ WebSocket connected: {client_id}")
    
    async def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"✓ WebSocket disconnected: {client_id}")
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        disconnected = []
        for client_id, conn in self.active_connections.items():
            try:
                await conn.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                disconnected.append(client_id)
        
        for client_id in disconnected:
            await self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_endpoint_events(websocket: WebSocket, token: str = Query(None)):
    """WebSocket endpoint for real-time event streaming"""
    if not token or not TokenManager.verify_token(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    client_id = f"event-{id(websocket)}"
    
    try:
        await manager.connect(websocket, client_id)
        while True:
            data = await websocket.receive_text()
            try:
                json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(client_id)
