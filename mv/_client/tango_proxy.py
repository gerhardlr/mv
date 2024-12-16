import os
from typing import Any
from tango import DeviceProxy, EventType
from .base import AbstractProxy, Attribute


def get_tango_proxy(dev_name: str):
    host = os.getenv("SERVER_IP", "127.0.0.1")
    port = os.getenv("SERVER_PORT", "30002")
    db = os.getenv("TANGO_DB")
    if db is None:
        proxy = DeviceProxy(f"tango://{host}:{port}/{dev_name}#dbase=no")
        return proxy
    else:
        raise NotImplementedError("Tango with DB not yet implemented")


class TangoProxy(AbstractProxy):
    dev_name = "mv/statemachine/1"

    def __init__(self) -> None:
        self._proxy = get_tango_proxy(self.dev_name)
        self._proxy.ping()

    def ping(self):
        return self._proxy.ping()

    def subscribe(self, subscriber: Any, attribute: Attribute = "state") -> int:
        sub_id = self._proxy.subscribe_event(
            "agg_state", EventType.CHANGE_EVENT, subscriber
        )
        return sub_id

    def unsubscribe(self, sub_scriber_id: int):
        self._proxy.unsubscribe(sub_scriber_id)

    def command_on(self, delay: float | None = None):
        delay_str = str(delay) if delay else ""
        self._proxy.switch_on(delay_str)

    def command_off(self, delay: float | None = None):
        delay_str = str(delay) if delay else ""
        self._proxy.switch_off(delay_str)

    def command_on_background(self, delay: float = 0):
        delay_str = str(delay) if delay else ""
        self._proxy.background_switch_on(delay_str)

    def command_off_background(self, delay: float = 0):
        delay_str = str(delay) if delay else ""
        self._proxy.background_switch_off(delay_str)

    @property
    def state(self):
        return self._proxy.agg_state
