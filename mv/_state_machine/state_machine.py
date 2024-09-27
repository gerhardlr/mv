import asyncio
from contextlib import contextmanager
from time import sleep
from typing import Any, Callable, ParamSpec, TypeVar, Concatenate

from .base import AbstractPublisher, State, ObsState
from .factory import get_state_updater, get_state_server

P = ParamSpec("P")
T = TypeVar("T")


class StateMachineBusyError(Exception):
    pass


def wraps(func: Any, wrapper: Any):
    def __get_inner_name():
        if hasattr(func, "__get_inner_name"):
            return func.__get_inner_name()
        return func.__name__

    wrapper.__get_inner_name = __get_inner_name


def get_name(func: Any):
    if hasattr(func, "__get_inner_name"):
        return func.__get_inner_name()
    return func.__name__


def check_busy(method: Callable[P, T]) -> Callable[P, T]:

    def wrapper(*args: P.args, **kwds: P.kwargs) -> T:
        updater = get_state_updater()
        if updater.state_machine_is_busy():
            method_name = get_name(method)
            raise StateMachineBusyError(
                f"{method_name} not allowed when state machine is busy"
            )
        return method(*args, **kwds)

    wraps(method, wrapper)

    return wrapper


class CommandNotAllowed(Exception):
    pass


def is_allowed(method: Callable[Concatenate["StateMachine", P], T]) -> Callable[P, T]:

    def wrapper(self: "StateMachine", *args: P.args, **kwds: P.kwargs) -> T:
        if method.__name__ in self.allowed_commands:
            return method(self, *args, **kwds)
        method_name = get_name(method)
        raise CommandNotAllowed(
            f"{method_name} not allowed when obs_state is {self.obs_state}"
        )

    wraps(method, wrapper)

    return wrapper


def ignore_if_in_state(state: State):
    def inner(method: Callable[Concatenate["StateMachine", P], T]) -> Callable[P, T]:

        def wrapper(self: "StateMachine", *args: P.args, **kwds: P.kwargs) -> T:
            if self.state == state:
                return
            return method(self, *args, **kwds)

        wraps(method, wrapper)

        return wrapper

    return inner


def ignore_if_in_obs_state(obs_state: ObsState):
    def inner(method: Callable[Concatenate["StateMachine", P], T]) -> Callable[P, T]:

        def wrapper(self: "StateMachine", *args: P.args, **kwds: P.kwargs) -> T:
            if self.obs_state == obs_state:
                return
            return method(self, *args, **kwds)

        wraps(method, wrapper)

        return wrapper

    return inner


def must_be_on(method: Callable[Concatenate["StateMachine", P], T]) -> Callable[P, T]:

    def wrapper(self: "StateMachine", *args: P.args, **kwds: P.kwargs) -> T:
        if self.state == "ON":
            return method(self, *args, **kwds)
        method_name = get_name(method)
        raise CommandNotAllowed(f"{method_name} not allowed when state is {self.state}")

    wraps(method, wrapper)

    return wrapper


class StateMachine:

    _allowed_commands: dict[ObsState | None | State, list[str]] = {
        None: ["switch_on"],
        "OFF": ["switch_on"],
        "EMPTY": ["switch_off", "assign_resources"],
        "RESOURCING": ["abort"],
        "IDLE": [
            "release_resources",
            "configure",
        ],
        "CONFIGURING": ["abort"],
        "READY": ["scan", "clear_config", "configure"],
        "SCANNING": ["abort"],
    }

    def __init__(self) -> None:
        self._state: None | State = None
        self._obs_state: None | ObsState = None
        self._updater = get_state_updater()

    @property
    def allowed_commands(self) -> list[str]:
        return self._allowed_commands.get(self.obs_state)

    @contextmanager
    def _update(self, delay: float | None = None):
        with self._updater.update_state() as state:
            if delay:
                sleep(delay)
            self._state = state.get("state") if state else None
            self._obs_state = state.get("obs_state") if state else None
            yield
            state["state"] = self._state
            state["obs_state"] = self._obs_state

    @ignore_if_in_state("ON")
    @check_busy
    @is_allowed
    def switch_on(self, delay: float | None = None):
        with self._updater.atomic():
            with self._update():
                self._state = "BUSY"
            with self._update(delay):
                self._state = "ON"
                self._obs_state = "EMPTY"

    def abort(self):
        raise NotImplementedError()

    @ignore_if_in_obs_state("IDLE")
    @must_be_on
    @check_busy
    @is_allowed
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

    @ignore_if_in_obs_state("EMPTY")
    @must_be_on
    @check_busy
    @is_allowed
    def release_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        with self._updater.atomic():
            with self._update():
                self._obs_state = "BUSY"
            with self._update(delay):
                self._obs_state = "RESOURCING"
            resourcing_delay = config.get("delay") if config else None
            with self._update(resourcing_delay):
                self._obs_state = "EMPTY"

    @must_be_on
    @check_busy
    @is_allowed
    def configure(self, delay: float | None = None, config: dict[str, Any] = None):
        with self._updater.atomic():
            with self._update():
                self._obs_state = "BUSY"
            with self._update(delay):
                self._obs_state = "CONFIGURING"
            resourcing_delay = config.get("delay") if config else None
            with self._update(resourcing_delay):
                self._obs_state = "READY"

    @ignore_if_in_obs_state("IDLE")
    @must_be_on
    @check_busy
    @is_allowed
    def clear_config(self, delay: float | None = None):
        with self._updater.atomic():
            with self._update():
                self._obs_state = "BUSY"
            with self._update(delay):
                self._obs_state = "IDLE"

    @ignore_if_in_obs_state("SCANNING")
    @must_be_on
    @check_busy
    @is_allowed
    def scan(self, delay: float | None = None, config: dict[str, Any] = None):
        with self._updater.atomic():
            with self._update():
                self._obs_state = "BUSY"
            with self._update(delay):
                self._obs_state = "SCANNING"
            resourcing_delay = config.get("delay") if config else None
            with self._update(resourcing_delay):
                self._obs_state = "READY"

    async def async_switch_on(self, delay: float | None = None):
        await asyncio.to_thread(self.switch_on, delay)

    @ignore_if_in_state("OFF")
    @check_busy
    @is_allowed
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


_state_machine: None | StateMachine = None


def get_state_machine():
    global _state_machine
    if _state_machine is None:
        _state_machine = StateMachine()
    return _state_machine


def reset_state_machine():
    global _state_machine
    _state_machine = None


@contextmanager
def state_server(publisher: AbstractPublisher):
    server = get_state_server(publisher)
    server.start_server()
    yield
    server.stop_server()
