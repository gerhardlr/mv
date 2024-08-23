from threading import Event
from assertpy import assert_that
import logging

from requests import HTTPError
from mv.client import Proxy
from pytest_bdd import scenario,given,when,then

from mv.state_machine import State, StateSubscriber
from mv.client import RealClient, set_use_server_ws

logger = logging.getLogger()

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



@given("a running state machhine on a server",target_fixture="proxy")
def given_a_running_state_machhine_on_a_server():
    client = RealClient()
    proxy = Proxy(client)
    set_use_server_ws()
    with proxy.listening():
        yield proxy

@given("a machine that is Off")
def a_machine_that_is_Off(proxy: Proxy):
    proxy.command_off()

@given("a machine that is On")
def a_machine_that_is_Off(proxy: Proxy):
    proxy.command_on()


@when("I command it to switch on",target_fixture="command_results")
def when_I_command_it_to_switch_on(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on()
    return (proxy,subscriber)

@when("I command it again to switch On", target_fixture="failed_result")
def when_I_command_it_again_to_switch_on(proxy: Proxy):
    try:
        proxy.command_on()
    except HTTPError as exception:
        return exception


@when("(in the background) I command it to switch on",target_fixture="command_results")
def when_back_I_command_it_to_switch_on(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_on_background(0.5)
    return (proxy,subscriber)

@when("I command it to switch off",target_fixture="command_results")
def when_I_command_it_to_switch_on(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_off()
    return (proxy,subscriber)

@when("(in the background) I command it to switch off",target_fixture="command_results")
def when_back_I_command_it_to_switch_on(proxy: Proxy):
    subscriber = Subscriber()
    proxy.subscribe(subscriber)
    proxy.command_off_background(0.5)
    return (proxy,subscriber)

@then("the server should first be off")
def then_the_server_should_first_be_off(command_results: tuple[Proxy,Subscriber]):
    proxy, _ = command_results
    assert_that(proxy.state).is_equal_to("OFF")

@then("the server should first be on")
def then_the_server_should_first_be_off(command_results: tuple[Proxy,Subscriber]):
    proxy, _ = command_results
    assert_that(proxy.state).is_equal_to("ON")

@then("the server should be on")
def then_the_server_should_be_on(command_results: tuple[Proxy,Subscriber]):
    proxy, subscriber = command_results
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")

@then("the server should be off")
def then_the_server_should_be_on(command_results: tuple[Proxy,Subscriber]):
    proxy, subscriber = command_results
    subscriber.wait_for_off()
    assert_that(proxy.state).is_equal_to("OFF")

@then("the server should reject the command")
def the_server_should_reject_the_command(failed_result: None | HTTPError):
    assert_that(failed_result).is_instance_of(HTTPError)

@scenario("test_on_off.feature","Switch System On")
def test_server_on():
    """"""

@scenario("test_on_off.feature","Switch System Off")
def test_server_off():
    """"""

@scenario("test_on_off.feature","Background Switch System On")
def test_back_server_on():
    """"""

@scenario("test_on_off.feature","Background Switch System Off")
def test_back_server_off():
    """"""

@scenario("test_on_off.feature","Commanding System on before finished")
def test_commanding_on_before_finished():
    """""" 
