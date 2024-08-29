from .base import AbstractStateUpdater

from .state import state_is_locked


class StateUpdater(AbstractStateUpdater):

    def state_machine_is_busy(self) -> bool:
        return state_is_locked()
