import asyncio
from assertpy import assert_that
import pytest
from fastapi.testclient import TestClient
import websockets

from .conftest import Proxy, MockWSServer, Observer


def test_get(proxy: Proxy):
    assert_that(proxy.state).is_none()

@pytest.mark.usefixtures("use_real_server")
def test_get_real(proxy:Proxy):
    assert_that(proxy.state).is_none()
    

def test_post_on(proxy: Proxy):
    proxy.command_on(delay=1)
    assert_that(proxy.state).is_equal_to("ON")

@pytest.mark.usefixtures("use_real_server")
def test_post_real_on(proxy: Proxy):
    proxy.command_on(delay=1)
    assert_that(proxy.state).is_equal_to("ON")


def execute_post_off(client: TestClient):
    result = client.post("switch_off",json = {"delay": 10})
    assert_that(result.status_code).is_equal_to(200)

@pytest.mark.usefixtures("use_real_server")
def test_post_real_off(client):
    execute_post_off(client)

def test_post_off(client):
    execute_post_off(client)


@pytest.mark.asyncio
#@pytest.mark.usefixtures("use_real_server")
async def test_command_twice(proxy: Proxy):
    task1 = asyncio.create_task(proxy.async_command_on(2))
    task2 = asyncio.create_task(proxy.async_command_on(0.5))
    with pytest.raises(AssertionError):
        await task1
        await task2


@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
async def test_ws_server(websocket: websockets.WebSocketClientProtocol):
    tx_message = "ON"
    await websocket.send(tx_message)
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)

@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
async def test_ws_server_with_command(
    websocket: websockets.WebSocketClientProtocol,
    proxy: Proxy
):
    #tx_message = ""
    #await websocket.send(tx_message)
    #rx_message = await websocket.recv()
    #assert_that(rx_message).is_equal_to(tx_message)
    await proxy.async_command_on()
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to("ON")



@pytest.mark.asyncio
async def test_ws_local(websocket: MockWSServer):
    tx_message = "ON"
    await websocket.send(tx_message)
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)



@pytest.mark.asyncio
async def test_listening(listening: MockWSServer, observer: Observer):
    websocket = listening
    tx_message = "ON"
    await websocket.send(tx_message)
    await asyncio.sleep(0.0001)
    rx_message = observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)