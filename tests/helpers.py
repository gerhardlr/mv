from contextlib import asynccontextmanager
from threading import Event
import requests
import abc
import queue
import logging
from assertpy import assert_that
import websockets
from fastapi.testclient import TestClient
import asyncio
from mv.stack_server import AbstractPublisher

class RealClient(TestClient):

    base_url = "http://127.0.0.1:8000/"

    def __init__(self):
        pass

    def get(self,path):
        return requests.get(f"{self.base_url}{path}")

    def post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", **kwargs)


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

TestWebsocket =  websockets.WebSocketClientProtocol | MockWSServer

class Proxy:

    def __init__(self, client: TestClient, websocket: TestWebsocket) -> None:
        self._client = client
        self._websocket = websocket

    def command_on(self,delay: float | None = None):
        json = {"delay": delay} if delay else delay
        result = self._client.post("switch_on",json = json)
        assert_that(result.status_code).is_equal_to(200)

    def command_off(self,delay: float | None = None):
        json = {"delay": delay} if delay else delay
        result = self._client.post("switch_off",json = json)
        assert_that(result.status_code).is_equal_to(200)

    def command_on_background(self,delay: float = 0):
        json = {"delay": delay}
        result = self._client.post("background_switch_on",json = json)
        assert_that(result.status_code).is_equal_to(200)

    def command_off_background(self,delay: float = 0):
        json = {"delay": delay}
        result = self._client.post("background_switch_off",json = json)
        assert_that(result.status_code).is_equal_to(200)

    async def async_command_on(self,delay: float | None = None):
        await asyncio.to_thread(self.command_on, delay)

    async def async_command_off(self,delay: float | None = None):
        await asyncio.to_thread(self.command_off, delay)

    async def async_wait_for_state_to_change(self):
        return await self._websocket.recv()
    
    def wait_for_state_to_change(self):
        return asyncio.run(self._websocket.recv())


    @property
    def state(self):
        result = self._client.get("state")
        assert_that(result.status_code).is_equal_to(200)
        return result.json()


class AbstractObserver:

    @abc.abstractmethod
    def push_event(self, message):
        """"""
        
class EventObserver:

     def __init__(self) -> None:
          self.state: None | dict = None
          self._new_event = Event()

     def set_event(self,event: dict):
          self.state = event
          self._new_event.set()
     
     def wait_for_next_event(self):
          assert self._new_event.wait(1)
          self._new_event.clear()


class Publisher(AbstractPublisher):

     def __init__(self) -> None:
          self._observer: None | EventObserver  = None

     def subscribe(self, observer: EventObserver):
          self._observer = observer

     def publish(self, state):
          if self._observer:
             self._observer.set_event(state)


class MessageObserver:

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