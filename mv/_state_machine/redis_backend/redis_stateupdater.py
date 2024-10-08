from contextlib import asynccontextmanager, contextmanager
import json
from typing import Any, cast
import redis
from redis.lock import Lock as RedisLock
import redis.asyncio as asyncio_redis
import fakeredis

from .state import cntrl_set_state_changed, state_write_lock

from .base import AbstractStateUpdater

Redis = fakeredis.FakeRedis | redis.Redis
AsyncRedis = fakeredis.FakeAsyncRedis | asyncio_redis.Redis


class RedisStateUpdater(AbstractStateUpdater):

    def __init__(self, redis_client: Redis, async_redis_client: AsyncRedis):
        self._redis_client = redis_client
        self._async_redis_client = async_redis_client
        self._state_write_lock: RedisLock = self._redis_client.lock(
            "_state_write_lock", timeout=30
        )

    @contextmanager
    def _write_lock(self):
        if isinstance(self._redis_client, fakeredis.FakeRedis):
            with state_write_lock():
                yield
        else:
            with self._state_write_lock:
                yield

    def _publish_state_changed(self, state: Any):
        if isinstance(self._redis_client, fakeredis.FakeRedis):
            cntrl_set_state_changed(state)
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
            self._publish_state_changed(state)

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
            self._publish_state_changed(state)

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
