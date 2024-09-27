from .base import (
    State,
    CombinedState,
    AbstractStateUpdater,
)

from .state_control import state_is_locked

__all__ = ["State", "StateUpdater", "CombinedState"]


class StateUpdater(AbstractStateUpdater):

    def state_machine_is_busy(self) -> bool:
        return state_is_locked()
