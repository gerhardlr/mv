import asyncio
from threading import Event
from typing import TypeVar
import queue
import logging
from mv.state_machine import AbstractPublisher
from mv.client import AsynchAbstractObserver, AbstractObserver


logger = logging.getLogger()


T = TypeVar("T")


class EventObserver:

    def __init__(self) -> None:
        self.state: None | dict = None
        self._new_event = Event()

    def set_event(self, event: dict):
        self.state = event
        self._new_event.set()

    def wait_for_next_event(self):
        assert self._new_event.wait(1)
        self._new_event.clear()


class Publisher(AbstractPublisher):

    def __init__(self) -> None:
        self._observer: None | EventObserver = None

    def subscribe(self, observer: EventObserver):
        self._observer = observer

    def publish(self, state):
        if self._observer:
            self._observer.set_event(state)


class MessageObserver(AbstractObserver):

    def __init__(self) -> None:
        self.message = queue.Queue()

    def push_event(self, message):
        logger.info(f"{message} receieved")
        self.message.put_nowait(message)


class AsynchMessageObserver(AsynchAbstractObserver):

    def __init__(self) -> None:
        self.message = asyncio.Queue()

    async def push_event(self, message):
        logger.info(f"{message} receieved")
        self.message.put_nowait(message)
