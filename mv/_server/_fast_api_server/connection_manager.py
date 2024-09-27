import asyncio
import json
from fastapi import WebSocket

from mv.state_machine import AbstractPublisher, get_state_server


class ConnectionManager(AbstractPublisher):
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._server = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if self._server is None:
            self._server = get_state_server(self)
            self._server.start_server()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if not self.active_connections:
            if self._server:
                self._server.stop_server()
            self._server = None

    def publish(self, state: dict):
        for connection in self.active_connections:
            value = json.dumps(state)
            asyncio.run(connection.send_text(value))


_connection_manager: None | ConnectionManager = None


def get_connection_manager():
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
