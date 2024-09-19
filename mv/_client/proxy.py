import abc
import asyncio
from fastapi.testclient import TestClient
from .ws_listener import AsyncWSListener, WSListener
from .base import AbstractObserver, AsynchAbstractObserver, AbstractProxy

from mv.state_machine import StateSubscriber, State


class ProxyObserver(AbstractObserver):
    def __init__(self) -> None:
        self._subscribers: list[StateSubscriber] = []
        # TODO add remove subscription (unsubcribe)
        self._index = -1

    def push_event(self, message: State):
        for subscriber in self._subscribers:
            subscriber.push_event(message)

    def subscribe(self, subscriber: StateSubscriber):
        self._subscribers.append(subscriber)
        self._index += 1
        return self._index


class AsynchProxyObserver(AsynchAbstractObserver):
    def __init__(self) -> None:
        self._subscribers: list[StateSubscriber] = []
        # TODO add remove subscription (unsubcribe)
        self._index = -1

    async def push_event(self, message: State):
        for subscriber in self._subscribers:
            subscriber.push_event(message)

    def subscribe(self, subscriber: StateSubscriber):
        self._subscribers.append(subscriber)
        self._index += 1
        return self._index


class BaseProxy(AbstractProxy):

    def __init__(self, client: TestClient) -> None:
        self._client = client

    @abc.abstractmethod
    def subscribe(self, subscriber: StateSubscriber):
        """"""

    def command_on(self, delay: float | None = None):
        json = {"delay": delay} if delay else delay
        result = self._client.post("switch_on", json=json)
        result.raise_for_status()

    def command_off(self, delay: float | None = None):
        json = {"delay": delay} if delay else delay
        result = self._client.post("switch_off", json=json)
        result.raise_for_status()

    def command_on_background(self, delay: float = 0):
        json = {"delay": delay}
        result = self._client.post("background_switch_on", json=json)
        result.raise_for_status()

    def command_off_background(self, delay: float = 0):
        json = {"delay": delay}
        result = self._client.post("background_switch_off", json=json)
        result.raise_for_status()

    async def async_command_on(self, delay: float | None = None):
        await asyncio.to_thread(self.command_on, delay)

    async def async_command_off(self, delay: float | None = None):
        await asyncio.to_thread(self.command_off, delay)

    @property
    def state(self):
        result = self._client.get("state")
        result.raise_for_status()
        return result.json()


class Proxy(BaseProxy, WSListener):

    def __init__(self, client: TestClient) -> None:
        super().__init__(client)
        self._proxy_observer = ProxyObserver()
        WSListener.__init__(self, self._proxy_observer)

    def subscribe(self, subscriber: StateSubscriber):
        return self._proxy_observer.subscribe(subscriber)


class AsyncProxy(BaseProxy, AsyncWSListener):

    def __init__(self, client: TestClient) -> None:
        BaseProxy.__init__(self, client)
        self._proxy_observer = AsynchProxyObserver()
        AsyncWSListener.__init__(self, self._proxy_observer)

    def subscribe(self, subscriber: StateSubscriber):
        return self._proxy_observer.subscribe(subscriber)
