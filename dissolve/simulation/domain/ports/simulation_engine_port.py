"""Port for simulation engine abstraction."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from typing import Any


class SimulationEnginePort(ABC):
    """Port for simulation engine abstraction (SimPy, custom, etc.)."""

    @abstractmethod
    def current_time(self) -> float:
        """Get current simulation time in minutes."""

    @abstractmethod
    def schedule_process(self, process: Callable[..., Generator[Any, Any, Any]]) -> Any:
        """Schedule a process for execution."""

    @abstractmethod
    def create_resource(self, capacity: int) -> Any:
        """Create resource with capacity."""

    @abstractmethod
    def create_store(self, capacity: int | None = None) -> Any:
        """Create store for items."""

    @abstractmethod
    def delay(self, duration: float) -> Any:
        """Create delay event."""

    @abstractmethod
    def run(self, until: float | None = None) -> None:
        """Run simulation until time or completion."""

    @abstractmethod
    def create_event(self) -> Any:
        """Create event for signaling."""
