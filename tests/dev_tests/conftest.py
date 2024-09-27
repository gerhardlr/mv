import os
from typing import Any, Generator, cast
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from websockets import connect as async_connect
from websockets.sync.client import connect, ClientConnection
import logging
from mv.client import MockWSServer
from mv.server import app
from mv.state_machine import (
    state_server,
    AbstractPublisher,
    get_state_updater,
    AbstractStateUpdater,
)
from mv.client import (
    get_async_mock_ws_server,
    get_mock_ws_server,
    Proxy,
    AsyncProxy,
    set_use_server_ws,
    AsyncWSListener,
    WSListener,
    RealClient,
    TestWebsocket,
)


from .helpers import MessageObserver, Publisher, EventObserver, AsynchMessageObserver

logger = logging.getLogger()


class Settings:

    use_mock_ws = True
    client = TestClient(app)
    websocket: None | TestWebsocket | MockWSServer | ClientConnection = None
    publisher = Publisher()
    use_synch_listening = False


@pytest.fixture(name="start", autouse=True)
def fxt_start():
    pass


@pytest.fixture(name="use_synch_listening")
def fxt_use_synch_listening(settings: Settings):
    settings.use_synch_listening = True


@pytest.fixture(name="settings")
def fxt_settings():
    return Settings()


@pytest.fixture(name="use_real_server")
def fxt_use_real_server(settings: Settings):
    settings.client = RealClient()


@pytest.fixture(name="client")
def fxt_client(settings: Settings):
    return settings.client


@pytest_asyncio.fixture(name="async_websocket")
async def fxt_async_websocket(settings: Settings):
    if settings.use_mock_ws:
        websocket = get_async_mock_ws_server()
        settings.websocket = websocket
        yield websocket
    else:
        async with async_connect("ws://localhost:30002") as websocket:
            settings.websocket = websocket
            yield websocket


@pytest_asyncio.fixture(name="websocket")
async def fxt_websocket(settings: Settings):
    if settings.use_mock_ws:
        websocket = get_mock_ws_server()
        settings.websocket = websocket
        yield websocket
    else:
        with connect("ws://localhost:30002") as websocket:
            settings.websocket = cast(ClientConnection, websocket)
            yield websocket


@pytest_asyncio.fixture(name="async_proxy")
async def fxt_async_proxy(client: TestClient):
    proxy = AsyncProxy(client)
    async with proxy.listening():
        yield proxy


@pytest.fixture(name="proxy")
def fxt_proxy(client: TestClient):
    proxy = Proxy(client)
    with proxy.listening():
        yield proxy


@pytest.fixture(name="use_ws_server")
def fxt_use_ws_server(settings: Settings):
    settings.use_mock_ws = False
    set_use_server_ws()


@pytest.fixture(name="observer")
def fxt_observer():
    return MessageObserver()


@pytest.fixture(name="async_observer")
def fxt_async_observer():
    return AsynchMessageObserver()


@pytest_asyncio.fixture(name="async_listening")
async def fxt_async_listening(async_observer: AsynchMessageObserver):
    listener = AsyncWSListener(async_observer)
    async with listener.listening() as websocket:
        yield websocket


@pytest_asyncio.fixture(name="listening")
def fxt_listening(observer: MessageObserver):
    listener = WSListener(observer)
    with listener.listening() as websocket:
        yield websocket


@pytest.fixture(name="publisher")
def fxt_publisher(settings: Settings):
    return settings.publisher


@pytest.fixture(name="state_updater")
def fxt_state_updater(
    publisher: AbstractPublisher,
) -> Generator[AbstractStateUpdater, Any, None]:
    with state_server(publisher):
        state_updater = get_state_updater()
        yield state_updater


@pytest.fixture(name="events_observer")
def fxt_events_observer(settings: Settings):
    assert settings.publisher
    observer = EventObserver()
    settings.publisher.subscribe(observer)
    return observer


@pytest.fixture(name="persist_state_in_file")
def fxt_persist_state_in_file():
    os.environ["PERSIST_STATE_IN_FILE"] = "True"


@pytest.fixture(name="reset_state")
def test_load_state_from_file(state_updater: AbstractStateUpdater):
    state_updater.reset_state()
