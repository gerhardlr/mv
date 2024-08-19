import asyncio
from fastapi import  WebSocket

from mv.stack_server import AbstractPublisher, StateServer

class ConnectionManager(AbstractPublisher):
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._server = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if self._server is None:
            self._server  = StateServer(self)
            self._server.start_server()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if not self.active_connections:
            self._server.stop_server()
            self._server = None

    def publish(self, state: dict):
        for connection in self.active_connections:
            value = state["state"]
            asyncio.run(connection.send_text(value))