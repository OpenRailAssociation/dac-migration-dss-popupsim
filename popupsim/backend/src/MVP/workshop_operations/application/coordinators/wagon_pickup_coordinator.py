"""Wagon pickup coordination."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from MVP.analytics.domain.events.simulation_events import (
    WagonDeliveredEvent,
)
from MVP.analytics.domain.value_objects.timestamp import Timestamp
from MVP.workshop_operations.domain.entities.wagon import (
    WagonStatus,
)
from MVP.workshop_operations.infrastructure.routing.transport_job import (
    TransportJob,
    execute_transport_job,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from workshop_operations.domain.entities.wagon import Wagon
    from workshop_operations.domain.protocols.orchestration_context import (
        OrchestrationContext,
    )

logger = logging.getLogger(__name__)


class WagonPickupCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates wagon pickup from collection to retrofit tracks."""

    def __init__(self, orchestrator: OrchestrationContext) -> None:
        self.orchestrator = orchestrator

    def pickup_wagons_to_retrofit(self) -> Generator:
        """Pick up wagons to retrofit."""
        if not self.orchestrator.scenario.process_times:
            msg = "Scenario must have process_times configured"
            raise ValueError(msg)
        if not self.orchestrator.scenario.trains:
            msg = "Scenario must have trains configured"
            raise ValueError(msg)
        if not self.orchestrator.scenario.routes:
            msg = "Scenario must have routes configured"
            raise ValueError(msg)

        logger.info("Starting wagon pickup process")

        while True:
            (
                collection_track_id,
                collection_wagons,
            ) = yield from self._wait_for_wagons_ready()
            tracks = list(self.orchestrator.scenario.tracks or [])
            wagons_to_pickup = self.orchestrator.yard_operations.classification_area.find_wagons_for_retrofit(
                collection_wagons, tracks
            )
            if not wagons_to_pickup:
                yield self.orchestrator.sim.delay(1.0)
                continue

            wagons_by_retrofit = self.orchestrator.yard_operations.classification_area.group_wagons_by_retrofit_track(
                wagons_to_pickup
            )
            yield from self._deliver_to_retrofit_tracks(
                collection_track_id, wagons_by_retrofit
            )
            yield from self._signal_wagons_ready(wagons_by_retrofit)

    def _wait_for_wagons_ready(self) -> Generator[None, None, tuple[str, list[Wagon]]]:
        """Wait for wagons ready on collection track."""
        while True:
            yield self.orchestrator.train_processed_event.wait()

            wagons_by_track = self.orchestrator.wagon_selector.filter_selected_wagons(
                self.orchestrator.wagons
            )
            if wagons_by_track:
                collection_track_id = next(iter(wagons_by_track))
                return (collection_track_id, wagons_by_track[collection_track_id])

    def _deliver_to_retrofit_tracks(
        self, collection_track_id: str, wagons_by_retrofit: dict[str, list[Wagon]]
    ) -> Generator:
        """Deliver wagons to retrofit tracks using transport jobs."""
        for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
            job = TransportJob(
                wagons=retrofit_wagons,
                from_track=collection_track_id,
                to_track=retrofit_track_id,
            )
            yield from execute_transport_job(
                self.orchestrator, job, self.orchestrator.locomotive_service
            )

            # Update wagon status after transport
            for wagon in retrofit_wagons:
                wagon.status = WagonStatus.MOVING

    def _signal_wagons_ready(
        self, wagons_by_retrofit: dict[str, list[Wagon]]
    ) -> Generator:
        """Signal wagons ready for workshop processing."""
        for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
            yield from self._distribute_wagons_to_workshops(
                retrofit_track_id, retrofit_wagons
            )

    def _distribute_wagons_to_workshops(
        self, retrofit_track_id: str, wagons: list[Wagon]
    ) -> Generator:
        """Distribute wagons to workshops based on available capacity."""
        capacity_claims = {w.track: 0 for w in self.orchestrator.workshops}
        remaining = list(wagons)
        batch_num = 1
        current_time = self.orchestrator.sim.current_time()

        while remaining:
            best_workshop = max(
                self.orchestrator.workshops,
                key=lambda w: self.orchestrator.workshop_capacity.get_available_stations(
                    w.track
                )
                - capacity_claims[w.track],
            )

            available = (
                self.orchestrator.workshop_capacity.get_available_stations(
                    best_workshop.track
                )
                - capacity_claims[best_workshop.track]
            )
            if available <= 0:
                best_workshop = self.orchestrator.workshops[0]
                batch = remaining
                remaining = []
            else:
                batch_size = min(available, len(remaining))
                batch = remaining[:batch_size]
                remaining = remaining[batch_size:]
                capacity_claims[best_workshop.track] += batch_size

            wagon_ids = ", ".join([w.id for w in batch])
            logger.info(
                "📦 BATCH %d: [%s] → %s (capacity: %d/%d)",
                batch_num,
                wagon_ids,
                best_workshop.track,
                capacity_claims[best_workshop.track],
                self.orchestrator.workshop_capacity.get_available_stations(
                    best_workshop.track
                ),
            )
            batch_num += 1

            for wagon in batch:
                self.orchestrator.wagon_state.mark_on_retrofit_track(wagon)

                # Record domain event
                event = WagonDeliveredEvent.create(
                    timestamp=Timestamp.from_simulation_time(current_time),
                    wagon_id=wagon.id,
                )
                self.orchestrator.metrics.record_event(event)

                yield from self.orchestrator.put_wagon_for_station(
                    best_workshop.track, retrofit_track_id, wagon
                )
