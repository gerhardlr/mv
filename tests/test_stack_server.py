from threading import Event
from time import sleep

from assertpy import assert_that
import pytest
from mv.stack_server import state_server, AbstractPublisher, update_state


class Observer:

     def __init__(self) -> None:
          self.state: None | dict = None
          self._new_event = Event()

     def set_event(self,event: dict):
          self.state = event
          self._new_event.set()
     
     def wait_for_next_event(self):
          assert self._new_event.wait(1)
          self._new_event.clear()


class Publisher(AbstractPublisher):

     def __init__(self) -> None:
          self._observer: None | Observer  = None

     def subscribe(self, observer: Observer):
          self._observer = observer

     def publish(self, state):
          if self._observer:
             self._observer.set_event(state)


class Settings:

    publisher  = Publisher()



@pytest.fixture(name="settings")
def fxt_settings():
     return Settings()

    
@pytest.fixture(name="publisher")
def fxt_publisher(settings: Settings):
     return settings.publisher
     

@pytest.fixture(name="state_server")
def fxt_state_server(publisher: AbstractPublisher):
     with state_server(publisher):
          yield


@pytest.fixture(name="observer")
def fxt_observer(settings: Settings):
     assert settings.publisher
     observer = Observer()
     settings.publisher.subscribe(observer)
     return observer
     

@pytest.mark.usefixtures("state_server")
def test_set_state(observer: Observer):
     with update_state() as state:
          state["foo"] = "bar"
     observer.wait_for_next_event()
     assert_that(observer.state).is_equal_to({"foo":"bar"})