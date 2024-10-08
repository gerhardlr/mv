from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from threading import Event
from typing import Any, Callable
from unittest import mock
from assertpy import assert_that
import pytest
from time import sleep

from mv.state_machine import (
    set_factory_for_memory_use_only,
    get_state_machine,
    StateMachine,
    reset_state_machine,
    CommandNotAllowed,
)


def polled_sleep(
    timeout: float = 10,
    poll_period: float = 0.1,
):
    wait_time = 0
    while wait_time < timeout:
        yield True
        sleep(poll_period)
        wait_time += poll_period
    yield False


class CommandNotIgnored(Exception):
    pass


class FakeTicker:

    def __init__(self):
        self._sleeping = Event()
        self._unblocked = Event()
        self._initiated_sleep = False
        self.sleep_called = 0
        self._future = None
        self._executor = None
        self._canceled = False

    def cancel_sleep(self):
        self._canceled = True

    def stop_sleeping(self):
        self.wait_until_sleeping(10)
        self._unblocked.set()
        self._sleeping.clear()

    def assert_command_ignored(self):
        try:
            self._future.result(0.1)
        except TimeoutError as time_out_err:
            if self._sleeping.is_set():
                self._unblocked.clear()
            raise CommandNotIgnored() from time_out_err
        except Exception as exception:
            raise CommandNotIgnored() from exception
        # if sleep not called then we can assume the method wasnt' ran
        if self.sleep_called != 0:
            raise CommandNotIgnored()

    @contextmanager
    def tick_for(self, command: Callable[[], Any]):
        with ThreadPoolExecutor(max_workers=2) as executor:
            self._executor = executor
            self._future = executor.submit(command)
            yield

    def tick(self):
        """
        Advance the program to the point where a thread is sleeping.
        If the thread is already sleeping it will advance to the point where the next sleep
        command is called.
        """
        if self._initiated_sleep:
            self.stop_sleeping()
        self.wait_until_sleeping()
        self._initiated_sleep = True

    def tock(self):
        """
        Lets a thread continue by breaking the sleeping block.
        """
        self.stop_sleeping()
        return self._future.result()

    def clear(self):
        self._unblocked.set()

    def fake_sleep(self, _):
        self.sleep_called += 1
        if self._canceled:
            return
        self._sleeping.set()
        returned_without_time_out = self._unblocked.wait(timeout=10)
        if not returned_without_time_out:
            raise Exception(
                "returned with the timeout of 10 seconds, did you remember to tick?"
            )
        self._unblocked.clear()

    def wait_until_sleeping(self, timeout: float = 5):
        assert self._future
        sleep_interval = polled_sleep(timeout)
        while next(sleep_interval):
            if self._future.done():
                if exception := self._future.exception():
                    raise exception
                return self._future.result()
            if self._sleeping.is_set():
                return
        raise Exception(
            f"returned with the timeout of {timeout} seconds, did you remember to tick?"
        )


@pytest.fixture(name="use_memory_state_machine")
def fxt_use_memory_state_machine():
    set_factory_for_memory_use_only()


@pytest.fixture(name="state_machine")
def fxt_state_machine():
    reset_state_machine()
    state_machine = get_state_machine()
    assert_that(state_machine.state).is_equal_to(None)
    assert_that(state_machine.obs_state).is_equal_to(None)
    return state_machine


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
def test_switch_on(state_machine: StateMachine):
    state_machine.switch_on()
    assert_that(state_machine.state).is_equal_to("ON")


@pytest.fixture(name="set on")
def fxt_set_on(state_machine: StateMachine):
    state_machine.switch_on()
    assert_that(state_machine.state).is_equal_to("ON")


@pytest.mark.usefixtures("set on")
@pytest.mark.usefixtures("use_memory_state_machine")
def test_switch_off(state_machine: StateMachine):
    state_machine.switch_off()
    assert_that(state_machine.state).is_equal_to("OFF")
    assert_that(state_machine.obs_state).is_equal_to(None)


@pytest.mark.usefixtures("set on")
@pytest.mark.usefixtures("use_memory_state_machine")
def test_assign_resources(state_machine: StateMachine):
    state_machine.assign_resources()
    assert_that(state_machine.obs_state).is_equal_to("IDLE")


@pytest.fixture(name="on_state_machine")
def fxt_on_state_machine(state_machine: StateMachine):
    state_machine.switch_on()
    return state_machine


@pytest.fixture(name="assign resources")
def fxt_assign_resources(on_state_machine: StateMachine):
    on_state_machine.assign_resources()
    assert_that(on_state_machine.obs_state).is_equal_to("IDLE")


@pytest.fixture(name="idle_state_machine")
def fxt_idle_state_machine(on_state_machine: StateMachine):
    on_state_machine.assign_resources()
    assert_that(on_state_machine.obs_state).is_equal_to("IDLE")
    return on_state_machine


@pytest.fixture(name="configure for scan")
def fxt_configure_for_scan(idle_state_machine: StateMachine):
    idle_state_machine.configure()
    assert_that(idle_state_machine.obs_state).is_equal_to("READY")


@pytest.fixture(name="ready_state_machine")
def fxt_ready_state_machine(idle_state_machine: StateMachine):
    idle_state_machine.configure()
    assert_that(idle_state_machine.obs_state).is_equal_to("READY")
    return idle_state_machine


@pytest.mark.usefixtures("set on")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_assign_resources_with_delay(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.assign_resources(10, {"delay": 10})

    with ticker.tick_for(command):
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("BUSY")
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("RESOURCING")
        ticker.tock()
    assert_that(state_machine.obs_state).is_equal_to("IDLE")


@pytest.mark.usefixtures("assign resources")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_release_resources_with_delay(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.release_resources(10, {"delay": 10})

    with ticker.tick_for(command):
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("BUSY")
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("RESOURCING")
        ticker.tock()
    assert_that(state_machine.obs_state).is_equal_to("EMPTY")


@pytest.mark.usefixtures("assign resources")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_configure_with_delay(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.configure(10, {"delay": 10})

    with ticker.tick_for(command):
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("BUSY")
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("CONFIGURING")
        ticker.tock()
    assert_that(state_machine.obs_state).is_equal_to("READY")


@pytest.mark.usefixtures("configure for scan")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_clear_configure_with_delay(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.clear_config(10)

    with ticker.tick_for(command):
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("BUSY")
        ticker.tock()
    assert_that(state_machine.obs_state).is_equal_to("IDLE")


@pytest.mark.usefixtures("configure for scan")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_scan_with_delay(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.scan(10, {"delay": 10})

    with ticker.tick_for(command):
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("BUSY")
        ticker.tick()
        assert_that(state_machine.obs_state).is_equal_to("SCANNING")
        ticker.tock()
    assert_that(state_machine.obs_state).is_equal_to("READY")


@pytest.mark.usefixtures("set on")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_ignore(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.switch_on(10)

    with ticker.tick_for(command):
        ticker.assert_command_ignored()


@pytest.mark.usefixtures("assign resources")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_ignore_assign_resources(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.assign_resources(10, {"delay": 10})

    with ticker.tick_for(command):
        ticker.assert_command_ignored()


@pytest.mark.usefixtures("assign resources")
@pytest.mark.usefixtures("use_memory_state_machine")
@pytest.mark.usefixtures("use_fake_time")
def test_ignore_clear_configure(state_machine: StateMachine, ticker: FakeTicker):

    def command():
        state_machine.clear_config(10)

    ticker.cancel_sleep()
    with ticker.tick_for(command):
        ticker.assert_command_ignored()


def test_not_allowed(state_machine: StateMachine):
    with pytest.raises(CommandNotAllowed):
        state_machine.assign_resources()
    with pytest.raises(CommandNotAllowed):
        state_machine.release_resources()
    with pytest.raises(CommandNotAllowed):
        state_machine.configure()
    with pytest.raises(CommandNotAllowed):
        state_machine.clear_config()
    with pytest.raises(CommandNotAllowed):
        state_machine.scan()


@pytest.mark.usefixtures("set on")
def test_not_allowed_when_empty(state_machine: StateMachine):
    """
    with pytest.raises(CommandNotAllowed):
        state_machine.switch_off()
    with pytest.raises(CommandNotAllowed):
        state_machine.assign_resources()
    with pytest.raises(CommandNotAllowed):
        state_machine.release_resources()
    """
    with pytest.raises(CommandNotAllowed):
        state_machine.configure()
    with pytest.raises(CommandNotAllowed):
        state_machine.clear_config()
    with pytest.raises(CommandNotAllowed):
        state_machine.scan()


@pytest.mark.usefixtures("assign resources")
def test_not_allowed_when_idle(state_machine: StateMachine):
    with pytest.raises(CommandNotAllowed):
        state_machine.switch_off()
    """
    with pytest.raises(CommandNotAllowed):
        state_machine.assign_resources()
    with pytest.raises(CommandNotAllowed):
        state_machine.release_resources()
    with pytest.raises(CommandNotAllowed):
        state_machine.configure()
    with pytest.raises(CommandNotAllowed):
        state_machine.clear_config()
    """
    with pytest.raises(CommandNotAllowed):
        state_machine.scan()


@pytest.mark.usefixtures("configure for scan")
def test_not_allowed_when_ready(state_machine: StateMachine):
    with pytest.raises(CommandNotAllowed):
        state_machine.switch_off()
    with pytest.raises(CommandNotAllowed):
        state_machine.assign_resources()
    with pytest.raises(CommandNotAllowed):
        state_machine.release_resources()
    """
    with pytest.raises(CommandNotAllowed):
        state_machine.configure()
    with pytest.raises(CommandNotAllowed):
        state_machine.clear_config()
    with pytest.raises(CommandNotAllowed):
        state_machine.scan()
    """
