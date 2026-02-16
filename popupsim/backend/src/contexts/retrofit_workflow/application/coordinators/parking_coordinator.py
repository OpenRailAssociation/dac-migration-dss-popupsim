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
        """Initialize coordinator."""
        self.config = config
        self.coordination = coordination
        self.batch_counter = 0
        self.track_manager = None
        self.track_selector = None  # Will be set by context

    def _get_tracks_by_type(self, track_type: str) -> list[Any]:
        """Get tracks by type using track_selector if available, otherwise empty list."""
        if self.track_selector:
            return self.track_selector.get_tracks_of_type(track_type)
        return []

    def start(self) -> None:
        """Start coordinator process."""
        logger.info(
            't=%.1f: PARKING → Starting coordinator with strategy=%s', self.config.env.now, self.config.strategy
        )
        self.config.env.process(self._parking_process())

    def _parking_process(self) -> Generator[Any, Any]:
        """Run main parking process continuously."""
        try:
            if self.config.strategy == 'smart_accumulation':
                yield from self._parking_process_smart_accumulation()
            else:
                yield from self._parking_process_opportunistic()
        except GeneratorExit:
            # Gracefully handle simulation shutdown
            pass

    def _parking_process_opportunistic(self) -> Generator[Any, Any]:
        """Opportunistic strategy: grab and go immediately."""
        while True:
            first_wagon = yield self.config.retrofitted_queue.get()
            logger.info('t=%.1f: WAGON[%s] → Retrieved from retrofitted queue', self.config.env.now, first_wagon.id)
            parking_track = self.config.track_selector.select_track_with_capacity('parking')
            logger.info(
                't=%.1f: TRACK[%s] → Selected for parking',
                self.config.env.now,
                parking_track.track_id if parking_track else 'None',
            )
            yield from self._process_wagon_batch(first_wagon, parking_track)

    def _parking_process_smart_accumulation(self) -> Generator[Any, Any]:
        """Smart accumulation strategy: accumulate to threshold, then transport."""
        while True:
            first_wagon = yield self.config.retrofitted_queue.get()
            logger.info(
                't=%.1f: WAGON[%s] → Retrieved from retrofitted queue, accumulating...',
                self.config.env.now,
                first_wagon.id,
            )

            # Accumulate to normal threshold
            wagons = yield from self._accumulate_to_threshold(first_wagon)
            wagon_ids = ','.join(w.id for w in wagons)
            logger.info('t=%.1f: BATCH[%s] → Accumulated %d wagons', self.config.env.now, wagon_ids, len(wagons))

            # Select parking track using track selection service
            parking_track = self.config.track_selector.select_track_with_capacity('parking')
            logger.info(
                't=%.1f: TRACK[%s] → Selected for parking',
                self.config.env.now,
                parking_track.track_id if parking_track else 'None',
            )
            yield from self._process_wagon_batch_with_wagons(wagons, parking_track)

    def _accumulate_to_threshold(self, first_wagon: Wagon) -> Generator[Any, Any, list[Wagon]]:
        """Accumulate wagons until retrofitted track reaches threshold.

        Keeps accumulating as long as retrofitted track fill level is below threshold.
        This prioritizes workshop flow by not immediately grabbing completed wagons.
        """
        wagons = [first_wagon]
        total_length = first_wagon.length
        threshold_length = self.config.normal_threshold * self.config.retrofitted_track_capacity

        # Keep accumulating while under threshold
        while total_length < threshold_length:
            if len(self.config.retrofitted_queue.items) > 0:
                next_wagon: Wagon = yield self.config.retrofitted_queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                # No more wagons available, check if we've reached threshold
                break

        return wagons

    def _calculate_fill_level(self) -> float:
        """Calculate retrofitted track fill level (0.0 to 1.0)."""
        total_length = sum(w.length for w in self.config.retrofitted_queue.items)
        return (
            total_length / self.config.retrofitted_track_capacity if self.config.retrofitted_track_capacity > 0 else 0.0
        )

    def _process_wagon_batch_with_wagons(self, wagons: list[Wagon], parking_track: Any) -> Generator[Any, Any]:
        """Process a batch of wagons (for smart_accumulation strategy)."""
        parking_track_id = parking_track.track_id

        # Form batch that fits parking track capacity
        batch_wagons = self.config.batch_service.form_batch_for_parking_track(
            wagons, parking_track.get_available_capacity()
        )
        if not batch_wagons:
            return

        # Create batch aggregate with rake integration
        batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, parking_track_id)
        yield from self._transport_batch_aggregate(batch_aggregate, parking_track_id)

    def _process_wagon_batch(self, first_wagon: Wagon, parking_track: Any) -> Generator[Any, Any]:
        """Process a batch of wagons."""
        parking_track_id = parking_track.track_id

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
        batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, parking_track_id)
        yield from self._transport_batch_aggregate(batch_aggregate, parking_track_id)

    def _collect_wagons(self, first_wagon: Wagon, parking_track: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in available parking capacity."""
        parking_capacity = parking_track.get_available_capacity()
        wagons = [first_wagon]
        total_length = first_wagon.length

        # Collect additional wagons WITHOUT yielding if queue is empty
        # This prevents race conditions with other coordinators
        while len(self.config.retrofitted_queue.items) > 0:
            next_wagon_length = self.config.retrofitted_queue.items[0].length
            if total_length + next_wagon_length <= parking_capacity:
                next_wagon: Wagon = yield self.config.retrofitted_queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                break

        # Must yield at least once to make this a generator
        if len(wagons) == 1:
            yield self.config.env.timeout(0)

        return wagons

    def _publish_batch_events(self, batch_aggregate: Any, parking_track_id: str) -> None:
        """Publish batch formation events."""
        EventPublisherHelper.publish_batch_events_for_aggregate(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_aggregate,
            parking_track_id,
        )

    def _park_wagons(self, wagons: list[Wagon], parking_track_id: str) -> Generator[Any, Any]:
        """Park wagons in parking area."""
        if self.track_manager:
            parking_track = self.track_manager.get_track(parking_track_id)
            if parking_track:
                # Check if wagons will fit before trying to add
                if parking_track.can_fit_wagons(wagons):
                    yield from parking_track.add_wagons(wagons)
                else:
                    total_length = sum(w.length for w in wagons)
                    available = parking_track.get_available_capacity()
                    wagon_ids = ', '.join(w.id for w in wagons)

                    # Console output for immediate visibility
                    print(f'\n*** WARNING: PARKING CAPACITY EXCEEDED at t={self.config.env.now} ***')
                    print(f'Track: {parking_track_id}')
                    print(f'Wagons: {len(wagons)} ({wagon_ids})')
                    print(f'Required: {total_length:.1f}m | Available: {available:.1f}m')
                    print(
                        f'Track capacity: {parking_track.capacity_meters:.1f}m | '
                        f'Used: {parking_track.get_occupied_capacity():.1f}m'
                    )
                    print('Action: Wagons marked as PARKED but track capacity NOT updated\n')

                    # Log to logger
                    logger.warning(
                        'PARKING_CAPACITY_EXCEEDED: track=%s, wagons=%d, required=%.1fm, available=%.1fm',
                        parking_track_id,
                        len(wagons),
                        total_length,
                        available,
                    )

                    # Publish warning event for tracking
                    if self.config.wagon_event_publisher:
                        for wagon in wagons:
                            EventPublisherHelper.publish_wagon_event(
                                self.config.wagon_event_publisher,
                                self.config.env.now,
                                wagon.id,
                                'PARKING_CAPACITY_WARNING',
                                parking_track_id,
                                'PARKED',
                            )

        for wagon in wagons:
            wagon.park(parking_track_id)
            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher, self.config.env.now, wagon.id, 'PARKED', parking_track_id, 'PARKED'
            )

        yield self.config.env.timeout(0)

    def _return_locomotive(self, loco: Any, parking_track_id: str) -> Generator[Any, Any]:
        """Return locomotive to home track."""
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, parking_track_id, loco.home_track
        )

        return_time = self.config.route_service.get_duration(parking_track_id, 'loco_parking')
        yield self.config.env.timeout(return_time)

    def _transport_to_parking_with_batch(
        self, loco: Any, batch_aggregate: Any, batch_id: str, parking_track_id: str
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area with proper train formation."""
        wagons = batch_aggregate.wagons

        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            parking_track_id,
            len(wagons),
        )

        # Form train and prepare (locomotive coupling + shunting prep)
        route_type = self.config.route_service.get_route_type('retrofitted', parking_track_id)
        train = self.config.train_service.form_train(loco, batch_aggregate, 'retrofitted', parking_track_id, route_type)
        process_times = self.config.scenario.process_times
        prep_time = self.config.train_service.prepare_train(
            train,
            process_times,
            self.config.env.now,
            coupling_event_publisher=self.config.coupling_event_publisher,
        )
        logger.info(
            't=%.1f: LOCO[%s] → TRAIN_PREP at retrofitted (coupling + prep, %.1f min)',
            self.config.env.now,
            loco.id,
            prep_time,
        )
        yield self.config.env.timeout(prep_time)

        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'retrofitted', parking_track_id
        )

        # Transport
        base_transport_time = self.config.route_service.get_duration('retrofitted', parking_track_id)
        yield self.config.env.timeout(base_transport_time)

        # Dissolve train (locomotive decoupling + rake decoupling)
        loco_decouple_time = self.config.train_service.dissolve_train(
            train,
            self.config.env.now,
            coupling_event_publisher=self.config.coupling_event_publisher,
        )
        if loco_decouple_time > 0:
            logger.info(
                't=%.1f: LOCO[%s] → DECOUPLING at %s (%.1f min)',
                self.config.env.now,
                loco.id,
                parking_track_id,
                loco_decouple_time,
            )
        yield self.config.env.timeout(loco_decouple_time)

        rake_decouple_time = self.config.train_service.coupling_service.get_rake_decoupling_time(wagons)
        wagon_ids = ','.join(w.id for w in wagons)
        logger.info(
            't=%.1f: RAKE[%s] → DECOUPLING at %s (%d couplings, %.1f min)',
            self.config.env.now,
            wagon_ids,
            parking_track_id,
            len(wagons) - 1,
            rake_decouple_time,
        )
        yield self.config.env.timeout(rake_decouple_time)

        EventPublisherHelper.publish_batch_arrived(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            parking_track_id,
            len(wagons),
        )

    def _transport_batch_aggregate(self, batch_aggregate: Any, parking_track_id: str) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area."""
        batch_id = batch_aggregate.id
        wagons = batch_aggregate.wagons

        # Publish batch events FIRST (before allocating locomotive)
        self._publish_batch_events(batch_aggregate, parking_track_id)

        # Allocate locomotive
        logger.info('t=%.1f: LOCO → Allocating for parking transport', self.config.env.now)
        loco = yield from self.config.locomotive_manager.allocate(purpose='batch_transport')
        logger.info('t=%.1f: LOCO[%s] → Allocated for parking transport', self.config.env.now, loco.id)
        EventPublisherHelper.publish_loco_allocated(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'batch_transport'
        )

        try:
            # Move locomotive to retrofitted track
            EventPublisherHelper.publish_loco_moving(
                self.config.loco_event_publisher, self.config.env.now, loco.id, loco.home_track, 'retrofitted'
            )
            move_time = self.config.route_service.get_duration(loco.home_track, 'retrofitted')
            yield self.config.env.timeout(move_time)

            # Remove wagons from retrofitted track
            if self.track_manager:
                retrofitted_tracks = self._get_tracks_by_type('retrofitted')
                if retrofitted_tracks:
                    retrofitted_track = retrofitted_tracks[0]
                    # Only remove wagons that are actually on the track
                    wagons_on_track = [w for w in wagons if w in retrofitted_track.wagons]
                    if wagons_on_track:
                        yield from retrofitted_track.remove_wagons(wagons_on_track)

            yield from self._transport_to_parking_with_batch(loco, batch_aggregate, batch_id, parking_track_id)
            yield from self._park_wagons(wagons, parking_track_id)
            yield from self._return_locomotive(loco, parking_track_id)
        finally:
            logger.info('t=%.1f: LOCO[%s] → Releasing', self.config.env.now, loco.id)
            yield from self.config.locomotive_manager.release(loco)
            logger.info('t=%.1f: LOCO[%s] → Released', self.config.env.now, loco.id)
