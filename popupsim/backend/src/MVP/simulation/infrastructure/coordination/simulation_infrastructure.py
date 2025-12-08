"""Simulation infrastructure for cross-context coordination."""

from dataclasses import dataclass
from typing import Any

from MVP.simulation.domain.ports.simulation_engine_port import (
    SimulationEnginePort,
)


@dataclass
class SimulationInfrastructure:
    """Coordination infrastructure for cross-context communication.

    Contains only coordination mechanisms (SimPy Stores), not domain collections.
    """

    engine: SimulationEnginePort

    # Wagon flow coordination (SimPy Stores)
    incoming_wagons: Any  # Store - External Trains → Yard
    wagons_for_retrofit: dict[str, Any]  # Store per workshop - Yard → PopUp
    retrofitted_wagons: Any  # Store - PopUp → Yard

    @classmethod
    def create(
        cls, engine: SimulationEnginePort, workshop_ids: list[str]
    ) -> "SimulationInfrastructure":
        """Create simulation infrastructure with coordination queues."""
        return cls(
            engine=engine,
            incoming_wagons=engine.create_store(),
            wagons_for_retrofit={
                workshop_id: engine.create_store() for workshop_id in workshop_ids
            },
            retrofitted_wagons=engine.create_store(),
        )
