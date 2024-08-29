from queue import Queue
import asyncio
from contextlib import asynccontextmanager, contextmanager
from threading import Lock
from typing import Any, Literal
from copy import deepcopy


State = Literal["ON", "OFF", "BUSY"]


_state: dict[str, Any] = {}

Signal = Literal["STOP", "STATE_CHANGED"]

_state_control_signals = Queue[Signal]()

_state_write_lock = Lock()
_async_state_write_lock = asyncio.Lock()


def get_state():
    global _state
    state_copy = deepcopy(_state)
    return state_copy


def set_state(state: dict[str, Any]):
    global _state
    _state = state


def cntrl_set_state_changed():
    _state_control_signals.put_nowait("STATE_CHANGED")


def cntrl_set_server_stop():
    _state_control_signals.put_nowait("STOP")


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
