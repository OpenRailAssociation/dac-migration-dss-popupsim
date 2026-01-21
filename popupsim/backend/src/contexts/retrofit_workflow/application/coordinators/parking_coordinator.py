"""Parking Coordinator - moves wagons from retrofitted to parking track."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import ParkingCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon

logger = logging.getLogger(__name__)


class ParkingCoordinator:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Coordinates wagon movement from retrofitted to parking track.

    Flow:
    1. Wait for wagons on retrofitted track
    2. Form batch (fits parking track capacity)
    3. Request locomotive
    4. Transport to parking track
    5. Release locomotive
    """

    def __init__(self, config: ParkingCoordinatorConfig, coordination: CoordinationService):
        """Initialize coordinator.

        Args:
            config: Coordinator configuration
            coordination: Coordination service
        """
        self.config = config
        self.coordination = coordination
        self.batch_counter = 0

    def start(self) -> None:
        """Start coordinator process."""
        self.config.env.process(self._parking_process())

    def _parking_process(self) -> Generator[Any, Any]:
        """Run main parking process continuously."""
        if self.config.strategy == 'smart_accumulation':
            yield from self._parking_process_smart_accumulation()
        else:
            yield from self._parking_process_opportunistic()

    def _parking_process_opportunistic(self) -> Generator[Any, Any]:
        """Opportunistic strategy: grab and go immediately."""
        while True:
            first_wagon = yield self.config.retrofitted_queue.get()
            parking_track = self.config.track_selector.select_track_with_capacity('parking_area')

            if not parking_track:
                logger.error('No parking tracks configured')
                continue

            yield from self._process_wagon_batch(first_wagon, parking_track)

    def _parking_process_smart_accumulation(self) -> Generator[Any, Any]:
        """Smart accumulation strategy: accumulate to threshold, wait for idle loco or force at critical level."""
        while True:
            first_wagon = yield self.config.retrofitted_queue.get()

            # Accumulate to normal threshold
            wagons = yield from self._accumulate_to_threshold(first_wagon)

            # Check fill level
            fill_level = self._calculate_fill_level()
            is_critical = fill_level >= self.config.critical_threshold

            if is_critical:
                logger.info(
                    'Critical fill level %.1f%% reached, forcing immediate transport of %d wagons',
                    fill_level * 100,
                    len(wagons),
                )
            else:
                # Wait for idle locomotive
                yield from self._wait_for_idle_locomotive()

            # Select best-fit parking track
            parking_track = self._select_best_fit_parking_track(wagons)
            if not parking_track:
                logger.error('No suitable parking track found for batch of %d wagons', len(wagons))
                continue

            yield from self._process_wagon_batch_with_wagons(wagons, parking_track)

    def _accumulate_to_threshold(self, first_wagon: Wagon) -> Generator[Any, Any, list[Wagon]]:
        """Accumulate wagons to normal threshold (percentage of retrofitted track capacity)."""
        wagons = [first_wagon]
        total_length = first_wagon.length
        threshold_length = self.config.normal_threshold * self.config.retrofitted_track_capacity

        while total_length < threshold_length and len(self.config.retrofitted_queue.items) > 0:
            next_wagon: Wagon = yield self.config.retrofitted_queue.get()
            wagons.append(next_wagon)
            total_length += next_wagon.length

        return wagons

    def _calculate_fill_level(self) -> float:
        """Calculate retrofitted track fill level (0.0 to 1.0)."""
        total_length = sum(w.length for w in self.config.retrofitted_queue.items)
        return (
            total_length / self.config.retrofitted_track_capacity if self.config.retrofitted_track_capacity > 0 else 0.0
        )

    def _wait_for_idle_locomotive(self) -> Generator[Any, Any]:
        """Wait until locomotive pool has idle locomotives."""
        while not self._has_idle_locomotive():
            yield self.config.env.timeout(self.config.idle_check_interval)

    def _has_idle_locomotive(self) -> bool:
        """Check if locomotive pool has idle locomotives."""
        return len(self.config.locomotive_manager.pool.items) > 0

    def _select_best_fit_parking_track(self, wagons: list[Wagon]) -> Any:
        """Select parking track that best fits batch size (smallest available capacity)."""
        batch_length = sum(w.length for w in wagons)

        # Get all parking tracks with sufficient capacity
        suitable_tracks = []
        for track_id in ['parking_area']:  # Extend if multiple parking areas
            track = self.config.track_selector.select_track_with_capacity(track_id)
            if track and track.get_available_capacity() >= batch_length:
                suitable_tracks.append(track)

        if not suitable_tracks:
            return None

        # Select track with smallest available capacity (best fit)
        return min(suitable_tracks, key=lambda t: t.get_available_capacity())

    def _process_wagon_batch_with_wagons(self, wagons: list[Wagon], parking_track: Any) -> Generator[Any, Any]:
        """Process a batch of wagons (for smart_accumulation strategy)."""
        # Form batch that fits parking track capacity
        batch_wagons = self.config.batch_service.form_batch_for_parking_track(
            wagons, parking_track.get_available_capacity()
        )
        if not batch_wagons:
            return

        # Create batch aggregate with rake integration
        try:
            batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, 'parking_area')
            yield from self._transport_batch_aggregate(batch_aggregate)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning('Batch aggregate creation failed: %s, falling back to old method', e)
            batch_id = self._publish_batch_events_old(batch_wagons)
            yield from self._transport_batch_old(batch_wagons, batch_id)

    def _process_wagon_batch(self, first_wagon: Wagon, parking_track: Any) -> Generator[Any, Any]:
        """Process a batch of wagons."""
        # Immediately collect available wagons (no accumulation window)
        wagons = yield from self._collect_wagons(first_wagon, parking_track)
        if not wagons:
            return

        # Form batch that fits parking track capacity
        batch_wagons = self.config.batch_service.form_batch_for_parking_track(
            wagons, parking_track.get_available_capacity()
        )
        if not batch_wagons:
            return

        # Create batch aggregate with rake integration
        try:
            batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, 'parking_area')
            yield from self._transport_batch_aggregate(batch_aggregate)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning('Batch aggregate creation failed: %s, falling back to old method', e)
            batch_id = self._publish_batch_events_old(batch_wagons)
            yield from self._transport_batch_old(batch_wagons, batch_id)

    def _collect_wagons(self, first_wagon: Wagon, parking_track: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in available parking capacity."""
        parking_capacity = parking_track.get_available_capacity()
        wagons = [first_wagon]
        total_length = first_wagon.length

        while len(self.config.retrofitted_queue.items) > 0:
            next_wagon_length = self.config.retrofitted_queue.items[0].length
            if total_length + next_wagon_length <= parking_capacity:
                next_wagon: Wagon = yield self.config.retrofitted_queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                break

        return wagons

    def _publish_batch_events(self, batch_aggregate: Any) -> None:
        """Publish batch formation events."""
        EventPublisherHelper.publish_batch_events_for_aggregate(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_aggregate,
            'parking_area',
        )

    def _transport_to_parking(self, loco: Any, wagons: list[Wagon], batch_id: str) -> Generator[Any, Any]:
        """Transport batch to parking area."""
        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            'parking_area',
            len(wagons),
        )

        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'retrofitted', 'parking_area'
        )

        transport_time = self.config.route_service.get_duration('retrofitted', 'parking_area')
        yield self.config.env.timeout(transport_time)

        EventPublisherHelper.publish_batch_arrived(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            'parking_area',
            len(wagons),
        )

    def _park_wagons(self, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Park wagons in parking area."""
        for wagon in wagons:
            wagon.park('parking_area')
            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher, self.config.env.now, wagon.id, 'PARKED', 'parking_area', 'PARKED'
            )

        yield self.config.env.timeout(0)

    def _return_locomotive(self, loco: Any) -> Generator[Any, Any]:
        """Return locomotive to home track."""
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'parking_area', loco.home_track
        )

        return_time = self.config.route_service.get_duration('parking_area', 'loco_parking')
        yield self.config.env.timeout(return_time)

    def _transport_batch_aggregate(self, batch_aggregate: Any) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area."""
        batch_id = batch_aggregate.id
        wagons = batch_aggregate.wagons

        self._publish_batch_events(batch_aggregate)

        loco = yield from self.config.locomotive_manager.allocate(purpose='batch_transport')
        EventPublisherHelper.publish_loco_allocated(self.config.loco_event_publisher, self.config.env.now, loco.id)

        try:
            yield from self._transport_to_parking_with_batch(loco, batch_aggregate, batch_id)
            yield from self._park_wagons(wagons)
            yield from self._return_locomotive(loco)
        finally:
            yield from self.config.locomotive_manager.release(loco)

    def _transport_to_parking_with_batch(self, loco: Any, batch_aggregate: Any, batch_id: str) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area with coupling time."""
        wagons = batch_aggregate.wagons

        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            'parking_area',
            len(wagons),
        )

        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'retrofitted', 'parking_area'
        )

        # Use batch aggregate to calculate transport time including coupling
        base_transport_time = self.config.route_service.get_duration('retrofitted', 'parking_area')
        process_times = (
            getattr(self.config.scenario, 'process_times', None) if hasattr(self.config, 'scenario') else None
        )
        total_transport_time = batch_aggregate.get_transport_time(base_transport_time, process_times)

        yield self.config.env.timeout(total_transport_time)

        EventPublisherHelper.publish_batch_arrived(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            'parking_area',
            len(wagons),
        )

    def _publish_batch_events_old(self, batch: list[Wagon]) -> str:
        self.batch_counter += 1
        batch_id = f'RETROFITTED-PARK-{int(self.config.env.now)}-{self.batch_counter}'

        EventPublisherHelper.publish_batch_formed(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            [w.id for w in batch],
            'parking_area',
            sum(w.length for w in batch),
        )

        return batch_id

    def _transport_batch_old(self, batch: list[Wagon], batch_id: str) -> Generator[Any, Any]:
        """Transport batch to parking area (old method)."""
        loco = yield from self.config.locomotive_manager.allocate(purpose='batch_transport')
        EventPublisherHelper.publish_loco_allocated(self.config.loco_event_publisher, self.config.env.now, loco.id)

        try:
            yield from self._transport_to_parking(loco, batch, batch_id)
            yield from self._park_wagons(batch)
            yield from self._return_locomotive(loco)
        finally:
            yield from self.config.locomotive_manager.release(loco)
