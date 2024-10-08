import abc
import asyncio
from typing import Any, Tuple
from fastapi.testclient import TestClient
from .ws_listener import AsyncWSListener, WSListener
from .base import (
    AbstractObserver,
    AbstractProxy,
    AsynchAbstractObserver,
    DelayArgs,
    ConfigArgs,
    StateSubscriber,
    CombinedState,
    Attribute,
)


class ProxyObserver(AbstractObserver):
    def __init__(self) -> None:
        self._subscribers: list[Tuple[StateSubscriber, Attribute]] = []
        # TODO add remove subscription (unsubcribe)
        self._index = -1
        self.previous: dict[Attribute, str] = {}

    def push_event(self, data: CombinedState):
        if len(self._subscribers) == 0:
            self.previous["state"] = data["state"]
            self.previous["obs_state"] = data["obs_state"]
        for subscriber, attribute in self._subscribers:
            value = data[attribute]
            if current := self.previous.get(attribute):
                if current != value:
                    # only push change events
                    subscriber.push_event(value)
                    self.previous[attribute] = value
            else:
                # we push first time values
                subscriber.push_event(value)
                self.previous[attribute] = value

    def subscribe(self, subscriber: StateSubscriber, attribute: Attribute = "state"):
        self._subscribers.append((subscriber, attribute))
        self._index += 1
        return self._index


class AsynchProxyObserver(AsynchAbstractObserver):
    def __init__(self) -> None:
        self._subscribers: list[Tuple[StateSubscriber, Attribute]] = []
        # TODO add remove subscription (unsubcribe)
        self._index = -1
        self.previous: dict[Attribute, str] = {}

    async def push_event(self, data: CombinedState):
        for subscriber, attribute in self._subscribers:
            value = data[attribute]
            if current := self.previous.get(attribute):
                if current != value:
                    # only push change events
                    subscriber.push_event(value)
                    self.previous[attribute] = value
            else:
                # we push first time values
                subscriber.push_event(value)
                self.previous[attribute] = value

    def subscribe(self, subscriber: StateSubscriber, attribute: Attribute = "state"):
        self._subscribers.append((subscriber, attribute))
        self._index += 1
        return self._index


class BaseProxy(AbstractProxy):

    def __init__(self, client: TestClient) -> None:
        self._client = client

    @abc.abstractmethod
    def subscribe(self, subscriber: StateSubscriber, attribute: Attribute = "state"):
        """"""

    def command_on(self, delay: float | None = None):
        json = DelayArgs(delay=delay).model_dump() if delay else None
        result = self._client.post("switch_on", json=json)
        result.raise_for_status()

    def command_on_background(self, delay: float = 0):
        json = DelayArgs(delay=delay).model_dump()
        result = self._client.post("background_switch_on", json=json)
        result.raise_for_status()

    def command_off(self, delay: float | None = None):
        json = DelayArgs(delay=delay).model_dump() if delay else None
        result = self._client.post("switch_off", json=json)
        result.raise_for_status()

    def command_off_background(self, delay: float = 0):
        json = DelayArgs(delay=delay).model_dump()
        result = self._client.post("background_switch_off", json=json)
        result.raise_for_status()

    def command_assign_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("assign_resources", json=json)
        result.raise_for_status()

    def command_background_assign_resources(
        self, delay: float, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("background_assign_resources", json=json)
        result.raise_for_status()

    def command_release_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("release_resources", json=json)
        result.raise_for_status()

    def command_background_release_resources(
        self, delay: float, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("background_release_resources", json=json)
        result.raise_for_status()

    def command_configure(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("configure", json=json)
        result.raise_for_status()

    def command_background_configure(
        self, delay: float, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("background_configure", json=json)
        result.raise_for_status()

    def command_clear_config(self, delay: float | None = None):
        json = DelayArgs(delay=delay).model_dump() if delay else None
        result = self._client.post("clear_config", json=json)
        result.raise_for_status()

    def command_background_clear_config(
        self, delay: float, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("background_clear_config", json=json)
        result.raise_for_status()

    def command_scan(self, delay: float, config: dict[str, Any] = None):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("switch_on", json=json)
        result.raise_for_status()

    def command_background_scan(
        self, delay: float, config: dict[str, Any] = None
    ):
        json = ConfigArgs(delay=delay, config=config).model_dump() if delay else None
        result = self._client.post("background_scan", json=json)
        result.raise_for_status()

    @property
    def state(self):
        result = self._client.get("state")
        result.raise_for_status()
        return result.json()

    @property
    def obs_state(self):
        result = self._client.get("obs_state")
        result.raise_for_status()
        return result.json()


class Proxy(BaseProxy, WSListener):

    def __init__(self, client: TestClient) -> None:
        super().__init__(client)
        self._proxy_observer = ProxyObserver()
        WSListener.__init__(self, self._proxy_observer)

    def subscribe(self, subscriber: StateSubscriber, attribute: Attribute = "state"):
        init_state: CombinedState = {}
        init_state["obs_state"] = self.obs_state
        init_state["state"] = self.state
        subscriber.init(init_state)
        return self._proxy_observer.subscribe(subscriber, attribute)


class AsyncProxy(BaseProxy, AsyncWSListener):

    def __init__(self, client: TestClient) -> None:
        BaseProxy.__init__(self, client)
        self._proxy_observer = AsynchProxyObserver()
        AsyncWSListener.__init__(self, self._proxy_observer)

    def subscribe(self, subscriber: StateSubscriber, attribute: Attribute = "state"):
        init_state: CombinedState = {}
        init_state["obs_state"] = self.obs_state
        init_state["state"] = self.state
        subscriber.init(init_state)
        return self._proxy_observer.subscribe(subscriber, attribute)

    async def async_command_on(self, delay: float | None = None):
        await asyncio.to_thread(self.command_on, delay)

    async def async_command_off(self, delay: float | None = None):
        await asyncio.to_thread(self.command_off, delay)
