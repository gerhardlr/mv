import json
from pathlib import Path
from typing import cast
from assertpy import assert_that
import pytest
from mv.state_machine import StateUpdater
from .helpers import EventObserver


def test_set_state(state_updater: StateUpdater, events_observer: EventObserver):
    with state_updater.update_state() as state:
        state["foo"] = "bar"
    events_observer.wait_for_next_event()
    assert_that(events_observer.state).is_equal_to({"foo": "bar"})


@pytest.mark.usefixtures("reset_state")
@pytest.mark.usefixtures("persist_state_in_file")
def test_load_state_from_file(state_updater: StateUpdater):
    state = state_updater.get_state()
    assert_that(state).is_equal_to({})
    with state_updater.update_state() as state:
        state["state"] = "ON"
    with cast(Path, state_updater._path).open("r") as file:
        red_state = json.load(file)
    assert_that(red_state.get("state")).is_equal_to("ON")
