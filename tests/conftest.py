import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
import websockets
import asyncio


from mv.fast_api_server import app
from mv.stack_server import state_server, AbstractPublisher

from .helpers import (
    TestWebsocket,
    RealClient,
    get_mock_ws_server,
    set_use_server_ws,
    Proxy,
    MessageObserver,
    WSListener,
    Publisher,
    EventObserver
)


class Settings:

    use_mock_ws = True
    client = TestClient(app)
    websocket = None | TestWebsocket
    publisher  = Publisher()

@pytest.fixture(name="settings")
def fxt_settings():
    return Settings()

@pytest.fixture(name="use_real_server")
def fxt_use_real_server(settings: Settings):
    settings.client = RealClient()

@pytest.fixture(name="client")
def fxt_client(settings: Settings):
    return settings.client


@pytest_asyncio.fixture(name="websocket")
async def fxt_websocket(settings: Settings):
    if settings.use_mock_ws:
        websocket = get_mock_ws_server()
        settings.websocket = websocket
        yield websocket
    else:
        async with websockets.connect("ws://localhost:8000") as websocket:
            settings.websocket = websocket
            yield websocket

@pytest.fixture(name="proxy")
def fxt_proxy(client: TestClient, websocket: TestWebsocket):
    return Proxy(client, websocket )

@pytest.fixture(name="use_ws_server")
def fxt_use_ws_server(settings: Settings):
    settings.use_mock_ws = False
    set_use_server_ws()


@pytest.fixture(name="observer")
def fxt_observer():
    return MessageObserver()


@pytest_asyncio.fixture(name="listening")
async def fxt_listening(
    observer: MessageObserver, websocket: TestWebsocket
):
    listener = WSListener(observer)
    task = asyncio.create_task(listener.listen())
    yield websocket
    await websocket.close()

@pytest.fixture(name="publisher")
def fxt_publisher(settings: Settings):
     return settings.publisher
     

@pytest.fixture(name="state_server")
def fxt_state_server(publisher: AbstractPublisher):
     with state_server(publisher):
          yield


@pytest.fixture(name="events_observer")
def fxt_observer(settings: Settings):
     assert settings.publisher
     observer = EventObserver()
     settings.publisher.subscribe(observer)
     return observer