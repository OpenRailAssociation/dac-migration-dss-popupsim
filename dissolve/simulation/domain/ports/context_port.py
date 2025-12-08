"""Port for bounded contexts to participate in simulation."""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from simulation.domain.aggregates.simulation_session import SimulationSession


class BoundedContextPort(Protocol):
    """Port for bounded contexts to participate in simulation."""

    def initialize(self, simulation_session: "SimulationSession") -> None:
        """Initialize context with simulation session."""

    def start_processes(self) -> None:
        """Start context-specific simulation processes."""

    def get_metrics(self) -> dict[str, Any]:
        """Get context metrics."""

    def cleanup(self) -> None:
        """Cleanup context resources."""
