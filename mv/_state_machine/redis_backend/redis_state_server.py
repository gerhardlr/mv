from threading import Event
from redis.client import PubSub, PubSubWorkerThread
from .base import AbstractPublisher, AbstractStateServer, AbstractStateUpdater

from .state import get_state_control_signals


class RedisStateServer(AbstractStateServer):

    def __init__(
        self,
        publisher: AbstractPublisher,
        redis_producer: PubSub,
        state_updater: AbstractStateUpdater,
    ):
        self._publisher = publisher
        self._started_flag = Event()
        self._server_thread: None | PubSubWorkerThread = None
        self._updater = state_updater
        self._redis_producer = redis_producer

    def _server(self):
        while True:
            self._started_flag.set()
            signal = get_state_control_signals()
            if signal == "STATE_CHANGED":
                state = self._updater.get_state()
                self._publisher.publish(state)
            else:
                self._started_flag.clear()
                return

    def _parse_message(self, message: dict):
        return message["data"].decode("utf-8")

    def _handler(self, message: dict):
        signal = self._parse_message(message)
        if signal == "STATE_CHANGED":
            state = self._updater.get_state()
            self._publisher.publish(state)

    def start_server(self):
        self._redis_producer.subscribe(**{"state_control_signals": self._handler})
        self._server_thread = self._redis_producer.run_in_thread(sleep_time=0.001)

    def stop_server(self):
        if self._server_thread:
            self._server_thread.stop()
