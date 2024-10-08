from queue import Queue
import asyncio
from contextlib import asynccontextmanager, contextmanager
from threading import Lock
from typing import Any, Literal


Signal = Literal["STOP", "STATE_CHANGED"]

_state_control_signals = Queue[tuple[Signal, Any]]()

_state_write_lock = Lock()
_async_state_write_lock = asyncio.Lock()


def cntrl_set_state_changed(state: Any):
    _state_control_signals.put_nowait(("STATE_CHANGED", state))


def cntrl_set_server_stop():
    _state_control_signals.put_nowait(("STOP", None))


def state_is_locked():
    return _async_state_write_lock.locked() or _state_write_lock.locked()


@contextmanager
def state_write_lock():
    with _state_write_lock:
        yield


@asynccontextmanager
async def async_state_write_lock():
    async with _async_state_write_lock:
        yield


def get_state_control_signals():
    return _state_control_signals.get()
