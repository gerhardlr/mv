from copy import deepcopy
from typing import Any


_state: dict[str, Any] = {}


def get_state():
    global _state
    state_copy = deepcopy(_state)
    return state_copy


def set_state(state: dict[str, Any]):
    global _state
    _state = state
