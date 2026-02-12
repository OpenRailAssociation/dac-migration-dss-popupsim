"""Simplified Parking Coordinator - focused on coordination, not service orchestration."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import ParkingCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon

logger = logging.getLogger(__name__)


class SimplifiedParkingCoordinator:
    """Simplified parking coordinator focused purely on coordination logic."""

    def __init__(self, config: ParkingCoordinatorConfig, coordination: CoordinationService):
        """Initialize coordinator with minimal dependencies."""
        self.config = config
        self.coordination = coordination
        self.batch_counter = 0

    def start(self) -> None:
        """Start coordinator process."""
        if self.config.strategy == 'smart_accumulation':
            self.config.env.process(self._smart_accumulation_process())
        else:
            self.config.env.process(self._opportunistic_process())

    def _opportunistic_process(self) -> Generator[Any, Any]:
        """Opportunistic strategy: grab and go immediately."""
        while True:
            first_wagon = yield self.config.retrofitted_queue.get()
            parking_track = self.config.track_selector.select_track_with_capacity('parking')

            if not parking_track:
                logger.error('No parking tracks configured')
                continue

            # Collect wagons that fit
            wagons = yield from self._collect_wagons_for_track(first_wagon, parking_track)

            # Transport batch
            yield from self._transport_batch_to_parking(wagons, parking_track.track_id)

    def _smart_accumulation_process(self) -> Generator[Any, Any]:
        """Smart accumulation: wait for threshold or critical level."""
        while True:
            first_wagon = yield self.config.retrofitted_queue.get()

            # Accumulate to threshold
            wagons = yield from self._accumulate_to_threshold(first_wagon)

            # Check if critical - if not, wait for idle locomotive
            if not self._is_critical_level():
                yield from self._wait_for_idle_locomotive()

            # Find best parking track
            parking_track = self._select_best_parking_track(wagons)
            if not parking_track:
                logger.error('No suitable parking track found')
                continue

            # Transport batch
            yield from self._transport_batch_to_parking(wagons, parking_track.track_id)

    def _collect_wagons_for_track(self, first_wagon: Wagon, track: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in track capacity."""
        wagons = [first_wagon]
        capacity = track.get_available_capacity()
        used_length = first_wagon.length

        while len(self.config.retrofitted_queue.items) > 0:
            next_wagon = self.config.retrofitted_queue.items[0]
            if used_length + next_wagon.length <= capacity:
                wagon = yield self.config.retrofitted_queue.get()
                wagons.append(wagon)
                used_length += wagon.length
            else:
                break

        return wagons

    def _accumulate_to_threshold(self, first_wagon: Wagon) -> Generator[Any, Any, list[Wagon]]:
        """Accumulate wagons to threshold."""
        wagons = [first_wagon]
        threshold = self.config.normal_threshold * self.config.retrofitted_track_capacity
        used_length = first_wagon.length

        while used_length < threshold and len(self.config.retrofitted_queue.items) > 0:
            wagon = yield self.config.retrofitted_queue.get()
            wagons.append(wagon)
            used_length += wagon.length

        return wagons

    def _is_critical_level(self) -> bool:
        """Check if retrofitted track is at critical level."""
        total_length = sum(w.length for w in self.config.retrofitted_queue.items)
        fill_level = total_length / self.config.retrofitted_track_capacity
        return fill_level >= self.config.critical_threshold

    def _wait_for_idle_locomotive(self) -> Generator[Any, Any]:
        """Wait for idle locomotive."""
        while len(self.config.locomotive_manager.pool.items) == 0:
            yield self.config.env.event()

    def _select_best_parking_track(self, wagons: list[Wagon]) -> Any:
        """Select best fitting parking track."""
        batch_length = sum(w.length for w in wagons)
        tracks = self.config.track_selector.get_tracks_of_type('parking')

        suitable = [t for t in tracks if t.get_available_capacity() >= batch_length]
        return min(suitable, key=lambda t: t.get_available_capacity()) if suitable else None

    def _transport_batch_to_parking(self, wagons: list[Wagon], track_id: str) -> Generator[Any, Any]:
        """Transport batch to parking - simplified version."""
        # Create batch
        batch_id = f'PARK-{int(self.config.env.now)}-{self.batch_counter}'
        self.batch_counter += 1

        # Publish batch formed
        EventPublisherHelper.publish_batch_formed(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            [w.id for w in wagons],
            track_id,
            sum(w.length for w in wagons),
        )

        # Get locomotive
        loco = yield from self.config.locomotive_manager.allocate(purpose='parking_transport')

        try:
            # Transport
            EventPublisherHelper.publish_batch_transport_started(
                self.config.batch_event_publisher, self.config.env.now, batch_id, loco.id, track_id, len(wagons)
            )

            transport_time = self.config.route_service.get_duration('retrofitted', track_id)
            yield self.config.env.timeout(transport_time)

            # Park wagons
            for wagon in wagons:
                wagon.park(track_id)
                EventPublisherHelper.publish_wagon_event(
                    self.config.wagon_event_publisher, self.config.env.now, wagon.id, 'PARKED', track_id, 'PARKED'
                )

            # Return locomotive
            return_time = self.config.route_service.get_duration(track_id, 'loco_parking')
            yield self.config.env.timeout(return_time)

        finally:
            yield from self.config.locomotive_manager.release(loco)
