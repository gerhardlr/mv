import asyncio
from assertpy import assert_that
import pytest
from fastapi.testclient import TestClient
import websockets

from .helpers import Proxy, MockWSServer, MessageObserver


def test_get(proxy: Proxy):
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
    proxy: Proxy
):
    await proxy.async_command_on()
    new_state = await proxy.async_wait_for_state_to_change()
    assert_that(new_state).is_equal_to("ON")

@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
async def test_ws_server_with_background_command(
    proxy: Proxy
):
    proxy.command_on_background()
    new_state = await proxy.async_wait_for_state_to_change()
    assert_that(new_state).is_equal_to("ON")


def test_server_with_background_command(
    proxy: Proxy
):
    proxy.command_on_background()
    new_state = proxy.wait_for_state_to_change()
    assert_that(new_state).is_equal_to("ON")

@pytest.mark.asyncio
async def test_ws_local(websocket: MockWSServer):
    tx_message = "ON"
    await websocket.send(tx_message)
    rx_message = await websocket.recv()
    assert_that(rx_message).is_equal_to(tx_message)



@pytest.mark.asyncio
async def test_listening(listening: MockWSServer, observer: MessageObserver):
    websocket = listening
    tx_message = "ON"
    await websocket.send(tx_message)
    await asyncio.sleep(0.0001)
    rx_message = observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)