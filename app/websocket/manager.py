from typing import Dict, List

from fastapi import WebSocket

class ConnectionManager:
    """
    Tracks active WebSocket connections per session_id, and broadcasts messages
    to everyone currently connected to that session's live feed.
    """
     
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id:str, websocket:WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(session_id, []).append(websocket)

    def disconnect(self, session_id:str, websocket:WebSocket):
        connections = self.active_connections.get(session_id)
        if not connections:
            return
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            del self.active_connections[session_id]

    async def broadcast(self, session_id, message:dict):
        connections = self.active_connections.get(session_id, [])
        stale = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(session_id, connection)

manager = ConnectionManager()