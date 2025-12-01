"""SimPy coordinator for parking operations."""

from collections.abc import Generator
import logging
from typing import Any

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.infrastructure.routing.transport_job import TransportJob
from workshop_operations.infrastructure.routing.transport_job import execute_transport_job

logger = logging.getLogger(__name__)


class ParkingSimPyCoordinator:
    """Coordinates SimPy processes for parking operations."""

    def move_to_parking_simpy(self, orchestrator: Any) -> Generator[Any]:
        """SimPy process for moving wagons to parking tracks."""
        logger.info('Starting move to parking process')

        retrofitted_track = orchestrator.retrofitted_tracks[0]
        wagons_batch: list[Wagon] = []

        while True:
            # Get wagon from retrofitted wagons store
            wagon: Wagon = yield from orchestrator.get_wagon_from_retrofitted()
            wagons_batch.append(wagon)

            # Collect additional wagons if available
            while len(orchestrator.retrofitted_wagons_ready.items) > 0 and len(wagons_batch) < 10:
                additional_wagon: Wagon = yield from orchestrator.get_wagon_from_retrofitted()
                wagons_batch.append(additional_wagon)

            # Use parking area to select track
            parking_track = orchestrator.yard_operations.parking_area.select_parking_track(wagons_batch)

            if not parking_track:
                # No parking capacity, put wagons back and wait
                for wagon in wagons_batch:
                    yield from orchestrator.put_wagon_if_fits_retrofitted(wagon)
                wagons_batch = []
                yield orchestrator.sim.delay(1.0)
                continue

            # Determine which wagons fit
            wagons_to_move, wagons_to_requeue = orchestrator.yard_operations.parking_area.get_wagons_that_fit(
                parking_track, wagons_batch
            )

            # Put back wagons that don't fit
            for wagon in wagons_to_requeue:
                yield from orchestrator.put_wagon_if_fits_retrofitted(wagon)

            wagons_batch = []

            if not wagons_to_move:
                orchestrator.yard_operations.parking_area.advance_to_next_track()
                yield orchestrator.sim.delay(1.0)
                continue

            # Reserve parking capacity
            total_length = sum(w.length for w in wagons_to_move)
            if not orchestrator.track_capacity.can_add_wagon(parking_track.id, total_length):
                for wagon in wagons_to_move:
                    yield from orchestrator.put_wagon_if_fits_retrofitted(wagon)
                orchestrator.yard_operations.parking_area.advance_to_next_track()
                yield orchestrator.sim.delay(1.0)
                continue

            # Execute transport job
            job = TransportJob(
                wagons=wagons_to_move,
                from_track=retrofitted_track.id,
                to_track=parking_track.id,
            )
            yield from execute_transport_job(orchestrator, job, orchestrator.locomotive_service)

            # Update final wagon status
            for wagon in wagons_to_move:
                wagon.status = WagonStatus.PARKING
                logger.info('Wagon %s moved to parking track %s', wagon.id, parking_track.id)

            # Check if parking track is full
            if not any(orchestrator.track_capacity.can_add_wagon(parking_track.id, 10.0) for _ in range(1)):
                orchestrator.yard_operations.parking_area.advance_to_next_track()
                logger.debug('Parking track %s full, switching to next', parking_track.id)
