import asyncio
from contextlib import contextmanager
from time import sleep
from typing import Any, Callable, ParamSpec, TypeVar

from .base import AbstractPublisher, State, ObsState
from .factory import get_state_updater, get_state_server, get_state_updater_rev2

P = ParamSpec("P")
T = TypeVar("T")


class StateMachineBusyError(Exception):
    pass


def check_busy(method: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwds: P.kwargs) -> T:
        updater = get_state_updater()
        if updater.state_machine_is_busy():
            raise StateMachineBusyError(
                f"{method.__name__} not allowed when state machine is busy"
            )
        return method(*args, **kwds)

    return wrapper


class StateMachine:

    def __init__(self) -> None:
        self._state: None | State = None
        self._updater = get_state_updater()

    @contextmanager
    def _update(self, delay: float | None = None):
        with self._updater.update_state() as state:
            if delay:
                sleep(delay)
            self._state = state.get("state") if state else None
            yield
            state["state"] = self._state

    @check_busy
    def switch_on(self, delay: float | None = None):
        with self._updater.atomic():
            with self._update():
                self._state = "BUSY"
            with self._update(delay):
                self._state = "ON"

    async def async_switch_on(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_on, delay)

    @check_busy
    def switch_off(self, delay: float | None = None):
        with self._updater.atomic():
            with self._update():
                self._state = "BUSY"
            with self._update(delay):
                self._state = "OFF"

    async def async_switch_off(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_off, delay)

    @property
    def state(self):
        state = self._updater.get_state()
        return state.get("state")

    @property
    def busy(self):
        return self._updater.state_machine_is_busy() or self.state == "BUSY"

    def assert_ready(self):
        if self._updater.state_machine_is_busy():
            raise StateMachineBusyError("machine is busy and can not be commanded")

_count = -1
class StateMachine_Rev2:

    def __init__(self) -> None:
        self._state: None | State = None
        self._obs_state: None | ObsState = None
        self._updater = get_state_updater_rev2()

    @contextmanager
    def _update(self, delay: float | None = None):
        global _count
        with self._updater.update_state() as state:
            if delay:
                _count += 1
                if _count == 1:
                    pass
                sleep(delay)
            self._state = state.get("state") if state else None
            self._obs_state = state.get("obs_state") if state else None
            yield
            state["state"] = self._state
            state["obs_state"] = self._obs_state

    @check_busy
    def switch_on(self, delay: float | None = None):
        with self._updater.atomic():
            with self._update():
                self._state = "BUSY"
            with self._update(delay):
                self._state = "ON"

    @check_busy
    def assign_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        with self._updater.atomic():
            with self._update():
                self._obs_state = "BUSY"
            with self._update(delay):
                self._obs_state = "RESOURCING"
            resourcing_delay = config.get("delay") if config else None
            with self._update(resourcing_delay):
                self._obs_state = "IDLE"

    async def async_switch_on(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_on, delay)

    @check_busy
    def switch_off(self, delay: float | None = None):
        with self._updater.atomic():
            with self._update():
                self._state = "BUSY"
            with self._update(delay):
                self._state = "OFF"

    async def async_switch_off(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_off, delay)

    @property
    def state(self):
        state = self._updater.get_state()
        return state.get("state")

    @property
    def obs_state(self):
        state = self._updater.get_state()
        return state.get("obs_state")

    @property
    def busy(self):
        return (
            self._updater.state_machine_is_busy()
            or self.state == "BUSY"
            or self._obs_state == "BUSY"
        )

    def assert_ready(self):
        if self._updater.state_machine_is_busy():
            raise StateMachineBusyError("machine is busy and can not be commanded")


_state_machine: None | StateMachine | StateMachine_Rev2 = None


def get_state_machine():
    global _state_machine
    if _state_machine is None:
        _state_machine = StateMachine()
    return _state_machine


def reset_state_machine():
    global _state_machine
    _state_machine = None


def get_state_machine_rev2():
    global _state_machine
    if _state_machine is None:
        _state_machine = StateMachine_Rev2()
    return _state_machine


@contextmanager
def state_server(publisher: AbstractPublisher):
    server = get_state_server(publisher)
    server.start_server()
    yield
    server.stop_server()
