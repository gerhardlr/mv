from queue import Queue
from threading import Event

from ..conftest import AbstractSubscriber
from mv.state_machine import StateSubscriber
from mv.data_types import ObsState, State


class Subscriber(AbstractSubscriber, StateSubscriber):

    def __init__(self) -> None:
        self._state_on = Event()
        self._state_events = Queue()
        self._obs_state_events = Queue()
        self._state_off = Event()
        self._state_resourcing = Event()
        self._state_idle = Event()
        self._state_empty = Event()
        self._state_configuring = Event()
        self._state_ready = Event()
        self._busy = Event()
        self._iter: None | int = None
        self._obs_state_iter = None
        StateSubscriber.__init__(self)
        self._index = None

    def first_state_event(self):
        self._iter = 0
        if len(self._state_events.queue) > self._iter:
            return self._state_events.queue[self._iter]
        return None

    def first_obs_state_event(self):
        self._obs_state_iter = 0
        if len(self._obs_state_events.queue) > self._obs_state_iter:
            return self._obs_state_events.queue[self._obs_state_iter]
        return None

    def next_obs_state_event(self):
        assert (
            self._obs_state_iter is not None
        ), "Did you remember to call first_event() first?"
        self._obs_state_iter += 1
        if len(self._obs_state_events.queue) > self._obs_state_iter:
            return self._obs_state_events.queue[self._obs_state_iter]
        return None

    def next_state_event(self):
        assert self._iter is not None, "Did you remember to call first_event() first?"
        self._iter += 1
        if len(self._state_events.queue) > self._iter:
            return self._state_events.queue[self._iter]
        return None

    def _add_obs_state_event(self, event: ObsState):
        if self.init_obs_state != event:
            self._obs_state_events.put(event)

    def _add_state_event(self, event: State):
        if self.init_state != event:
            self._state_events.put(event)

    def push_event(self, event: State | ObsState):
        if event == "ON":
            self._state_on.set()
            self._add_state_event(event)
        elif event == "OFF":
            self._state_off.set()
            self._add_state_event(event)
        elif event == "BUSY":
            self._busy.set()
            self._add_state_event(event)
        elif event == "RESOURCING":
            self._state_resourcing.set()
            self._add_obs_state_event(event)
        elif event == "IDLE":
            self._state_empty.clear()
            self._state_idle.set()
            self._add_obs_state_event(event)
        elif event == "EMPTY":
            self._state_empty.set()
            self._add_obs_state_event(event)
        elif event == "CONFIGURING":
            self._state_configuring.set()
            self._add_obs_state_event(event)
        elif event == "READY":
            self._state_idle.clear()
            self._state_ready.set()
            self._add_obs_state_event(event)

    def wait_for_on(self):
        self._state_on.wait()

    def wait_for_busy(self):
        self._busy.wait()

    def wait_for_off(self):
        self._state_off.wait()

    def wait_for_resourcing(self):
        self._state_resourcing.wait()

    def wait_for_idle(self):
        self._state_idle.wait()

    def wait_for_empty(self):
        self._state_empty.wait()

    def wait_for_configuring(self):
        self._state_configuring.wait()

    def wait_for_ready(self):
        self._state_ready.wait()
