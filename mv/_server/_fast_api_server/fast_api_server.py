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
from mv.state_machine import (
    get_async_state_machine,
    StateMachineBusyError,
    CommandNotAllowed,
)
from mv.data_types import State, ObsState
from mv._server._fast_api_server.connection_manager import get_connection_manager
from mv._server._fast_api_server.data_types import DelayArgs, ConfigArgs

logger = logging.getLogger()
app = FastAPI()

manager = get_connection_manager()

state_machine = get_async_state_machine()


@app.exception_handler(StateMachineBusyError)
async def state_machine_busy_exception_handler(
    request: Request, exc: StateMachineBusyError
):
    raise HTTPException(status_code=405, detail=exc.args)


@app.exception_handler(CommandNotAllowed)
async def state_machine_command_not_allowed_error(
    request: Request, exc: CommandNotAllowed
):
    raise HTTPException(status_code=405, detail=exc.args)


@app.post("/background_switch_on")
def post_switch_on_background(
    args: DelayArgs | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.delay
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    background_tasks.add_task(state_machine.switch_on, delay)
    # state_machine.wait_busy()


@app.post("/background_switch_off")
def post_switch_off_background(
    args: DelayArgs | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.delay
    # because we return immediately we have to check the state
    state_machine.assert_ready()
    background_tasks.add_task(state_machine.switch_off, delay)


@app.post("/switch_on")
async def post_switch_on(args: DelayArgs | None = None):
    delay = args if args is None else args.get("delay")
    await state_machine.async_switch_on(delay)


@app.post("/switch_off")
async def post_switch_off(args: DelayArgs | None = None):
    delay = args if args is None else args.delay
    await state_machine.async_switch_off(delay)


@app.post("/scan")
async def post_scan(args: ConfigArgs | None = None):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    await state_machine.async_scan(delay, config)


@app.post("/background_scan")
def post_background_scan(args: ConfigArgs | None, background_tasks: BackgroundTasks):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    state_machine.assert_method_allowed(state_machine.scan)
    background_tasks.add_task(state_machine.scan, delay, config)


@app.post("/clear_config")
async def post_clear_config(args: DelayArgs | None = None):
    delay = args if args is None else args.delay
    await state_machine.async_clear_config(delay)


@app.post("/background_clear_config")
def post_background_clear_config(
    args: DelayArgs | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.delay
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    state_machine.assert_method_allowed(state_machine.clear_config)
    background_tasks.add_task(state_machine.clear_config, delay)


@app.post("/configure")
async def post_configure(
    args: ConfigArgs | None = None,
):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    await state_machine.async_configure(delay, config)


@app.post("/background_configure")
def background_post_configure(
    args: ConfigArgs | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    state_machine.assert_method_allowed(state_machine.configure)
    background_tasks.add_task(state_machine.configure, delay, config)


@app.post("/release_resources")
async def post_release_resources(args: ConfigArgs | None = None):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    await state_machine.async_release_resources(delay, config)


@app.post("/background_release_resources")
def background_post_release_resources(
    args: ConfigArgs | None, background_tasks: BackgroundTasks
):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    state_machine.assert_method_allowed(state_machine.release_resources)
    background_tasks.add_task(state_machine.release_resources, delay, config)


@app.post("/assign_resources")
async def post_assign_resources(
    args: ConfigArgs | None = None,
):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    await state_machine.async_assign_resources(delay, config)


@app.post("/background_assign_resources")
def background_post_assign_resources(
    args: ConfigArgs | None,
    background_tasks: BackgroundTasks,
):
    delay = args if args is None else args.delay
    config = args if args is None else args.config
    # because we return immediately we have to check the state
    # before pushing command to background task
    state_machine.assert_ready()
    state_machine.assert_method_allowed(state_machine.assign_resources)
    background_tasks.add_task(state_machine.assign_resources, delay, config)


@app.get("/state")
def app_get_state() -> State | None:
    return state_machine.state


@app.get("/obs_state")
def app_get_obs_state() -> ObsState | None:
    return state_machine.obs_state


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
