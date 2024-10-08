import abc
from typing import Any, TypeVar
from mv.data_types import DelayArgs, ConfigArgs, State, ObsState
from mv.state_machine import StateSubscriber, CombinedState, Attribute

__all__ = ["DelayArgs", "ConfigArgs", "StateSubscriber", "CombinedState", "Attribute"]

T = TypeVar("T")


class AbstractObserver:

    @abc.abstractmethod
    def push_event(self, message: T):
        """"""


class AsynchAbstractObserver:

    @abc.abstractmethod
    async def push_event(self, message: T):
        """"""


class AbstractProxy:

    @abc.abstractmethod
    def subscribe(
        self,
        subscriber: StateSubscriber,
        attribute: Attribute = "state"
    ):
        """"""

    @abc.abstractmethod
    def command_on(self, delay: float | None = None):
        """"""

    @abc.abstractmethod
    def command_off(self, delay: float | None = None):
        """"""

    @abc.abstractmethod
    def command_on_background(self, delay: float = 0):
        """"""

    @abc.abstractmethod
    def command_off_background(self, delay: float = 0):
        """"""

    @abc.abstractmethod
    def command_assign_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_background_assign_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_release_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_background_release_resources(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_configure(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_background_configure(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_clear_config(self, delay: float | None = None):
        """"""

    @abc.abstractmethod
    def command_background_clear_config(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @abc.abstractmethod
    def command_scan(self, delay: float | None = None, config: dict[str, Any] = None):
        """"""

    @abc.abstractmethod
    def command_background_scan(
        self, delay: float | None = None, config: dict[str, Any] = None
    ):
        """"""

    @property
    @abc.abstractmethod
    def state(self) -> State:
        """"""

    @property
    @abc.abstractmethod
    def obs_state(self) -> ObsState:
        """"""
