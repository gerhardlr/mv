from threading import Event
from assertpy import assert_that
import logging

from pytest_bdd import scenario, given, then
from tango import EventData
from PyTango import DevFailed

from mv.client import TangoProxy

from ..conftest import AbstractProxy

logger = logging.getLogger()


class Subscriber(AbstractProxy):

    def __init__(self) -> None:
        self._on = Event()
        self._off = Event()
        self._busy = Event()
        self._on.clear()
        self._off.clear()
        self.current: None | str = None

    def push_event(self, event: EventData):
        logging.info(event)
        if event is None:
            return
        if event.err:
            logging.info(f"Errors received in event from tango server: {event.errors}")
            return
        if event.attr_value:
            value = event.attr_value.value
            if self.current is None:
                self.current = value
                return
            if value == "ON":
                self._on.set()
            elif value == "OFF":
                self._off.set()
            elif value == "BUSY":
                self._busy.set()
       
    def wait_for_on(self):
        self._on.wait()

    def wait_for_busy(self):
        self._busy.wait()

    def wait_for_off(self):
        self._off.wait()


# --- Givens ---


@given("a running state machine on a server", target_fixture="setup")
def given_a_running_state_machhine_on_a_server():
    proxy = TangoProxy()
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
