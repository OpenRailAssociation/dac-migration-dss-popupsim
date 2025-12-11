"""Protocol for contexts participating in simulation."""

from abc import abstractmethod
from typing import Any
from typing import Protocol


class SimulationContextProtocol(Protocol):
    """Protocol for bounded contexts participating in simulation."""

    @abstractmethod
    def initialize(self, infrastructure: Any, scenario: Any) -> None:
        """Initialize context with infrastructure and scenario."""

    @abstractmethod
    def start_processes(self) -> None:
        """Start context-specific simulation processes."""

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get context performance metrics."""

    def get_status(self) -> dict[str, Any]:
        """Get current context status."""
        return {'status': 'unknown'}

    def cleanup(self) -> None:
        """Cleanup context resources."""

    # Lifecycle event handlers (optional)
    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started event."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended event."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed event."""
