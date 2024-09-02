from tango import EventData
from assertpy import assert_that
from threading import Event

from mv.client import TangoProxy


class Subscriber:

    def __init__(self) -> None:
        self._on = Event()
        self._off = Event()
        self._on.clear()
        self._off.clear()
        self.current: None | str = None

    def push_event(self, event: EventData):
        if event is None:
            return
        value = event.attr_value.value
        if self.current is None:
            self.current = value
            return
        if value == "ON":
            self._on.set()
        elif value == "OFF":
            self._off.set()

    def wait_for_on(self):
        self._on.wait()

    def wait_for_off(self):
        self._off.wait()


def test_proxy():
    proxy = TangoProxy()
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")
    proxy.command_off()
    subscriber.wait_for_off()
    assert_that(proxy.state).is_equal_to("OFF")
    proxy.command_on_background()
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")
    proxy.command_off_background()
    subscriber.wait_for_off()
    assert_that(proxy.state).is_equal_to("OFF")
