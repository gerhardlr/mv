from assertpy import assert_that
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
import websockets
import abc
import queue
import logging
import asyncio
import requests

from mv.fast_api_server import app

class RealClient(TestClient):

    base_url = "http://127.0.0.1:8000/"

    def __init__(self):
        pass

    def get(self,path):
        return requests.get(f"{self.base_url}{path}")

    def post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", **kwargs)

class Proxy:

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def command_on(self,delay: float | None = None):
        json = {"delay": delay} if delay else delay
        result = self._client.post("switch_on",json = json)
        assert_that(result.status_code).is_equal_to(200)

    def command_off(self,delay: float | None = None):
        json = {"delay": delay} if delay else delay
        result = self._client.post("switch_off",json = json)
        assert_that(result.status_code).is_equal_to(200)

    async def async_command_on(self,delay: float | None = None):
        await asyncio.to_thread(self.command_on, delay)

    async def async_command_off(self,delay: float | None = None):
        await asyncio.to_thread(self.command_off, delay)

    @property
    def state(self):
        result = self._client.get("state")
        assert_that(result.status_code).is_equal_to(200)
        return result.json()

logger = logging.getLogger()


class MockWSServer:

    def __init__(self) -> None:
        self._messages = asyncio.Queue()
        self._closed = asyncio.Event()

    async def send(self, message):
        await self._messages.put(message)

    async def recv(self):
        message = await self._messages.get()
        if message == "STOP":
            self._closed.set()
            raise Exception("STOP")
        return message

    async def close(self):
        await self._messages.put("STOP")
        await self._closed.wait()


class AbstractObserver:

    @abc.abstractmethod
    def push_event(self, message):
        """"""


class Observer:

    def __init__(self) -> None:
        self.message = queue.Queue()

    @abc.abstractmethod
    def push_event(self, message):
        logger.info(f"{message} receieved")
        self.message.put_nowait(message)


_use_mock_ws = True
_mock_websocket: None | MockWSServer = None


def set_use_server_ws():
    global _use_mock_ws
    _use_mock_ws = False


def get_mock_ws_server():
    global _mock_websocket
    if _mock_websocket is None:
        _mock_websocket = MockWSServer()
    return _mock_websocket


@asynccontextmanager
async def get_websocket():
    if _use_mock_ws:
        yield get_mock_ws_server()
    else:
        async with websockets.connect("ws://localhost:8765") as websocket:
            yield websocket


class WSListener:

    def __init__(self, observer: AbstractObserver) -> None:
        self._observer = observer

    async def listen(self):
        async with get_websocket() as websocket:
            while True:
                try:
                    message = await websocket.recv()
                except Exception:
                    return
                await asyncio.to_thread(self._observer.push_event, message)


class Settings:

    use_mock_ws = True
    client = TestClient(app)

@pytest.fixture(name="use_real_server")
def fxt_use_real_server(settings: Settings):
    settings.client = RealClient()

@pytest.fixture(name="client")
def fxt_client(settings: Settings):
    return settings.client

@pytest.fixture(name="proxy")
def fxt_proxy(client):
    return Proxy(client)


@pytest.fixture(name="settings")
def fxt_settings():
    return Settings()


@pytest_asyncio.fixture(name="websocket")
async def fxt_websocket(settings: Settings):
    if settings.use_mock_ws:
        yield get_mock_ws_server()
    else:
        async with websockets.connect("ws://localhost:8000") as websocket:
            yield websocket


@pytest.fixture(name="use_ws_server")
def fxt_use_ws_server(settings: Settings):
    settings.use_mock_ws = False
    set_use_server_ws()


@pytest.fixture(name="observer")
def fxt_observer():
    return Observer()


@pytest_asyncio.fixture(name="listening")
async def fxt_listening(
    observer: Observer, websocket: websockets.WebSocketClientProtocol | MockWSServer
):
    listener = WSListener(observer)
    task = asyncio.create_task(listener.listen())
    yield websocket
    await websocket.close()