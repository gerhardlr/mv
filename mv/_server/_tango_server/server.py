from threading import Thread
from typing import cast
from tango.server import Device, command, attribute
from mv.state_machine import get_state_machine, get_state_server


class _Args:

    def __init__(self, args: str) -> None:
        self._args = args

    @property
    def delay(self):
        if self._args == "":
            return None
        else:
            return float(self._args)


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

    def _background_on(self, delay: float | None):
        self._executor = Thread(
            target=self._state_machine.switch_on, args=[delay], daemon=True
        )
        self._executor.start()

    def _background_off(self, delay: float | None):
        self._executor = Thread(
            target=self._state_machine.switch_off, args=[delay], daemon=True
        )
        self._executor.start()

    @command(dtype_in=str)
    def switch_on(self, input_args: str):
        args = _Args(input_args)
        if args.delay:
            if args.delay > 2.9:
                self._background_on(args.delay)
                return
        self._state_machine.switch_on()

    @command(dtype_in=str)
    def switch_off(self, input_args: str):
        args = _Args(input_args)
        if args.delay:
            if args.delay > 2.9:
                self._background_off(args.delay)
                return
        self._state_machine.switch_off()

    @command(dtype_in=str)
    def background_switch_off(self, input_args: str):
        args = _Args(input_args)
        if args.delay:
            self._background_off(args.delay)
        else:
            self._state_machine.switch_off()

    @command(dtype_in=str)
    def background_switch_on(self, input_args: str):
        args = _Args(input_args)
        if args.delay:
            self._background_on(args.delay)
        else:
            self._state_machine.switch_on()
