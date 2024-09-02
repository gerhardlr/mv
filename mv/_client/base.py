import abc
from typing import Any, TypeVar

T = TypeVar("T")


class AbstractObserver:

    @abc.abstractmethod
    def push_event(self, message: T):
        """"""


class AsynchAbstractObserver:

    @abc.abstractmethod
    async def push_event(self, message: T):
        """"""


class AbstractProxy:

    @abc.abstractmethod
    def subscribe(self, subscriber: Any):
        """"""

    @abc.abstractmethod
    def command_on(self, delay: float | None = None):
        """"""

    @abc.abstractmethod
    def command_off(self, delay: float | None = None):
        """"""

    @abc.abstractmethod
    def command_on_background(self, delay: float = 0):
        """"""

    @abc.abstractmethod
    def command_off_background(self, delay: float = 0):
        """"""

    @property
    @abc.abstractmethod
    def state(self):
        """"""
