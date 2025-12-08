"""Protocol for simulation context access."""

from typing import Any, Protocol

from MVP.configuration.domain.models.scenario import Scenario
from MVP.simulation.domain.ports.simulation_engine_port import (
    SimulationEnginePort,
)


class SimulationContextProtocol(Protocol):
    """Protocol for objects that provide simulation context."""

    @property
    def sim(self) -> SimulationEnginePort:
        """Get simulation engine."""

    @property
    def scenario(self) -> Scenario:
        """Get scenario configuration."""

    @property
    def locomotives(self) -> Any:
        """Get locomotives resource pool."""

    @property
    def track_capacity(self) -> Any:
        """Get track capacity manager."""

    @property
    def workshop_capacity(self) -> Any:
        """Get workshop capacity manager."""

    @property
    def wagon_state(self) -> Any:
        """Get wagon state manager."""

    @property
    def loco_state(self) -> Any:
        """Get locomotive state manager."""

    @property
    def locomotive_service(self) -> Any:
        """Get locomotive service."""

    @property
    def yard_operations(self) -> Any:
        """Get yard operations context."""

    @property
    def popup_retrofit(self) -> Any:
        """Get popup retrofit context."""

    @property
    def metrics(self) -> Any:
        """Get metrics aggregator."""
