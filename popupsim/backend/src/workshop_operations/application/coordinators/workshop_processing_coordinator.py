"""Workshop processing coordination."""

from __future__ import annotations

from collections.abc import Generator
import logging
from typing import TYPE_CHECKING
from typing import Any

from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.domain.entities.wagon import WagonStatus

if TYPE_CHECKING:
    from workshop_operations.application.orchestrator import WorkshopOrchestrator
    from workshop_operations.domain.entities.wagon import Wagon
    from workshop_operations.domain.entities.workshop import Workshop

logger = logging.getLogger(__name__)


class WorkshopProcessingCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates workshop processing operations."""

    def __init__(self, orchestrator: WorkshopOrchestrator) -> None:
        self.orchestrator = orchestrator

    def move_wagons_to_stations(self) -> Generator:
        """Move wagon batches from retrofit track to stations."""
        scenario = self.orchestrator.scenario
        if not scenario.routes:
            raise ValueError('Scenario must have routes configured')

        logger.info('Starting wagon-to-station movement process')

        # Process each track independently
        for track_id in self.orchestrator.wagons_ready_for_stations:
            self.orchestrator.sim.run_process(self._process_track_batches, track_id)

        yield self.orchestrator.sim.delay(0)  # Ensure generator yields

    def _process_track_batches(self, workshop_track_id: str) -> Generator:
        """Process wagon batches for a single workshop track."""
        workshop = self.orchestrator.workshop_capacity.workshops_by_track[workshop_track_id]
        batch_size = workshop.retrofit_stations

        while True:
            batch_wagons, retrofit_track_id = yield from self._collect_wagon_batch(workshop_track_id, batch_size)

            if not batch_wagons or retrofit_track_id is None:
                continue

            yield from self._wait_for_workshop_ready(workshop_track_id, workshop)
            yield from self._deliver_batch_to_workshop(batch_wagons, retrofit_track_id, workshop.track)

    def _collect_wagon_batch(
        self, workshop_track_id: str, batch_size: int
    ) -> Generator[Any, Any, tuple[list[Wagon], str | None]]:
        """Collect wagon batch up to batch_size."""
        batch_wagons: list[Wagon] = []
        retrofit_track_id: str | None = None

        for i in range(batch_size):
            if i > 0 and len(self.orchestrator.wagons_ready_for_stations[workshop_track_id].items) == 0:
                break

            item = yield self.orchestrator.wagons_ready_for_stations[workshop_track_id].get()
            track_id, wagons = item
            if retrofit_track_id is None:
                retrofit_track_id = track_id
            batch_wagons.extend(wagons)

        return batch_wagons, retrofit_track_id

    def _wait_for_workshop_ready(self, workshop_track_id: str, workshop: Workshop) -> Generator:
        """Wait until workshop track and all stations are empty."""
        while True:
            track_empty = self.orchestrator.track_capacity.get_available_capacity(
                workshop_track_id
            ) == self.orchestrator.track_capacity.get_total_capacity(workshop_track_id)
            stations_empty = (
                self.orchestrator.workshop_capacity.get_available_stations(workshop_track_id)
                == workshop.retrofit_stations
            )
            if track_empty and stations_empty:
                break
            yield self.orchestrator.sim.delay(0.1)

    def _deliver_batch_to_workshop(
        self, batch: list[Wagon], retrofit_track_id: str, workshop_track_id: str
    ) -> Generator:
        """Move batch from retrofit track to workshop and start processing."""
        # Allocate locomotive
        loco = yield from self.orchestrator.locomotive_service.allocate(self.orchestrator)

        try:
            # Move to pickup location
            yield from self.orchestrator.locomotive_service.move(self.orchestrator, loco, loco.track, retrofit_track_id)

            # Couple wagons
            coupler_type = batch[0].coupler_type if batch else CouplerType.SCREW
            yield from self.orchestrator.locomotive_service.couple_wagons(
                self.orchestrator, loco, len(batch), coupler_type
            )

            # Update wagon states - remove from source track
            for wagon in batch:
                self.orchestrator.track_capacity.remove_wagon(retrofit_track_id, wagon.length)
                wagon.status = WagonStatus.MOVING
                wagon.source_track_id = retrofit_track_id
                wagon.destination_track_id = workshop_track_id
                wagon.track = None

            # Move to workshop
            yield from self.orchestrator.locomotive_service.move(
                self.orchestrator, loco, retrofit_track_id, workshop_track_id
            )

            # Decouple wagons
            yield from self.orchestrator.locomotive_service.decouple_wagons(
                self.orchestrator, loco, len(batch), coupler_type
            )

            # Update wagon states - add to destination track
            for wagon in batch:
                self.orchestrator.track_capacity.add_wagon(workshop_track_id, wagon.length)
                wagon.track = workshop_track_id
                wagon.source_track_id = None
                wagon.destination_track_id = None

            # Start wagon processing immediately
            yield from self._process_wagons_at_workshop(batch, workshop_track_id)

            # Return locomotive to parking
            parking_track_id = self.orchestrator.parking_tracks[0].id
            yield from self.orchestrator.locomotive_service.move(self.orchestrator, loco, loco.track, parking_track_id)

        finally:
            # Release locomotive
            yield from self.orchestrator.locomotive_service.release(self.orchestrator, loco)

    def _process_wagons_at_workshop(self, batch: list[Wagon], workshop_track_id: str) -> Generator:
        """Spawn processing for each wagon at workshop."""
        for wagon in batch:
            self.orchestrator.sim.run_process(self._process_single_wagon, wagon, workshop_track_id)
        yield self.orchestrator.sim.delay(0)

    def _process_single_wagon(self, wagon: Wagon, track_id: str) -> Generator:
        """Process single wagon at PopUp workshop."""
        workshop_resource = self.orchestrator.workshop_capacity.get_resource(track_id)
        process_times = self.orchestrator.scenario.process_times
        if not process_times:
            raise ValueError('Process times must be configured')

        # Use PopUp Retrofit Context station service for processing
        station_service = self.orchestrator.popup_retrofit.get_station_service()
        yield from station_service.process_wagon_at_station(
            wagon=wagon,
            workshop_resource=workshop_resource,
            track_id=track_id,
            process_time=process_times.wagon_retrofit_time,
            workshop_capacity_manager=self.orchestrator.workshop_capacity,
            metrics=self.orchestrator.metrics,
        )

        # Signal completion
        yield from self.orchestrator.put_completed_wagon(track_id, wagon)
