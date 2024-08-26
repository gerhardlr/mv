import asyncio
from contextlib import contextmanager
from time import sleep
from typing import Callable, ParamSpec, TypeVar
from .state_server import update_state, state_machine_is_busy, get_state
from .base import State

P = ParamSpec("P")
T = TypeVar("T")


class StateMachineBusyError(Exception):
    pass


def check_busy(method: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwds: P.kwargs) -> T:
        if state_machine_is_busy():
            raise StateMachineBusyError(
                f"{method.__name__} not allowed when state machine is busy"
            )
        return method(*args, **kwds)

    return wrapper


class StateMachine:

    def __init__(self) -> None:
        self._state: None | State = None

    @contextmanager
    def _update(self, delay: float | None = None):
        with update_state() as state:
            if delay:
                sleep(delay)
            self._state = state.get("state")
            yield
            state["state"] = self._state

    @check_busy
    def switch_on(self, delay: float | None = None):
        with self._update(delay):
            self._state = "ON"

    async def async_switch_on(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_on, delay)

    @check_busy
    def switch_off(self, delay: float | None = None):
        with self._update(delay):
            self._state = "OFF"

    async def async_switch_off(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_off, delay)

    @property
    def state(self):
        state = get_state()
        return state.get("state")

    @property
    def busy(self):
        return state_machine_is_busy()

    def assert_ready(self):
        if state_machine_is_busy():
            raise StateMachineBusyError("machine is busy and can not be commanded")


_state_machine: None | StateMachine = None


def get_state_machine():
    global _state_machine
    if _state_machine is None:
        _state_machine = StateMachine()
    return _state_machine
