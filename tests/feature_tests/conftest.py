import abc
from typing import Any
import pytest
from pytest_bdd.parser import Feature, Scenario, Step
from _pytest.fixtures import TopRequest
import logging
import os
from assertpy import assert_that

from mv.client import AbstractProxy

from pytest_bdd import given, when, then

logger = logging.getLogger()


@pytest.fixture(name="start", autouse=True)
def fxt_start():
    pass


def pytest_bdd_before_step(
    request: TopRequest, feature: Feature, scenario: Scenario, step: Step, step_func
):
    logger.info(f"STEP: {step.keyword} {step.name}")
    if os.getenv("DEBUG_LOGS"):
        logger.info(
            f'{step_func.__name__}:("{step_func.__code__.co_filename}:'
            f'{step_func.__code__.co_firstlineno}"'
        )


class AbstractSubscriber:

    @abc.abstractmethod
    def push_event(self, event: Any):
        """"""

    @abc.abstractmethod
    def wait_for_on(self):
        """"""

    @abc.abstractmethod
    def wait_for_off(self):
        """"""


@pytest.fixture(name="subscriber")
def fxt_subscriber(setup: tuple[AbstractProxy, AbstractSubscriber]):
    return setup[1]


@pytest.fixture(name="proxy")
def fxt_setup(setup: tuple[AbstractProxy, AbstractSubscriber]):
    return setup[0]


# --- Givens ---

# must be implemented on each concrete test
# NB it must return a fixture as stated below
# @given("a running state machhine on a server", target_fixture="setup")


@given("a machine that is Off")
def a_machine_that_is_Off(proxy: AbstractProxy):
    proxy.command_off()


@given("a machine that is On")
def a_machine_that_is_on(proxy: AbstractProxy):
    proxy.command_on()


# --- Whens ---


@when("I command it to switch on", target_fixture="command_results")
def when_I_command_it_to_switch_on(
    proxy: AbstractProxy, subscriber: AbstractSubscriber
):
    proxy.subscribe(subscriber)
    proxy.command_on()
    return (proxy, subscriber)


@when("I command it again to switch On", target_fixture="failed_result")
def when_I_command_it_again_to_switch_on(proxy: AbstractProxy):
    try:
        proxy.command_on()
    except Exception as exception:
        return exception


@when("(in the background) I command it to switch on", target_fixture="command_results")
def when_back_I_command_it_to_switch_on(
    proxy: AbstractProxy, subscriber: AbstractSubscriber
):
    proxy.subscribe(subscriber)
    proxy.command_on_background(2)
    return (proxy, subscriber)


@when("I command it to switch off", target_fixture="command_results")
def when_I_command_it_to_switch_off(
    proxy: AbstractProxy, subscriber: AbstractSubscriber
):
    proxy.subscribe(subscriber)
    proxy.command_off()
    return (proxy, subscriber)


@when(
    "(in the background) I command it to switch off", target_fixture="command_results"
)
def when_back_I_command_it_to_switch_off(
    proxy: AbstractProxy, subscriber: AbstractSubscriber
):
    proxy.subscribe(subscriber)
    proxy.command_off_background(0.5)
    return (proxy, subscriber)


# --- Thens ---


@then("the server should first be busy")
def then_the_server_should_first_be_on(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, _ = command_results
    assert_that(proxy.state).is_equal_to("BUSY")


@then("the server should be on")
def then_the_server_should_be_on(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_on()
    assert_that(proxy.state).is_equal_to("ON")


@then("the server should be off")
def then_the_server_should_be_off(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_off()
    assert_that(proxy.state).is_equal_to("OFF")
