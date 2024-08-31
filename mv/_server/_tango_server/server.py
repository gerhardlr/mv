import json
from threading import Thread
from typing import cast
from tango.server import Device, command, attribute
from mv.state_machine import get_state_machine, get_state_server


class App(Device):

    def __init__(self, cl, name):
        super().__init__(cl, name)
        self._state_machine = get_state_machine()
        self._executor: None | Thread = None
        self._server = get_state_server(self)
        self._server.start_server()
        self.set_change_event("agg_state", True, False)

    def publish(self, state: dict):
        value = state["state"]
        self.push_change_event("agg_state", value)

    @attribute(dtype=str)
    def agg_state(self) -> str:
        return cast(str, self._state_machine.state)

    def _background_on(self, delay: float):
        self._executor = Thread(
            target=self._state_machine.switch_on(), args=[delay], daemon=True
        )
        self._executor.start()

    def _background_off(self, delay: float):
        self._executor = Thread(
            target=self._state_machine.switch_off(), args=[delay], daemon=True
        )
        self._executor.start()

    @command(dtype_in=str)
    def switch_on(self, args):
        if args == "":
            delay = None
        else:
            delay = float(
                json.loads(args),
            )
        if delay:
            if delay > 2.9:
                self._background_on(delay)
                return
        self._state_machine.switch_on()

    @command(dtype_in=str)
    def switch_off(self, args):
        if args == "":
            delay = None
        else:
            delay = float(
                json.loads(args),
            )
        if delay:
            if delay > 2.9:
                self._background_off(delay)
                return
        self._state_machine.switch_off()

    @command(dtype_in=str)
    def background_switch_off(self, args):
        if args == "":
            delay = None
        if delay:
            self._background_off(delay)
        else:
            self._state_machine.switch_off()

    @command(dtype_in=str)
    def background_switch_on(self, args):
        if args == "":
            delay = None
        if delay:
            self._background_on(delay)
        else:
            self._state_machine.switch_on()
