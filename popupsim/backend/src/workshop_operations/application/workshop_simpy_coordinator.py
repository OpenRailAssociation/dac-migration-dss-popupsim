"""Workshop SimPy coordination for locomotive and transport operations."""

from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workshop_operations.application.orchestrator import WorkshopOrchestrator
    from workshop_operations.domain.entities.wagon import Wagon


class WorkshopSimPyCoordinator:
    """Coordinates SimPy processes for workshop operations."""

    def __init__(self, orchestrator: 'WorkshopOrchestrator') -> None:
        self.orchestrator = orchestrator

    def allocate_locomotive_process(self) -> Generator:
        """SimPy process for locomotive allocation."""
        loco = yield from self.orchestrator.locomotive_service.allocate(self.orchestrator)
        return loco

    def transport_wagons_process(self, wagons: list['Wagon'], from_track: str, to_track: str) -> Generator:
        """SimPy process for wagon transport between tracks."""
        from workshop_operations.infrastructure.routing.transport_job import TransportJob
        from workshop_operations.infrastructure.routing.transport_job import execute_transport_job

        job = TransportJob(wagons=wagons, from_track=from_track, to_track=to_track)
        yield from execute_transport_job(self.orchestrator, job, self.orchestrator.locomotive_service)
