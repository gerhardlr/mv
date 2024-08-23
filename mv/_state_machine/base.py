import abc
from typing import Literal


State = Literal["ON","OFF"]

class StateSubscriber:

    @abc.abstractmethod
    def push_event(self, event: State):
        """"""

class AbstractPublisher:

    @abc.abstractmethod
    def publish(self, state):
        """"""