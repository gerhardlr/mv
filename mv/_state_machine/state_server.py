import abc
import asyncio
from contextlib import contextmanager, asynccontextmanager
import json
import os
from pathlib import Path
from queue import Queue
from threading import Event, Lock, Thread
from copy import deepcopy
from typing import Any, Generator, Literal, TypeVar

from .base import AbstractPublisher

T = TypeVar("T")

_state: dict[str, T] = {}

_state_control_signals = Queue[Literal["STOP", "STATE_CHANGED"]]()

_state_write_lock = Lock()
_async_state_write_lock = asyncio.Lock()


def cntrl_set_state_changed():
    _state_control_signals.put_nowait("STATE_CHANGED")


def cntrl_set_server_stop():
    _state_control_signals.put_nowait("STOP")


class StateUpdater:

    @abc.abstractmethod
    @contextmanager
    def update_state(self) -> Generator[dict[str, T], Any, None]:
        raise NotImplementedError()

    @abc.abstractmethod
    @contextmanager
    def atomic(self) -> Generator[None, Any, None]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_state(self) -> dict[str, T]:
        raise NotImplementedError()

    @abc.abstractmethod
    def reset_state(self) -> None:
        raise NotImplementedError()

    @asynccontextmanager
    async def async_update_state() -> Generator[dict[str, T], Any, None]:
        raise NotImplementedError()

    def state_machine_is_busy(self) -> bool:
        return _async_state_write_lock.locked() or _state_write_lock.locked()


class InFileStateUpdater(StateUpdater):
    _path = Path(".build/state.json")

    def __init__(self) -> None:
        if not self._path.exists():
            if not (dir := self._path.parent).exists():
                dir.mkdir()
            self._write({})

    def _write(self, state: dict[str, Any]):
        with self._path.open("w") as file:
            json.dump(state, file)

    def _read(self):
        with self._path.open("r") as file:
            return json.load(file)

    def get_state(self):
        return self._read()

    def reset_state(self) -> None:
        self._write({})

    @contextmanager
    def update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        with _state_write_lock:
            state = self._read()
            # we copy the state so that it can be red statically whilst being updated
            yield state
            self._write(state)
            cntrl_set_state_changed()

    @asynccontextmanager
    async def async_update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        async with _async_state_write_lock:
            state = self._read()
            # we copy the state so that it can be red statically whilst being updated
            yield state
            self._write(state)
            cntrl_set_state_changed()

    @contextmanager
    def atomic(self):
        original_state = self._read()
        try:
            yield
        except Exception as exception:
            self._write(original_state)
            raise exception


class InMemStateUpdater(StateUpdater):

    @contextmanager
    def update_state(self):
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

    @asynccontextmanager
    async def async_update_state(self):
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

    @contextmanager
    def atomic(self):
        global _state
        original_state = deepcopy(_state)
        try:
            yield
        except Exception as exception:
            _state = original_state
            raise exception

    def get_state(self):
        global _state
        read_state = deepcopy(_state)
        return read_state

    def reset_state(self):
        with self.update_state() as state:
            state.clear()


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


def get_state_updater() -> StateUpdater:
    if os.getenv("PERSIST_STATE_IN_FILE"):
        return InFileStateUpdater()
    return InMemStateUpdater()


class StateServer:

    def __init__(self, publisher: AbstractPublisher):
        self._publisher = publisher
        self._started_flag = Event()
        self._server_thread: None | Thread = None
        self._updater = get_state_updater()

    def _server(self):
        while True:
            self._started_flag.set()
            signal = _state_control_signals.get()
            if signal == "STATE_CHANGED":
                state = self._updater.get_state()
                self._publisher.publish(state)
            else:
                self._started_flag.clear()
                return

    def start_server(self):
        self._server_thread = Thread(target=self._server, daemon=True)
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
