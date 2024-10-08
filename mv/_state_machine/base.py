import abc
from contextlib import contextmanager
from typing import Generator, Literal, TypedDict

State = Literal["ON", "OFF", "BUSY"]
ObsState = Literal[
    "EMPTY", "RESOURCING", "IDLE", "CONFIGURING", "READY", "SCANNING", "BUSY"
]

Attribute = Literal["state", "obs_state"]


class CombinedState(TypedDict):
    state: State
    obs_state: ObsState


class StateSubscriber:

    def __init__(self) -> None:
        self._init_state = None

    @abc.abstractmethod
    def push_event(self, event: CombinedState):
        """"""

    def init(self, state: CombinedState):
        """"""
        self._init_state = state

    @property
    def init_state(self):
        if self._init_state:
            return self._init_state["state"]

    @property
    def init_obs_state(self):
        if self._init_state:
            return self._init_state["obs_state"]


class AbstractPublisher:

    @abc.abstractmethod
    def publish(self, state: CombinedState):
        """"""


class AbstractStateUpdater:

    @abc.abstractmethod
    @contextmanager
    def update_state(
        self,
    ) -> Generator[CombinedState, None, None]:
        raise NotImplementedError()

    @abc.abstractmethod
    @contextmanager
    def atomic(self) -> Generator[None, None, None]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_state(self) -> CombinedState:
        raise NotImplementedError()

    @abc.abstractmethod
    def reset_state(self) -> None:
        raise NotImplementedError()
        """"""

    @abc.abstractmethod
    def state_machine_is_busy(self) -> bool:
        """"""


class AbstractStateServer:

    @abc.abstractmethod
    def start_server(self):
        """"""

    @abc.abstractmethod
    def stop_server(self):
        """"""


class AbstractFactory:

    @abc.abstractmethod
    def get_state_updater(self) -> AbstractStateUpdater:
        """"""

    @abc.abstractmethod
    def get_state_server(self, publisher: AbstractPublisher) -> AbstractStateServer:
        """"""
