import uvicorn
from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
    Request,
)

import logging
import os
from mv.state_machine import get_state_machine, StateMachineBusyError

from mv._server._fast_api_server.connection_manager import get_connection_manager


logger = logging.getLogger()
app = FastAPI()

manager = get_connection_manager()

state_machine = get_state_machine()


@app.exception_handler(StateMachineBusyError)
async def state_machine_busy_exception_handler(
    request: Request, exc: StateMachineBusyError
):
    raise HTTPException(status_code=405, detail=exc.args)


@app.post("/background_switch_on")
def post_switch_on_background(
    args: dict[str, float] | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.get("delay")
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    background_tasks.add_task(state_machine.switch_on, delay)


@app.post("/background_switch_off")
def post_switch_off_background(
    args: dict[str, float] | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.get("delay")
    # because we return immediately we have to check the state
    state_machine.assert_ready()
    background_tasks.add_task(state_machine.switch_off, delay)


@app.post("/switch_on")
async def post_switch_on(args: dict[str, float] | None = None):
    delay = args if args is None else args.get("delay")
    await state_machine.async_switch_on(delay)


@app.post("/switch_off")
async def post_switch_off(args: dict[str, float] | None = None):
    delay = args if args is None else args.get("delay")
    await state_machine.async_switch_off(delay)


@app.get("/state")
def app_get_state():
    return state_machine.state


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
    if log_level := os.getenv("LOG_LEVEL") == "debug":
        uvicorn.run(app, host="0.0.0.0", port=30000, log_level=log_level)
    else:
        uvicorn.run(app, host="0.0.0.0", port=30000)
