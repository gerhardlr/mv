import abc
import asyncio
from contextlib import contextmanager, asynccontextmanager
from queue import Queue
from threading import Event, Lock, Thread
from copy import deepcopy
from typing import Literal, TypeVar

from .base import AbstractPublisher

T = TypeVar("T")

_state: dict[str,T] = {}

_state_control_signals = Queue[Literal["STOP","STATE_CHANGED"]]()

_state_write_lock = Lock()
_async_state_write_lock = asyncio.Lock()


def cntrl_set_state_changed():
    _state_control_signals.put_nowait("STATE_CHANGED")

def cntrl_set_server_stop():   
    _state_control_signals.put_nowait("STOP")


def get_state():
    global _state
    read_state = deepcopy(_state)
    return read_state


@contextmanager
def update_state():
    # only one thread at a time can write or update the state
    # after a write, a signal is sent indicating the state has changed
    # once the signal is sent the update state lock is released
    global _state
    with _state_write_lock:
        state = deepcopy(_state)
        # we copy the state so that it can be red statically whilst being updated
        yield state
        _state = state
        cntrl_set_state_changed()

def reset_state():
    with update_state() as state:
        state = {}

def state_machine_is_busy() -> bool:
    return (_async_state_write_lock.locked() or _state_write_lock.locked())

@asynccontextmanager
async def async_update_state():
    # only one thread at a time can write or update the state
    # after a write, a signal is sent indicating the state has changed
    # once the signal is sent the update state lock is released
    global _state
    async with _async_state_write_lock:
        state = deepcopy(_state)
        # we copy the state so that it can be red statically whilst being updated
        yield state
        _state = state
        cntrl_set_state_changed()


class StateServer():

    def __init__(self, publisher: AbstractPublisher):
        self._publisher = publisher
        self._started_flag = Event()
        self._server_thread: None | Thread = None

    def _server(self):
        while True:
            self._started_flag.set()
            signal = _state_control_signals.get()
            if signal == "STATE_CHANGED":
                state = get_state()
                self._publisher.publish(state)
            else:
                self._started_flag.clear()
                return
            
    def start_server(self):
        self._server_thread = Thread(target = self._server, daemon=True)
        self._server_thread.start()
        self._started_flag.wait()

    def stop_server(self):
        cntrl_set_server_stop()
        if self._server_thread:
            self._server_thread.join(1)


@contextmanager
def state_server(publisher: AbstractPublisher):
    server = StateServer(publisher)
    server.start_server()
    yield
    server.stop_server()
