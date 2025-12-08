"""Enhanced port for simulation engine abstraction."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from collections.abc import Generator
from datetime import timedelta
from typing import Any


class SimulationEnginePort(ABC):
    """Enhanced port defining interface for discrete event simulation engines."""

    # Core simulation methods
    @abstractmethod
    def current_time(self) -> float:
        """Get current simulation time."""

    @abstractmethod
    def delay(self, duration: float | timedelta) -> Generator[Any]:
        """Delay execution for specified duration (supports timedelta)."""

    @abstractmethod
    def schedule_process(self, process: Generator[Any] | Callable) -> Any:
        """Schedule a process to run (supports generators and callables)."""

    @abstractmethod
    def run(self, until: float | None = None) -> None:
        """Run simulation until specified time or completion."""

    # Resource management
    @abstractmethod
    def create_resource(self, capacity: int) -> Any:
        """Create a resource with specified capacity."""

    @abstractmethod
    def create_store(self, capacity: int | None = None) -> Any:
        """Create a store with optional capacity."""

    @abstractmethod
    def add_pre_run_hook(self, hook: Callable[..., None]) -> None:
        """Execute function before simulation run."""

    @abstractmethod
    def add_post_run_hook(self, hook: Callable[..., None]) -> None:
        """Execute function after simulation run."""

    # Enhanced capabilities (optional - provide default implementations)
    def get_simulation_stats(self) -> dict[str, Any]:
        """Get simulation statistics."""
        return {'current_time': self.current_time()}
