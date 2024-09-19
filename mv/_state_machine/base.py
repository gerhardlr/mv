import abc
from contextlib import contextmanager
from typing import Any, Generator


class StateSubscriber:

    @abc.abstractmethod
    def push_event(self, event: Any):
        """"""


class AbstractPublisher:

    @abc.abstractmethod
    def publish(self, state):
        """"""


class AbstractStateUpdater:

    @abc.abstractmethod
    @contextmanager
    def update_state(self) -> Generator[dict[str, Any], Any, None]:
        raise NotImplementedError()

    @abc.abstractmethod
    @contextmanager
    def atomic(self) -> Generator[None, Any, None]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_state(self) -> dict[str, Any]:
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
