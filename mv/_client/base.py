import abc
from typing import TypeVar

T = TypeVar("T")

class AbstractObserver:

    @abc.abstractmethod
    def push_event(self, message: T):
        """"""

class AsynchAbstractObserver:

    @abc.abstractmethod
    async def push_event(self, message: T):
        """"""