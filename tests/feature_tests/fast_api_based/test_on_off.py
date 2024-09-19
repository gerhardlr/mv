from queue import Queue
from threading import Event
import logging
from requests import HTTPError
from assertpy import assert_that
from mv.client import Proxy
from pytest_bdd import scenario, given, then

from mv.state_machine import State, StateSubscriber
from mv.client import RealClient, set_use_server_ws

from ..conftest import AbstractSubscriber

logger = logging.getLogger()


class Subscriber(AbstractSubscriber, StateSubscriber):

    def __init__(self) -> None:
        self._state_on = Event()
        self._events = Queue()
        self._state_off = Event()

    def push_event(self, event: State):
        if event == "ON":
            self._state_on.set()
        elif event == "OFF":
            self._state_off.set()
        self._events.put(event)

    def wait_for_on(self):
        self._state_on.wait()

    def wait_for_off(self):
        self._state_off.wait()


# --- Givens ---


@given("a running state machhine on a server", target_fixture="setup")
def given_a_running_state_machhine_on_a_server():
    """"""
    client = RealClient()
    proxy = Proxy(client)
    subscriber = Subscriber()
    set_use_server_ws()
    with proxy.listening():
        yield proxy, subscriber


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
def the_server_should_reject_the_command(failed_result: None | HTTPError):
    assert_that(failed_result).is_instance_of(HTTPError)


@scenario("test_on_off.feature", "Switch System On")
def test_server_on():
    """"""


@scenario("test_on_off.feature", "Switch System Off")
def test_server_off():
    """"""


@scenario("test_on_off.feature", "Background Switch System On")
def test_back_server_on():
    """"""


@scenario("test_on_off.feature", "Background Switch System Off")
def test_back_server_off():
    """"""


@scenario("test_on_off.feature", "Commanding System on before finished")
def test_commanding_on_before_finished():
    """"""
