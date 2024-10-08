from contextlib import asynccontextmanager, contextmanager
from .base import StateUpdater

from .state_control import (
    state_write_lock,
    cntrl_set_state_changed,
    async_state_write_lock,
)
from .memstate import get_state, set_state


class InMemStateUpdater(StateUpdater):

    @contextmanager
    def update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        with state_write_lock():
            state = get_state()
            # we copy the state so that it can be red statically whilst being updated
            yield state
            set_state(state)
            cntrl_set_state_changed(state)

    @asynccontextmanager
    async def async_update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        async with async_state_write_lock():
            state = get_state()
            # we copy the state so that it can be red statically whilst being updated
            yield state
            set_state(state)
            cntrl_set_state_changed(state)

    @contextmanager
    def atomic(self):
        original_state = get_state()
        try:
            yield
        except Exception as exception:
            set_state(original_state)
            raise exception

    def get_state(self):
        read_state = get_state()
        return read_state

    def reset_state(self):
        with self.update_state() as state:
            state.clear()
