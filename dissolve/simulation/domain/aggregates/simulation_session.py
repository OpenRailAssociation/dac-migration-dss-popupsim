"""Simulation session aggregate."""

from typing import TYPE_CHECKING

from configuration.domain.models.scenario import Scenario

from simulation.domain.ports.simulation_engine_port import SimulationEnginePort

if TYPE_CHECKING:
    from simulation.domain.ports.context_port import BoundedContextPort


class SimulationSession:
    """Complete simulation run with lifecycle management."""

    def __init__(self, scenario: Scenario, engine: SimulationEnginePort) -> None:
        self.scenario = scenario
        self.engine = engine
        self.contexts: dict[str, BoundedContextPort] = {}
        self._is_running = False

    def register_context(self, name: str, context: "BoundedContextPort") -> None:
        """Register bounded context."""
        self.contexts[name] = context

    def start(self) -> None:
        """Start simulation."""
        self._is_running = True

    def stop(self) -> None:
        """Stop simulation."""
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self._is_running

    @property
    def current_time(self) -> float:
        """Get current simulation time."""
        return self.engine.current_time()
