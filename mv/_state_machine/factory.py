import os
import fakeredis
import redis
import redis.asyncio as asyncio_redis

from .base import (
    AbstractFactory,
    AbstractPublisher,
    AbstractStateServer,
    AbstractStateUpdater,
)
from .file_backend import InFileStateUpdater
from .inmem_backend import InMemStateUpdater
from .redis_backend import RedisStateUpdater, RedisStateServer
from .state_server import StateServer
from . import config


class InMemFactory(AbstractFactory):

    def get_state_updater(self) -> InMemStateUpdater:
        return InMemStateUpdater()

    def get_state_server(self, publisher: AbstractPublisher) -> AbstractStateServer:
        state_updater = self.get_state_updater()
        return StateServer(publisher, state_updater)


class DefaultFactory(AbstractFactory):

    def get_state_updater(self) -> InMemStateUpdater | InFileStateUpdater:
        if os.getenv("PERSIST_STATE_IN_FILE"):
            return InFileStateUpdater()
        return InMemStateUpdater()

    def get_state_server(self, publisher: AbstractPublisher) -> AbstractStateServer:
        state_updater = self.get_state_updater()
        return StateServer(publisher, state_updater)


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

    def get_state_updater(self) -> AbstractStateUpdater:
        return RedisStateUpdater(self._redis_client, self._async_redis_client)

    def get_state_server(self, publisher: AbstractPublisher) -> RedisStateServer:
        redis_producer = self._redis_client.pubsub()
        state_updater = self.get_state_updater()
        return RedisStateServer(publisher, redis_producer, state_updater)


_factory: None | AbstractFactory = None


def inject_factory(factory: AbstractFactory):
    global _factory
    _factory = factory


def set_factory_for_memory_use_only():
    inject_factory(InMemFactory())


def _get_factory():
    global _factory
    if _factory is None:
        if os.getenv("USE_REDIS_FOR_STATE_SERVER"):
            _factory = Redisfactory()
        else:
            _factory = DefaultFactory()
    return _factory


def get_state_server(publisher: AbstractPublisher) -> AbstractStateServer:
    factory = _get_factory()
    return factory.get_state_server(publisher)


def get_state_updater() -> AbstractStateUpdater:
    factory = _get_factory()
    return factory.get_state_updater()
