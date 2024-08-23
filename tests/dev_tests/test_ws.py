from assertpy import assert_that
import pytest
import websockets
from mv.client import AsyncMockWSServer, MockWSServer


@pytest.mark.asyncio
async def test_async_ws_local(async_websocket: AsyncMockWSServer):
    tx_message = "ON"
    websocket = async_websocket
    await websocket.send(tx_message)
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)


def test_ws_local(websocket: MockWSServer):
    tx_message = "ON"
    websocket.send(tx_message)
    rx_message = websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)

@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
async def test_async_ws_server(async_websocket: websockets.WebSocketClientProtocol):
    tx_message = "ON"
    websocket = async_websocket
    await websocket.send(tx_message)
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)


@pytest.mark.usefixtures("use_ws_server")
def test_ws_server(websocket: websockets.WebSocketClientProtocol):
    tx_message = "ON"
    websocket.send(tx_message)
    rx_message = websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)