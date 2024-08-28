import abc
import asyncio
from contextlib import contextmanager, asynccontextmanager
import json
import os
from pathlib import Path
from queue import Queue
from threading import Event, Lock, Thread
from copy import deepcopy
from typing import Any, Generator, Literal, TypeVar, cast

import fakeredis

import redis
from redis.lock import Lock as RedisLock
from redis.client import PubSub, PubSubWorkerThread
import redis.asyncio as asyncio_redis

from .base import AbstractPublisher
from . import config

T = TypeVar("T")

_state: dict[str, Any] = {}

Signal = Literal["STOP", "STATE_CHANGED"]

_state_control_signals = Queue[Signal]()

_state_write_lock = Lock()
_async_state_write_lock = asyncio.Lock()


def cntrl_set_state_changed():
    _state_control_signals.put_nowait("STATE_CHANGED")


def cntrl_set_server_stop():
    _state_control_signals.put_nowait("STOP")


class StateUpdater:

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

    def state_machine_is_busy(self) -> bool:
        return _async_state_write_lock.locked() or _state_write_lock.locked()


class InFileStateUpdater(StateUpdater):
    _path = Path(".build/state.json")

    def __init__(self) -> None:
        if not self._path.exists():
            if not (dir := self._path.parent).exists():
                dir.mkdir()
            self._write({})

    def _write(self, state: dict[str, Any]):
        with self._path.open("w") as file:
            json.dump(state, file)

    def _read(self):
        with self._path.open("r") as file:
            return json.load(file)

    def get_state(self):
        return self._read()

    def reset_state(self) -> None:
        self._write({})

    @contextmanager
    def update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        with _state_write_lock:
            state = self._read()
            # we copy the state so that it can be red statically whilst being updated
            yield state
            self._write(state)
            cntrl_set_state_changed()

    @asynccontextmanager
    async def async_update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        async with _async_state_write_lock:
            state = self._read()
            # we copy the state so that it can be red statically whilst being updated
            yield state
            self._write(state)
            cntrl_set_state_changed()

    @contextmanager
    def atomic(self):
        original_state = self._read()
        try:
            yield
        except Exception as exception:
            self._write(original_state)
            raise exception


class InMemStateUpdater(StateUpdater):

    @contextmanager
    def update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        global _state
        with _state_write_lock:
            state = deepcopy(_state)
            # we copy the state so that it can be red statically whilst being updated
            yield state
            _state = state
            cntrl_set_state_changed()

    @asynccontextmanager
    async def async_update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        global _state
        async with _async_state_write_lock:
            state = deepcopy(_state)
            # we copy the state so that it can be red statically whilst being updated
            yield state
            _state = state
            cntrl_set_state_changed()

    @contextmanager
    def atomic(self):
        global _state
        original_state = deepcopy(_state)
        try:
            yield
        except Exception as exception:
            _state = original_state
            raise exception

    def get_state(self):
        global _state
        read_state = deepcopy(_state)
        return read_state

    def reset_state(self):
        with self.update_state() as state:
            state.clear()


Redis = fakeredis.FakeRedis | redis.Redis
AsyncRedis = fakeredis.FakeAsyncRedis | asyncio_redis.Redis


class RedisStateUpdater(StateUpdater):

    def __init__(self, redis_client: Redis, async_redis_client: AsyncRedis):
        self._redis_client = redis_client
        self._async_redis_client = async_redis_client
        self._state_write_lock: RedisLock = self._redis_client.lock(
            "_state_write_lock", timeout=30
        )

    @contextmanager
    def _write_lock(self):
        if isinstance(self._redis_client, fakeredis.FakeRedis):
            with _state_write_lock:
                yield
        else:
            with self._state_write_lock:
                yield

    def _publish_state_changed(self):
        if isinstance(self._redis_client, fakeredis.FakeRedis):
            cntrl_set_state_changed()
        else:
            self._redis_client.publish("state_control_signals", "STATE_CHANGED")

    @contextmanager
    def update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        with self._write_lock():
            state_str = self._redis_client.get("state")
            if state_str:
                state = json.loads(cast(str, state_str))
            else:
                state = {}
            # we copy the state so that it can be red statically whilst being updated
            yield state
            state_str = json.dumps(state)
            self._redis_client.set("state", state_str)
            self._publish_state_changed()

    @asynccontextmanager
    async def async_update_state(self):
        # only one thread at a time can write or update the state
        # after a write, a signal is sent indicating the state has changed
        # once the signal is sent the update state lock is released
        with self._state_write_lock:
            state_str = await self._async_redis_client.get("state")
            if state_str:
                state = json.loads(cast(str, state_str))
            else:
                state = {}
            # we copy the state so that it can be red statically whilst being updated
            yield state
            state_str = json.dumps(state)
            await self._async_redis_client.set("state", state_str)
            self._publish_state_changed()

    @contextmanager
    def atomic(self):
        state_str = self._redis_client.get("state")
        try:
            yield
        except Exception as exception:
            self._redis_client.set("state", cast(str, state_str))
            raise exception

    def get_state(self):
        state_str = self._redis_client.get("state")
        if state_str:
            read_state = json.loads(cast(str, state_str))
        else:
            read_state = {}
        return read_state

    def reset_state(self):
        with self.update_state() as state:
            state.clear()

    def state_machine_is_busy(self) -> bool:
        return self._state_write_lock.locked()


@asynccontextmanager
async def async_update_state():
    # only one thread at a time can write or update the state
    # after a write, a signal is sent indicating the state has changed
    # once the signal is sent the update state lock is released
    global _state
    async with _async_state_write_lock:
        state = deepcopy(_state)
        # we copy the state so that it can be red statically whilst being updated
        yield state
        _state = state
        cntrl_set_state_changed()


class StateServer:

    def __init__(self, publisher: AbstractPublisher):
        self._publisher = publisher
        self._started_flag = Event()
        self._server_thread: None | Thread = None
        self._updater = get_state_updater()

    def _server(self):
        while True:
            self._started_flag.set()
            signal = _state_control_signals.get()
            if signal == "STATE_CHANGED":
                state = self._updater.get_state()
                self._publisher.publish(state)
            else:
                self._started_flag.clear()
                return

    def start_server(self):
        self._server_thread = Thread(target=self._server, daemon=True)
        self._server_thread.start()
        self._started_flag.wait()

    def stop_server(self):
        cntrl_set_server_stop()
        if self._server_thread:
            self._server_thread.join(1)


class RedisStateServer(StateServer):

    def __init__(self, publisher: AbstractPublisher, redis_producer: PubSub):
        self._publisher = publisher
        self._started_flag = Event()
        self._server_thread: None | PubSubWorkerThread = None
        self._updater = get_state_updater()
        self._redis_producer = redis_producer

    def _server(self):
        while True:
            self._started_flag.set()
            signal = _state_control_signals.get()
            if signal == "STATE_CHANGED":
                state = self._updater.get_state()
                self._publisher.publish(state)
            else:
                self._started_flag.clear()
                return

    def _parse_message(self, message: dict) -> Signal:
        return message["data"].decode("utf-8")

    def _handler(self, message: dict):
        signal = self._parse_message(message)
        if signal == "STATE_CHANGED":
            state = self._updater.get_state()
            self._publisher.publish(state)

    def start_server(self):
        self._redis_producer.subscribe(**{"state_control_signals": self._handler})
        self._server_thread = self._redis_producer.run_in_thread(sleep_time=0.001)

    def stop_server(self):
        if self._server_thread:
            self._server_thread.stop()


class AbstractFactory:

    @abc.abstractmethod
    def get_state_updater(self) -> StateUpdater:
        """"""

    @abc.abstractmethod
    def get_state_server(self, publisher: AbstractPublisher) -> StateServer:
        """"""


class DefaultFactory(AbstractFactory):

    def __init__(self) -> None:
        self._persist_state_in_file = os.getenv("PERSIST_STATE_IN_FILE")

    def get_state_updater(self) -> StateUpdater:
        if self._persist_state_in_file:
            return InFileStateUpdater()
        return InMemStateUpdater()

    def get_state_server(self, publisher: AbstractPublisher) -> StateServer:
        return StateServer(publisher)


class Redisfactory(AbstractFactory):

    def __init__(self) -> None:
        if os.getenv("USEFAKE_REDIS"):
            self._redis_client = fakeredis.FakeRedis()
            self._async_redis_client = fakeredis.FakeAsyncRedis()
        else:
            redis_port = config.get_redis_port()
            redis_host = config.get_redis_host()
            self._redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
            self._async_redis_client = asyncio_redis.Redis(
                host=redis_host, port=redis_port, db=0
            )

    def get_state_updater(self) -> StateUpdater:
        return RedisStateUpdater(self._redis_client, self._async_redis_client)

    def get_state_server(self, publisher: AbstractPublisher) -> RedisStateServer:
        redis_producer = self._redis_client.pubsub()
        return RedisStateServer(publisher, redis_producer)


_factory: None | AbstractFactory = None


def _get_factory():
    global _factory
    if _factory is None:
        if os.getenv("USE_REDIS_FOR_STATE_SERVER"):
            _factory = Redisfactory()
        else:
            _factory = DefaultFactory()
    return _factory


def get_state_server(publisher: AbstractPublisher) -> StateServer:
    factory = _get_factory()
    return factory.get_state_server(publisher)


def get_state_updater() -> StateUpdater:
    factory = _get_factory()
    return factory.get_state_updater()


@contextmanager
def state_server(publisher: AbstractPublisher):
    server = get_state_server(publisher)
    server.start_server()
    yield
    server.stop_server()
