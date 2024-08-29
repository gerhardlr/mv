from contextlib import asynccontextmanager, contextmanager
import json
from pathlib import Path
from typing import Any
from .base import StateUpdater
from .state import state_write_lock, cntrl_set_state_changed, async_state_write_lock


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
        with state_write_lock():
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
        async with async_state_write_lock():
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
