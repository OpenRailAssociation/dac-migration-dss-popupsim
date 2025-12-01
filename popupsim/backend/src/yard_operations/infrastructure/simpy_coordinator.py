"""SimPy coordinator for yard operations."""

from collections.abc import Generator
import logging
from typing import Any

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.infrastructure.simulation.simpy_adapter import SimulationAdapter

from ..domain.services.hump_yard_service import HumpYardService

logger = logging.getLogger(__name__)


class YardSimPyCoordinator:
    """Coordinates SimPy processes for yard operations."""

    def __init__(self, sim_adapter: SimulationAdapter, hump_service: HumpYardService) -> None:
        self.sim = sim_adapter
        self.hump_service = hump_service

    def process_hump_classification_simpy(
        self,
        wagon: Wagon,
        wagons_queue: list[Wagon],
        rejected_queue: list[Wagon],
        classification_delay: float = 0.5,
    ) -> Generator[Any, Any]:
        """SimPy process for hump yard classification."""
        # SimPy timing for classification
        yield self.sim.delay(classification_delay)

        # Pure domain logic
        decision = self.hump_service.process_wagon(wagon, wagons_queue, rejected_queue)

        logger.debug('Hump classification completed for wagon %s: %s', wagon.id, decision.value)
