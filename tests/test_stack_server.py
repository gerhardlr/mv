
from assertpy import assert_that
import pytest
from mv.stack_server import update_state
from .helpers import EventObserver

     
@pytest.mark.usefixtures("state_server")
def test_set_state(events_observer: EventObserver):
     with update_state() as state:
          state["foo"] = "bar"
     events_observer.wait_for_next_event()
     assert_that(events_observer.state).is_equal_to({"foo":"bar"})