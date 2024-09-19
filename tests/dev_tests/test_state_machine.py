from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import mock
from assertpy import assert_that
from time import sleep
import pytest

from mv.state_machine import (
    set_factory_for_memory_use_only,
    get_state_machine,
    get_state_machine_rev2,
    StateMachine,
    StateMachine_Rev2,
    reset_state_machine,
)


class FakeTicker:

    def __init__(self):
        self._sleeping = Event()
        self._unblocked = Event()
        self._initiated_sleep = False

    def stop_sleeping(self):
        self.wait_until_sleeping(10)
        self._unblocked.set()
        self._sleeping.clear()

    def tick(self):
        if self._initiated_sleep:
            self.stop_sleeping()
        self.wait_until_sleeping()
        self._initiated_sleep = True

    def tock(self):
        self.stop_sleeping()

    def clear(self):
        self._unblocked.set()

    def fake_sleep(self, _):
        self._sleeping.set()
        returned_without_time_out = self._unblocked.wait(timeout=10)
        if not returned_without_time_out:
            raise Exception(
                "returned with the timeout of 10 seconds, did you remember to tick?"
            )
        self._unblocked.clear()

    def wait_until_sleeping(self, timeout: float = 10):
        returned_without_time_out = self._sleeping.wait(timeout)
        if not returned_without_time_out:
            raise Exception(
                "returned with the timeout of 10 seconds, did you remember to tick?"
            )


@pytest.fixture(name="use_memory_state_machine")
def fxt_use_memory_state_machine():
    set_factory_for_memory_use_only()


@pytest.fixture(name="state_machine")
def fxt_state_machine():
    reset_state_machine()
    return get_state_machine_rev2()


@pytest.fixture(name="ticker")
def fxt_ticker():
    ticker = FakeTicker()
    yield ticker
    ticker.clear()


@pytest.fixture(name="use_fake_time")
def fxt_use_fake_time(ticker: FakeTicker):
    with mock.patch("mv._state_machine.state_machine.sleep") as mock_sleep:
        mock_sleep.side_effect = ticker.fake_sleep
        yield


@pytest.mark.usefixtures("use_memory_state_machine")
def test_switch_on_f(state_machine: StateMachine):
    state_machine.switch_on()
    assert_that(state_machine.state).is_equal_to("ON")


@pytest.mark.usefixtures("use_memory_state_machine")
def test_switch_off(state_machine: StateMachine):
    state_machine.switch_off()
    assert_that(state_machine.state).is_equal_to("OFF")


@pytest.mark.usefixtures("use_memory_state_machine")
def test_assign_resources(state_machine: StateMachine_Rev2):
    state_machine.assign_resources()
    assert_that(state_machine.obs_state).is_equal_to("IDLE")


@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_assign_resources_with_delay(
    state_machine: StateMachine_Rev2, ticker: FakeTicker
):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(state_machine.assign_resources, 10, {"delay": 10})
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("BUSY")
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("RESOURCING")
        ticker.tock()
        future.result()
    assert_that(state_machine.obs_state).is_equal_to("IDLE")
