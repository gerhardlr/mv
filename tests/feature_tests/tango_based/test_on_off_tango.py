from threading import Event
from assertpy import assert_that
import logging

from pytest_bdd import scenario, given, then
from tango import EventData, DeviceProxy
from PyTango import DevFailed

from mv.client import TangoProxy

from ..conftest import AbstractProxy, GlobalSettings

logger = logging.getLogger()


class WaitTimeout(Exception):

    pass


class Subscriber(AbstractProxy):

    def __init__(self) -> None:
        self._on = Event()
        self._off = Event()
        self._busy = Event()
        self._on.clear()
        self._off.clear()
        self.current: None | str = None
        self._event_messages: list[str] = []
        self._first_event = True
        self._device = None | DeviceProxy

    def _log_event_message(self, message: str):
        self._event_messages.append(message)

    def print_event_messages(self):
        logging.info("Events:\n")
        logging.info("\n".join(self._event_messages))

    def push_event(self, event: EventData):
        if event is None:
            return
        if event.err:
            self._log_event_message(
                f"Errors received in event from tango server: {event.errors}"
            )
            return
        if event.attr_value:
            value = event.attr_value.value
            if self.current is None:
                self.current = value
                self._device = event.device
                self._log_event_message(
                    f"got FIRST value from pub sub event: value = {value}"
                )
                return
            self._log_event_message(f"got value from pub sub event: value = {value}")
            if value == "ON":
                self._on.set()
            elif value == "OFF":
                self._off.set()
            elif value == "BUSY":
                self._busy.set()

    def wait_for_on(self, timeout: bool | None = None):
        if self._on.wait(timeout):
            return
        self.print_event_messages()
        current_state = self._device.agg_state
        raise WaitTimeout(
            f"timed out waiting for on after {timeout} seconds;"
            f" current state = {current_state}"
        )

    def wait_for_busy(self, timeout: bool | None = None):
        if self._busy.wait(timeout):
            return
        self.print_event_messages()
        current_state = self._device.agg_state
        raise WaitTimeout(
            f"timed out waiting for busy after {timeout} seconds;"
            f" current state = {current_state}"
        )

    def wait_for_off(self, timeout: bool | None = None):
        if self._off.wait(timeout):
            return
        self.print_event_messages()
        current_state = self._device.agg_state
        raise WaitTimeout(
            f"timed out waiting for off after {timeout} seconds;"
            f" current state = {current_state}"
        )


# --- Givens ---


@given("a running state machine on a server", target_fixture="setup")
def given_a_running_state_machine_on_a_server(global_settings: GlobalSettings):
    global_settings.wait_for_timeout = 9.5
    # global_settings.command_delay = 9
    proxy = TangoProxy()
    logger.info(f"Using device {proxy.dev_name} on address: {proxy.tango_address}")
    subscriber = Subscriber()
    return proxy, subscriber


# from ..conftest

# @given("a machine that is Off")


# @given("a machine that is On")

# --- Whens ---

# from ..conftest

# @when("I command it again to switch On", target_fixture="failed_result")

# @when("I command it to switch off", target_fixture="command_results")

# @when(
#    "(in the background) I command it to switch off", target_fixture="command_results"
# )

# --- Thens ---

# from ..conftest

# @then("the server should first be busy")

# @then("the server should be on")

# @then("the server should be off")


@then("the server should reject the command")
def the_server_should_reject_the_command(failed_result: None | DevFailed):
    assert_that(failed_result).is_instance_of(DevFailed)


@scenario("test_on_off_tango.feature", "Switch System On")
def test_server_on():
    """"""


@scenario("test_on_off_tango.feature", "Switch System Off")
def test_server_off():
    """"""


@scenario("test_on_off_tango.feature", "Background Switch System On")
def test_back_server_on():
    """"""


@scenario("test_on_off_tango.feature", "Background Switch System Off")
def test_back_server_off():
    """"""


@scenario("test_on_off_tango.feature", "Commanding System on before finished")
def test_commanding_on_before_finished():
    """"""
