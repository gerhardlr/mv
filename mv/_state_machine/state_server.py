from threading import Event, Thread
from .base import AbstractPublisher, AbstractStateServer, AbstractStateUpdater
from .state import get_state_control_signals, cntrl_set_server_stop


class StateServer(AbstractStateServer):

    def __init__(
        self, publisher: AbstractPublisher, state_updater: AbstractStateUpdater
    ):
        self._publisher = publisher
        self._started_flag = Event()
        self._server_thread: None | Thread = None
        self._updater = state_updater

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

    def start_server(self):
        self._server_thread = Thread(target=self._server, daemon=True)
        self._server_thread.start()
        self._started_flag.wait()

    def stop_server(self):
        cntrl_set_server_stop()
        if self._server_thread:
            self._server_thread.join(1)
