import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from mv.stack_server import get_state, async_update_state, state_machine_is_busy, AbstractPublisher, StateServer
import logging

logger = logging.getLogger()

app = FastAPI()


@app.post("/switch_on")
async def post_switch_on(args: dict[str, float] | None = None):
    if state_machine_is_busy():
        raise HTTPException(status_code=405, detail="command switch ON not allowed when State Machine is busy executing a command")
    async with async_update_state() as state:
        if args:
            delay = args["delay"]
            logger.info(f"sleeping for {delay} seconds before setting state")
            await asyncio.sleep(delay)
        state["state"] = "ON"

@app.post("/switch_off")
async def post_switch_on(args: dict[str, float] | None = None):
    if state_machine_is_busy():
        raise HTTPException(status_code=405, detail="command switch ON not allowed when State Machine is busy executing a command")
    async with async_update_state() as state:
        if args:
            delay = args["delay"]
            logger.info(f"sleeping for {delay} seconds before setting state")
            await asyncio.sleep(delay)
        state["state"] = "OFF"

@app.get("/state")
def app_get_state():
    state = get_state()
    return state.get("state")

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

manager = ConnectionManager()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)