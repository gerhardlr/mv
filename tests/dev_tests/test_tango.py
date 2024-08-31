from tango import DeviceProxy
from tango import EventData
from tango import EventType
from assertpy import assert_that
from threading import Event


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


def test_commands():
    host = "127.0.0.1"
    port = 10000
    dev_name = "mv/statemachine/1"
    proxy = DeviceProxy(f"tango://{host}:{port}/{dev_name}#dbase=no")
    subscriber = Subscriber()
    sub_id = proxy.subscribe_event("agg_state", EventType.CHANGE_EVENT, subscriber)
    proxy.switch_on("")
    subscriber.wait_for_on()
    assert_that(proxy.agg_state).is_equal_to("ON")
    proxy.switch_off("")
    subscriber.wait_for_off()
    assert_that(proxy.agg_state).is_equal_to("OFF")
