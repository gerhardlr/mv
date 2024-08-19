import abc
import asyncio
from contextlib import asynccontextmanager
from queue import Empty
import queue
from assertpy import assert_that
import pytest
import pytest_asyncio
import websockets
import logging

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
                except Exception as exception:
                    return
                await asyncio.to_thread(self._observer.push_event, message)


class Settings:

    use_mock_ws = True


@pytest.fixture(name="settings")
def fxt_settings():
    return Settings()


@pytest_asyncio.fixture(name="websocket")
async def fxt_websocket(settings: Settings):
    if settings.use_mock_ws:
        yield get_mock_ws_server()
    else:
        async with websockets.connect("ws://localhost:8765") as websocket:
            yield websocket


async def execute(websocket: websockets.WebSocketClientProtocol | MockWSServer):
    tx_message = "ON"
    await websocket.send(tx_message)
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)


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


@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
async def test_ws_server(websocket: websockets.WebSocketClientProtocol):
    await execute(websocket)


@pytest.mark.asyncio
async def test_ws_local(websocket: MockWSServer):
    await execute(websocket)


@pytest.mark.asyncio
async def test_listening(listening: MockWSServer, observer: Observer):
    websocket = listening
    tx_message = "ON"
    await websocket.send(tx_message)
    await asyncio.sleep(0.0001)
    rx_message = observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)
