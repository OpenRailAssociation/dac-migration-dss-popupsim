"""SimPy coordinator for shunting operations."""

from collections.abc import Generator
import logging
from typing import Any

from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.infrastructure.routing.transport_job import TransportJob
from workshop_operations.infrastructure.routing.transport_job import execute_transport_job

logger = logging.getLogger(__name__)


class ShuntingSimPyCoordinator:
    """Coordinates SimPy processes for shunting operations."""

    def allocate_locomotive_simpy(self, orchestrator: Any) -> Generator[Any, Any, Locomotive]:
        """SimPy process for locomotive allocation."""
        loco = yield from orchestrator.locomotive_service.allocate(orchestrator)
        return loco

    def move_locomotive_simpy(
        self, orchestrator: Any, loco: Locomotive, from_track: str, to_track: str
    ) -> Generator[Any, Any]:
        """SimPy process for locomotive movement."""
        yield from orchestrator.locomotive_service.move(orchestrator, loco, from_track, to_track)

    def couple_wagons_simpy(
        self, orchestrator: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType
    ) -> Generator[Any, Any]:
        """SimPy process for wagon coupling."""
        yield from orchestrator.locomotive_service.couple_wagons(orchestrator, loco, wagon_count, coupler_type)

    def decouple_wagons_simpy(
        self, orchestrator: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType
    ) -> Generator[Any, Any]:
        """SimPy process for wagon decoupling."""
        yield from orchestrator.locomotive_service.decouple_wagons(orchestrator, loco, wagon_count, coupler_type)

    def execute_transport_simpy(
        self, orchestrator: Any, wagons: list[Wagon], from_track: str, to_track: str
    ) -> Generator[Any, Any]:
        """SimPy process for wagon transport."""
        job = TransportJob(wagons=wagons, from_track=from_track, to_track=to_track)
        yield from execute_transport_job(orchestrator, job, orchestrator.locomotive_service)

    def release_locomotive_simpy(self, orchestrator: Any, loco: Locomotive) -> Generator[Any, Any]:
        """SimPy process for locomotive release."""
        yield from orchestrator.locomotive_service.release(orchestrator, loco)
