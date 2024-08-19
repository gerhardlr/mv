import asyncio
from time import sleep
import uvicorn
from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks
)
from mv.stack_server import (
    get_state,
    async_update_state,
    state_machine_is_busy,
    update_state
)
import logging

from mv.fastapi_ws_helpers import ConnectionManager

logger = logging.getLogger()
app = FastAPI()

manager = ConnectionManager()



def backgorund_switch_on(args: dict[str, float] | None = None):
    with update_state() as state:
        if args:
            delay = args["delay"]
            sleep(delay)
        state["state"] = "ON"

def backgorund_switch_off(args: dict[str, float] | None = None):
    with update_state() as state:
        if args:
            delay = args["delay"]
            sleep(delay)
        state["state"] = "OFF"

@app.post("/background_switch_on")
def post_switch_on_background(args: dict[str, float], background_tasks: BackgroundTasks):
    background_tasks.add_task(backgorund_switch_on, args)
    

@app.post("/background_switch_off")
def post_switch_off_background(args: dict[str, float], background_tasks: BackgroundTasks):
    background_tasks.add_task(backgorund_switch_off, args)



@app.post("/switch_on")
async def post_switch_on(args: dict[str, float] | None = None):
    if state_machine_is_busy():
        raise HTTPException(status_code=405, detail="command switch ON not allowed when State Machine is busy executing a command")
    async with async_update_state() as state:
        if args:
            delay = args["delay"]
            await asyncio.sleep(delay)
        state["state"] = "ON"

@app.post("/switch_off")
async def post_switch_on(args: dict[str, float] | None = None):
    if state_machine_is_busy():
        raise HTTPException(status_code=405, detail="command switch ON not allowed when State Machine is busy executing a command")
    async with async_update_state() as state:
        if args:
            delay = args["delay"]
            await asyncio.sleep(delay)
        state["state"] = "OFF"

@app.get("/state")
def app_get_state():
    state = get_state()
    return state.get("state")


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