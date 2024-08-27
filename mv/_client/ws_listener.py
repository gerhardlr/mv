import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from queue import Queue
from threading import Event
from typing import cast
import websockets
from websockets.sync.client import connect

from .base import AbstractObserver, AsynchAbstractObserver
from .config import get_ws_address

from mv.state_machine import AbstractPublisher, StateServer


class AsyncMockWSServer(AbstractPublisher):

    def __init__(self) -> None:
        self.messages = asyncio.Queue()
        self._closed = asyncio.Event()
        self._server  = StateServer(self)
        self._server.start_server()

    async def send(self, message):
        await self.messages.put(message)

    async def put_message(self, message):
        await self.messages.put(message)

    async def recv(self):
        message = await self.messages.get()
        if message == "STOP":
            self._closed.set()
            raise Exception("STOP")
        return message

    async def close(self):
        await self.messages.put("STOP")
        await self._closed.wait()
        self._server.stop_server()

    def publish(self, state: dict):
        value = state["state"]
        asyncio.run(self.messages.put(value))


class MockWSServer(AbstractPublisher):

    def __init__(self) -> None:
        self.messages = Queue()
        self._closed = Event()
        self._server  = StateServer(self)
        self._server.start_server()

    def wait_closed(self):
        self._closed.wait()

    def send(self, message):
        self.messages.put(message)
    
    def recv(self):
        message = self.messages.get()
        if message == "STOP":
            self._closed.set()
            raise Exception("STOP")
        return message

    def close(self):
        self.messages.put("STOP")
        self.wait_closed()
        self._server.stop_server()

    def publish(self, state: dict):
        value = state["state"]
        self.messages.put(value)


_use_mock_ws = True
_async_mock_websocket: None | AsyncMockWSServer = None
_mock_websocket: None | MockWSServer = None


def set_use_server_ws():
    global _use_mock_ws
    _use_mock_ws = False


def get_async_mock_ws_server():
    global _async_mock_websocket
    if _async_mock_websocket is None:
        _async_mock_websocket = AsyncMockWSServer()
    return _async_mock_websocket


def get_mock_ws_server():
    global _mock_websocket
    if _mock_websocket is None:
        _mock_websocket = MockWSServer()
    return _mock_websocket


@asynccontextmanager
async def get_async_websocket():
    if _use_mock_ws:
        yield get_async_mock_ws_server()
    else:
        async with websockets.connect(get_ws_address()) as websocket:
            yield websocket

@contextmanager
def get_websocket():
    if _use_mock_ws:
        yield get_mock_ws_server()
    else:
        with connect(get_ws_address()) as websocket:
            yield websocket
            
TestWebsocket =  websockets.WebSocketClientProtocol | AsyncMockWSServer

class AsyncWSListener:

    def __init__(self, observer: AsynchAbstractObserver) -> None:
        self._observer = observer
        self._websocket = None
        self._ws_ready =asyncio.Queue[bool | Exception]()

    @property
    def websocket(self):
        return self._websocket

    async def stop(self):
        if self._websocket:
            await self._websocket.close()

    async def _wait_for_ws_ready(self):
        if(result := await self._ws_ready.get()) is not True:
            raise cast(Exception,result)



    async def _listen(self):
        try:
            async with get_async_websocket() as websocket:
                self._websocket = websocket
                await self._ws_ready.put(True)
                while True:
                    try:
                        message = await websocket.recv()
                    except Exception as exception:
                        await self._ws_ready.put(exception)
                        return
                    await self._observer.push_event(message)
        except Exception as exception:
            await self._ws_ready.put(exception)


    
    @asynccontextmanager
    async def listening(self):
        task = asyncio.create_task(self._listen())
        await self._wait_for_ws_ready()
        yield self.websocket
        await self.stop()
        await task


class WSListener:

    def __init__(self, observer: AbstractObserver) -> None:
        self._observer = observer
        self._websocket = None
        self._ws_ready =  Event()
        self._stop_signal = Event()

    @property
    def websocket(self):
        return self._websocket

    def stop(self):
        if self._websocket:
            self._websocket.close()

    def _listen(self):
        with get_websocket() as websocket:
            self._websocket = websocket
            self._ws_ready.set()
            while True:
                try:
                    message = websocket.recv()
                except Exception:
                    return
                self._observer.push_event(message)

    def wait_for_ws_ready(self,):
        if not self._ws_ready.wait(timeout=2):
            raise TimeoutError("Timed out waiting for ws to be ready")

    @staticmethod
    def _cancel_task(task: Future):
        if task.running():
            task.cancel()
        elif task.done():
            task.result() 


    @contextmanager
    def listening(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            listening_task = executor.submit(self._listen)  
            try:
                self.wait_for_ws_ready()
            except TimeoutError:
                self._cancel_task(listening_task)            
            yield self.websocket
            self.stop()
            listening_task.result()
        
