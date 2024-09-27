import asyncio
from threading import Event
from assertpy import assert_that
import pytest
import logging
from httpx import HTTPStatusError
from requests import HTTPError
from mv.client import Proxy, AsyncProxy
from mv.state_machine import State, StateSubscriber

logger = logging.getLogger()


@pytest.fixture(autouse=True)
def fxt_auto():
    pass


@pytest.mark.asyncio
async def test_command_twice(proxy: Proxy):

    async def cor1():
        await proxy.async_command_on(0.1)

    async def cor2():
        await asyncio.sleep(0.01)
        await proxy.async_command_on(0.2)

    task1 = asyncio.create_task(cor1())
    task2 = asyncio.create_task(cor2())
    with pytest.raises(HTTPStatusError):
        await task1
        await task2


class AsyncOnSubscriber(StateSubscriber):

    def __init__(self) -> None:
        self._state_on = asyncio.Event()

    def push_event(self, event: State):
        if event == "ON":
            self._state_on.set()

    async def wait_for_on(self):
        await self._state_on.wait()


class Subscriber(StateSubscriber):

    def __init__(self) -> None:
        self._state_on = Event()
        self._state_off = Event()

    def push_event(self, event: State):
        if event == "ON":
            self._state_on.set()
        elif event == "OFF":
            self._state_off.set()

    def wait_for_on(self):
        self._state_on.wait()

    def wait_for_off(self):
        self._state_off.wait()


@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
async def test_async_ws_server_with_command(async_proxy: AsyncProxy):

    subscriber = AsyncOnSubscriber()
    async_proxy.subscribe(subscriber)
    async_proxy.command_on()
    await subscriber.wait_for_on()
    assert_that(async_proxy.state).is_equal_to("ON")


@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
def test_ws_server_with_command(proxy: Proxy):

    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")


@pytest.mark.asyncio
@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
async def test_ws_server_with_background_command(async_proxy: Proxy):
    subscriber = AsyncOnSubscriber()
    async_proxy.subscribe(subscriber)
    async_proxy.command_on_background()
    await subscriber.wait_for_on()
    assert_that(async_proxy.state).is_equal_to("ON")


@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
def test_server_with_background_command(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on_background()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")


@pytest.mark.usefixtures("use_ws_server")
@pytest.mark.usefixtures("use_real_server")
def test_server_with_multiple_background_command(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on_background(0.2)
    with pytest.raises(HTTPError):
        proxy.command_on_background()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")


def test_mock_server_with_background_command(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on_background()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")


def test_mock_server_with_background_command_off(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_off_background(2)
    subscriber.wait_for_off()
    assert_that(proxy.state).is_equal_to("OFF")


def test_mock_server_with_command(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")


def test_mock_server_with_command_off(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_off()
    subscriber.wait_for_off()
    assert_that(proxy.state).is_equal_to("OFF")


@pytest.mark.asyncio
async def test_mock_server_with_async_background_command(async_proxy: Proxy):
    subscriber = AsyncOnSubscriber()
    async_proxy.subscribe(subscriber)
    async_proxy.command_on_background()
    await subscriber.wait_for_on()
    assert_that(async_proxy.state).is_equal_to("ON")
