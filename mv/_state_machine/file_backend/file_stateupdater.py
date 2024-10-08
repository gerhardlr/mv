from contextlib import asynccontextmanager, contextmanager
import json
from pathlib import Path
from threading import Lock
from time import sleep
from .base import StateUpdater, State
from .state_control import (
    state_write_lock,
    cntrl_set_state_changed,
    async_state_write_lock,
)


class InFileStateUpdater(StateUpdater):
    _path = Path(".build/state.json")

    def __init__(self) -> None:
        self._file_read_lock = Lock()
        if not self._path.exists():
            if not (dir := self._path.parent).exists():
                dir.mkdir()
            self._write({})

    def _write(self, state: dict[str, State]):
        with self._file_read_lock:
            with self._path.open("w") as file:
                json.dump(state, file)

    def _read(self):
        with self._file_read_lock:
            try:
                with self._path.open("r") as file:
                    return json.load(file)
            except Exception:
                # attempt again if failed the first time
                sleep(2)
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
        with state_write_lock():
            state = self._read()
            state = state if state else {}
            # we copy the state so that it can be red statically whilst being updated
            yield state
            self._write(state)
            cntrl_set_state_changed(state)

    @asynccontextmanager
    async def async_update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        async with async_state_write_lock():
            state = self._read()
            state = state if state else {}
            # we copy the state so that it can be red statically whilst being updated
            yield state
            self._write(state)
            cntrl_set_state_changed(state)

    @contextmanager
    def atomic(self):
        original_state = self._read()
        original_state = original_state if original_state else {}
        try:
            yield
        except Exception as exception:
            self._write(original_state)
            raise exception
