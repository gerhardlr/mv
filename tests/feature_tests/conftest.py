import abc
from contextlib import ExitStack, contextmanager
from typing import Any
import pytest
from pytest_bdd.parser import Feature, Scenario, Step
from _pytest.fixtures import TopRequest
import logging
import os
from assertpy import assert_that

from mv.client import AbstractProxy

from pytest_bdd import given, when, then

from .contextmanagement import StackableContext

logger = logging.getLogger()


@pytest.fixture(name="start", autouse=True)
def fxt_start():
    pass


# utils


@pytest.fixture(scope="session")
def session_stack():
    with ExitStack() as session_stack:
        yield session_stack


@pytest.fixture
def stack():
    with ExitStack() as stack:
        yield stack


@pytest.fixture
def context(stack: ExitStack, session_stack: ExitStack):
    context = StackableContext(session_stack, stack)
    return context


class TelescopeController:

    def __init__(self, stack: StackableContext):
        self._stack = stack
        self._disable_release = False
        self._disable_clear_config = False

    def clear_release_after(self):
        self._disable_release = True

    def disable_clear_config_after(self):
        self._disable_clear_config = True

    @contextmanager
    def _release_resources_after(
        self, proxy: AbstractProxy, subscriber: "AbstractSubscriber"
    ):
        yield
        if self._disable_release:
            return
        if subscriber:
            subscriber.wait_for_idle()
        proxy.command_release_resources()

    @contextmanager
    def _clear_config_after(
        self, proxy: AbstractProxy, subscriber: "AbstractSubscriber"
    ):
        yield
        if self._disable_clear_config:
            return
        if subscriber:
            subscriber.wait_for_ready()
        proxy.command_clear_config()

    @contextmanager
    def _switch_off_after(self, proxy: AbstractProxy):
        yield
        proxy.command_off()

    def release_resources_after(
        self, proxy: AbstractProxy, subscriber: "AbstractSubscriber" = None
    ):
        self._stack.push_context_onto_test(
            self._release_resources_after(proxy, subscriber)
        )

    def clear_config_after(
        self, proxy: AbstractProxy, subscriber: "AbstractSubscriber" = None
    ):
        self._stack.push_context_onto_test(self._clear_config_after(proxy, subscriber))

    def switch_off_after_session(self, proxy: AbstractProxy):
        self._stack.push_context_onto_session(self._switch_off_after(proxy))


@pytest.fixture(name="telescope_controller")
def telescope_controller(context):
    return TelescopeController(context)


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
    def wait_for_busy(self):
        """"""

    @abc.abstractmethod
    def wait_for_resourcing(self):
        """"""

    @abc.abstractmethod
    def wait_for_idle(self):
        """"""

    @abc.abstractmethod
    def wait_for_ready(self):
        """"""

    @abc.abstractmethod
    def wait_for_configuring(self):
        """"""

    @abc.abstractmethod
    def wait_for_empty(self):
        """"""

    @abc.abstractmethod
    def wait_for_off(self):
        """"""

    @abc.abstractmethod
    def first_state_event(self):
        """"""

    @abc.abstractmethod
    def next_state_event(self):
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


@pytest.fixture(name="running_telescope")
def fxt_running(proxy: AbstractProxy, telescope_controller: TelescopeController):
    telescope_controller.switch_off_after_session(proxy)
    proxy.command_on()


@pytest.fixture(name="machine_in_idle")
def fxt_machine_in_idle(
    running_telescope,
    proxy: AbstractProxy,
    telescope_controller: TelescopeController,
    subscriber: AbstractSubscriber,
):
    proxy.subscribe(subscriber, "obs_state")
    telescope_controller.release_resources_after(proxy)
    proxy.command_assign_resources()


@given("a machine that is Off")
def a_machine_that_is_Off(proxy: AbstractProxy):
    proxy.command_off()


@given("a machine that is On")
def a_machine_that_is_on(proxy: AbstractProxy):
    proxy.command_on()


@given("a machine that is in IDLE state")
def a_machine_that_is_in_the_idle_state(
    running_telescope,
    proxy: AbstractProxy,
    telescope_controller: TelescopeController,
):
    telescope_controller.release_resources_after(proxy)
    proxy.command_assign_resources()
    assert_that(proxy.obs_state).is_equal_to("IDLE")


@given("a machine that is in READY state")
def a_machine_that_is_in_the_ready_state(
    machine_in_idle,
    proxy: AbstractProxy,
    telescope_controller: TelescopeController,
):
    telescope_controller.clear_config_after(proxy)
    proxy.command_configure()
    assert_that(proxy.obs_state).is_equal_to("READY")


# --- Whens ---


@when("I command it to switch on", target_fixture="command_results")
def when_I_command_it_to_switch_on(
    proxy: AbstractProxy, subscriber: AbstractSubscriber
):
    proxy.subscribe(subscriber, "state")
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
    proxy.subscribe(
        subscriber,
    )
    proxy.command_on_background(0.5)
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


@when("I assign resources to it", target_fixture="command_results")
def when_i_assign_resources_to_it(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    proxy.subscribe(subscriber, "obs_state")
    telescope_controller.release_resources_after(proxy)
    proxy.command_assign_resources()
    return (proxy, subscriber)


@when("I configure it for a scan", target_fixture="command_results")
def when_i_configure_it(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    proxy.subscribe(subscriber, "obs_state")
    telescope_controller.clear_config_after(proxy)
    proxy.command_configure()
    return (proxy, subscriber)


@when("(in the background) I assign resources to it", target_fixture="command_results")
def when_background_i_assign_resources_to_it(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    proxy.subscribe(subscriber, "obs_state")
    telescope_controller.release_resources_after(proxy, subscriber)
    proxy.command_background_assign_resources(0.5)
    return (proxy, subscriber)


@when("(in the background) I configure it for a scan", target_fixture="command_results")
def when_background_i_configure_it(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    proxy.subscribe(subscriber, "obs_state")
    telescope_controller.clear_config_after(proxy, subscriber)
    proxy.command_background_configure(0.5)
    return (proxy, subscriber)


@when("I release the resources", target_fixture="command_results")
def when_i_release_the_resources(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    telescope_controller.clear_release_after()
    proxy.subscribe(subscriber, "obs_state")
    proxy.command_release_resources()
    return (proxy, subscriber)


@when("I clear the configuration", target_fixture="command_results")
def when_i_clear_the_configuration(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    telescope_controller.disable_clear_config_after()
    proxy.subscribe(subscriber, "obs_state")
    proxy.command_clear_config()
    return (proxy, subscriber)


@when("(in the background) I release the resources", target_fixture="command_results")
def when_background_i_release_resources_to_it(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    telescope_controller.clear_release_after()
    proxy.subscribe(subscriber, "obs_state")
    proxy.command_background_release_resources(0.5)
    return (proxy, subscriber)


@when("(in the background) I clear the configuration", target_fixture="command_results")
def when_background_i_clear_the_configuration(
    proxy: AbstractProxy,
    subscriber: AbstractSubscriber,
    telescope_controller: TelescopeController,
):
    telescope_controller.disable_clear_config_after()
    proxy.subscribe(subscriber, "obs_state")
    proxy.command_background_clear_config(0.5)
    return (proxy, subscriber)


@when("I command it again to assign resources", target_fixture="failed_result")
def when_I_command_it_again_to_assign_resources(proxy: AbstractProxy):
    try:
        proxy.command_assign_resources()
    except Exception as exception:
        return exception


@when("I command it again to configure", target_fixture="failed_result")
def when_I_command_it_again_to_configure(proxy: AbstractProxy):
    try:
        proxy.command_configure()
    except Exception as exception:
        return exception


# --- Thens ---


@then(
    "the machine should first go into RESOURCING state",
    target_fixture="command_results",
)
def then_machine_should_first_go_into_resourcing_state(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    _, subscriber = command_results
    subscriber.wait_for_resourcing()
    assert_that(subscriber.first_obs_state_event()).is_equal_to("RESOURCING")
    return _, subscriber


@then(
    "the machine should first go into CONFIGURING state",
    target_fixture="command_results",
)
def then_machine_should_first_go_into_configuring_state(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    _, subscriber = command_results
    subscriber.wait_for_configuring()
    assert_that(subscriber.first_obs_state_event()).is_equal_to("CONFIGURING")
    return _, subscriber


@then(
    "the machine should go into IDLE state and remain there",
    target_fixture="command_results",
)
def then_the_machine_should_go_into_idle_state(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_idle()
    assert_that(subscriber.next_obs_state_event()).is_equal_to("IDLE")
    assert_that(proxy.obs_state).is_equal_to("IDLE")


@then(
    "the machine should be in IDLE state",
    target_fixture="command_results",
)
def then_the_machine_should_be_in_idle_state(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_idle()
    assert_that(proxy.obs_state).is_equal_to("IDLE")


@then(
    "the machine should go into READY state and remain there",
    target_fixture="command_results",
)
def then_the_machine_should_go_into_ready_state(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_ready()
    assert_that(subscriber.next_obs_state_event()).is_equal_to("READY")
    assert_that(proxy.obs_state).is_equal_to("READY")


@then(
    "the machine should be in EMPTY state",
    target_fixture="command_results",
)
def then_the_machine_should_go_into_empty_state(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_empty()
    assert_that(subscriber.next_obs_state_event()).is_equal_to("EMPTY")
    assert_that(proxy.obs_state).is_equal_to("EMPTY")


@then("the server should first be busy")
def then_the_server_should_first_be_on(
    command_results: tuple[AbstractProxy, AbstractSubscriber]
):
    proxy, subscriber = command_results
    subscriber.wait_for_busy()
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
