from copy import deepcopy

from .base import CombinedState

_state: CombinedState = {}


def get_state():
    global _state
    state_copy = deepcopy(_state)
    return state_copy


def set_state(state: CombinedState):
    global _state
    _state = state
