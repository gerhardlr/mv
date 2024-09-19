from .base import AbstractStateUpdater, State, CombinedState, AbstractStateUpdater_Rev2

from .state_control import state_is_locked

__all__ = ["State", "StateUpdater_Rev2", "CombinedState"]


class StateUpdater(AbstractStateUpdater):

    def state_machine_is_busy(self) -> bool:
        return state_is_locked()


class StateUpdater_Rev2(AbstractStateUpdater_Rev2):

    def state_machine_is_busy(self) -> bool:
        return state_is_locked()
