"""SimPy coordinator for parking operations."""

import logging
from collections.abc import Generator
from typing import Any

from MVP.workshop_operations.domain.entities.wagon import (
    Wagon,
    WagonStatus,
)
from MVP.workshop_operations.infrastructure.routing.transport_job import (
    TransportJob,
    execute_transport_job,
)

logger = logging.getLogger(__name__)


class ParkingSimPyCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates SimPy processes for parking operations."""

    def __init__(self, orchestrator: Any) -> None:
        """Initialize parking coordinator.

        Parameters
        ----------
        orchestrator : Any
            Workshop operations context providing access to simulation resources.
        """
        self.orchestrator = orchestrator
        # Get batch size from largest workshop capacity
        max_stations = max(
            (w.retrofit_stations for w in orchestrator.workshops), default=10
        )
        self.batch_size = max_stations

    def _collect_wagon_batch(self) -> Generator[Any, Any, list[Wagon]]:
        """Collect batch of wagons from retrofitted store."""
        wagon: Wagon = yield from self.orchestrator.get_wagon_from_retrofitted()
        wagons_batch = [wagon]

        while (
            len(self.orchestrator.retrofitted_wagons_ready.items) > 0
            and len(wagons_batch) < self.batch_size
        ):
            additional_wagon: Wagon = yield from self.orchestrator.get_wagon_from_retrofitted()
            wagons_batch.append(additional_wagon)

        return wagons_batch

    def _requeue_wagons(self, wagons: list[Wagon]) -> Generator[Any]:
        """Put wagons back to retrofitted store."""
        for wagon in wagons:
            yield from self.orchestrator.put_wagon_if_fits_retrofitted(wagon)

    def _execute_parking_transport(
        self, wagons: list[Wagon], from_track_id: str, to_track_id: str
    ) -> Generator[Any]:
        """Execute transport job and update wagon status."""
        job = TransportJob(
            wagons=wagons, from_track=from_track_id, to_track=to_track_id
        )
        yield from execute_transport_job(
            self.orchestrator, job, self.orchestrator.locomotive_service
        )

        for wagon in wagons:
            wagon.status = WagonStatus.PARKING
            logger.info("Wagon %s moved to parking track %s", wagon.id, to_track_id)

    def move_to_parking_simpy(self) -> Generator[Any]:
        """SimPy process for moving wagons to parking tracks.
        
        Note: This process should only move wagons that are ready for parking,
        not flush all wagons at simulation end.
        """
        logger.info("Starting move to parking process")
        retrofitted_track = self.orchestrator.retrofitted_tracks[0]

        while True:
            wagons_batch: list[Wagon] = yield from self._collect_wagon_batch()
            parking_track = (
                self.orchestrator.yard_operations.parking_area.select_parking_track(
                    wagons_batch
                )
            )

            if not parking_track:
                yield from self._requeue_wagons(wagons_batch)
                continue

            wagons_to_move, wagons_to_requeue = (
                self.orchestrator.yard_operations.parking_area.get_wagons_that_fit(
                    parking_track, wagons_batch
                )
            )
            yield from self._requeue_wagons(wagons_to_requeue)

            if not wagons_to_move:
                self.orchestrator.yard_operations.parking_area.advance_to_next_track()
                continue

            total_length = sum(w.length for w in wagons_to_move)
            if not self.orchestrator.track_capacity.can_add_wagon(
                parking_track.id, total_length
            ):
                yield from self._requeue_wagons(wagons_to_move)
                self.orchestrator.yard_operations.parking_area.advance_to_next_track()
                continue

            yield from self._execute_parking_transport(
                wagons_to_move, retrofitted_track.id, parking_track.id
            )
