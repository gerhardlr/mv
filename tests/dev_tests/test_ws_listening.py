import asyncio
from assertpy import assert_that
import pytest
from mv.client import AsyncMockWSServer, MockWSServer
from .helpers import MessageObserver, AsynchMessageObserver


@pytest.mark.asyncio
async def test_async_listening(async_listening: AsyncMockWSServer, async_observer: AsynchMessageObserver):
    websocket = async_listening
    tx_message = "ON"
    await websocket.send(tx_message)
    await asyncio.sleep(0.0001)
    rx_message = await async_observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)

@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
async def test_async_real_listening(async_listening: AsyncMockWSServer, async_observer: AsynchMessageObserver):
    websocket = async_listening
    tx_message = "ON"
    await websocket.send(tx_message)
    rx_message = await async_observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)



def test_listening(listening: MockWSServer, observer: MessageObserver):
    websocket = listening
    tx_message = "ON"
    websocket.send(tx_message)
    rx_message = observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)

@pytest.mark.usefixtures("use_ws_server")
def test_real_listening(listening: MockWSServer, observer: MessageObserver):
    websocket = listening
    tx_message = "ON"
    websocket.send(tx_message)
    rx_message = observer.message.get()
    assert_that(rx_message).is_equal_to(tx_message)