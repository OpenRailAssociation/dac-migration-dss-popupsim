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
        """Start coordinator processes - one per retrofitted track."""
        logger.info(
            't=%.1f: PARKING → Starting coordinator with strategy=%s', self.config.env.now, self.config.strategy
        )

        retrofitted_tracks = self._get_tracks_by_type('retrofitted')

        if not retrofitted_tracks:
            logger.error('No retrofitted tracks configured')
            return

        for track in retrofitted_tracks:
            self.config.env.process(self._parking_process(track.track_id))

    def _parking_process(self, retrofitted_track_id: str) -> Generator[Any, Any]:
        """Run main parking process for a specific retrofitted track.

        Args:
            retrofitted_track_id: ID of the retrofitted track to monitor
        """
        try:
            if self.config.strategy == 'smart_accumulation':
                yield from self._parking_process_smart_accumulation(retrofitted_track_id)
            else:
                yield from self._parking_process_opportunistic(retrofitted_track_id)
        except GeneratorExit:
            pass

    def _parking_process_opportunistic(self, retrofitted_track_id: str) -> Generator[Any, Any]:
        """Opportunistic strategy: grab and go immediately.

        Args:
            retrofitted_track_id: ID of the retrofitted track to process
        """
        if not self.track_manager:
            logger.error('Track manager not initialized')
            return

        track = self.track_manager.get_track(retrofitted_track_id)
        if not track:
            logger.error('Track %s not found', retrofitted_track_id)
            return

        queue = track.queue

        while True:
            first_wagon: Wagon = yield queue.get()
            logger.info(
                't=%.1f: WAGON[%s] → Retrieved from retrofitted track %s',
                self.config.env.now,
                first_wagon.id,
                retrofitted_track_id,
            )
            parking_track = self.config.track_selector.select_track_with_capacity('parking')
            logger.info(
                't=%.1f: TRACK[%s] → Selected for parking',
                self.config.env.now,
                parking_track.track_id if parking_track else 'None',
            )
            yield from self._process_wagon_batch(first_wagon, parking_track, retrofitted_track_id, queue)

    def _parking_process_smart_accumulation(self, retrofitted_track_id: str) -> Generator[Any, Any]:
        """Smart accumulation strategy: accumulate to threshold, then transport.

        Args:
            retrofitted_track_id: ID of the retrofitted track to process
        """
        if not self.track_manager:
            logger.error('Track manager not initialized')
            return

        track = self.track_manager.get_track(retrofitted_track_id)
        if not track:
            logger.error('Track %s not found', retrofitted_track_id)
            return

        queue = track.queue
        track_capacity = track.capacity_meters

        while True:
            first_wagon: Wagon = yield queue.get()
            logger.info(
                't=%.1f: WAGON[%s] → Retrieved from retrofitted track %s, accumulating...',
                self.config.env.now,
                first_wagon.id,
                retrofitted_track_id,
            )

            wagons = yield from self._accumulate_to_threshold(first_wagon, queue, track_capacity)
            wagon_ids = ','.join(w.id for w in wagons)
            logger.info(
                't=%.1f: BATCH[%s] → Accumulated %d wagons from %s',
                self.config.env.now,
                wagon_ids,
                len(wagons),
                retrofitted_track_id,
            )

            parking_track = self.config.track_selector.select_track_with_capacity('parking')
            logger.info(
                't=%.1f: TRACK[%s] → Selected for parking',
                self.config.env.now,
                parking_track.track_id if parking_track else 'None',
            )
            yield from self._process_wagon_batch_with_wagons(wagons, parking_track, retrofitted_track_id)

    def _accumulate_to_threshold(
        self, first_wagon: Wagon, queue: Any, track_capacity: float
    ) -> Generator[Any, Any, list[Wagon]]:
        """Accumulate wagons until retrofitted track reaches threshold.

        Args:
            first_wagon: First wagon in batch
            queue: Queue for this specific retrofitted track
            track_capacity: Capacity of this specific retrofitted track
        """
        wagons = [first_wagon]
        total_length = first_wagon.length
        threshold_length = self.config.normal_threshold * track_capacity

        while total_length < threshold_length:
            if len(queue.items) > 0:
                next_wagon: Wagon = yield queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                break

        return wagons

    def _calculate_fill_level(self, retrofitted_track_id: str) -> float:
        """Calculate retrofitted track fill level (0.0 to 1.0).

        Args:
            retrofitted_track_id: ID of the retrofitted track
        """
        if not self.track_manager:
            return 0.0

        track = self.track_manager.get_track(retrofitted_track_id)
        if not track:
            return 0.0

        total_length = sum(w.length for w in track.queue.items)
        return total_length / track.capacity_meters if track.capacity_meters > 0 else 0.0

    def _process_wagon_batch_with_wagons(
        self, wagons: list[Wagon], parking_track: Any, retrofitted_track_id: str
    ) -> Generator[Any, Any]:
        """Process a batch of wagons (for smart_accumulation strategy).

        Args:
            wagons: Wagons to process
            parking_track: Target parking track
            retrofitted_track_id: Source retrofitted track ID
        """
        parking_track_id = parking_track.track_id

        batch_wagons = self.config.batch_service.form_batch_for_parking_track(
            wagons, parking_track.get_available_capacity()
        )
        if not batch_wagons:
            return

        batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, parking_track_id)
        yield from self._transport_batch_aggregate(batch_aggregate, parking_track_id, retrofitted_track_id)

    def _process_wagon_batch(
        self, first_wagon: Wagon, parking_track: Any, retrofitted_track_id: str, queue: Any
    ) -> Generator[Any, Any]:
        """Process a batch of wagons.

        Args:
            first_wagon: First wagon in batch
            parking_track: Target parking track
            retrofitted_track_id: Source retrofitted track ID
            queue: Queue for this specific retrofitted track
        """
        parking_track_id = parking_track.track_id

        wagons = yield from self._collect_wagons(first_wagon, parking_track, queue)
        if not wagons:
            return

        batch_wagons = self.config.batch_service.form_batch_for_parking_track(
            wagons, parking_track.get_available_capacity()
        )
        if not batch_wagons:
            return

        batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, parking_track_id)
        yield from self._transport_batch_aggregate(batch_aggregate, parking_track_id, retrofitted_track_id)

    def _collect_wagons(self, first_wagon: Wagon, parking_track: Any, queue: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in available parking capacity.

        Args:
            first_wagon: First wagon in batch
            parking_track: Target parking track
            queue: Queue for this specific retrofitted track
        """
        parking_capacity = parking_track.get_available_capacity()
        wagons = [first_wagon]
        total_length = first_wagon.length

        while len(queue.items) > 0:
            next_wagon_length = queue.items[0].length
            if total_length + next_wagon_length <= parking_capacity:
                next_wagon: Wagon = yield queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                break

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
        self, loco: Any, batch_aggregate: Any, parking_track_id: str, retrofitted_track_id: str
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area with proper train formation.

        Args:
            loco: Locomotive
            batch_aggregate: Batch to transport
            parking_track_id: Target parking track ID
            retrofitted_track_id: Source retrofitted track ID
        """
        wagons = batch_aggregate.wagons
        batch_id = batch_aggregate.id

        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            parking_track_id,
            len(wagons),
        )

        route_type = self.config.route_service.get_route_type(retrofitted_track_id, parking_track_id)
        train = self.config.train_service.form_train(
            loco, batch_aggregate, retrofitted_track_id, parking_track_id, route_type
        )
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
            self.config.loco_event_publisher, self.config.env.now, loco.id, retrofitted_track_id, parking_track_id
        )

        base_transport_time = self.config.route_service.get_duration(retrofitted_track_id, parking_track_id)
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

    def _transport_batch_aggregate(
        self, batch_aggregate: Any, parking_track_id: str, retrofitted_track_id: str
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area.

        Args:
            batch_aggregate: Batch to transport
            parking_track_id: Target parking track ID
            retrofitted_track_id: Source retrofitted track ID
        """
        wagons = batch_aggregate.wagons

        self._publish_batch_events(batch_aggregate, parking_track_id)

        logger.info('t=%.1f: LOCO → Allocating for parking transport', self.config.env.now)
        loco = yield from self.config.locomotive_manager.allocate(purpose='batch_transport')
        logger.info('t=%.1f: LOCO[%s] → Allocated for parking transport', self.config.env.now, loco.id)
        EventPublisherHelper.publish_loco_allocated(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'batch_transport'
        )

        try:
            EventPublisherHelper.publish_loco_moving(
                self.config.loco_event_publisher, self.config.env.now, loco.id, loco.home_track, retrofitted_track_id
            )
            move_time = self.config.route_service.get_duration(loco.home_track, retrofitted_track_id)
            yield self.config.env.timeout(move_time)

            if self.track_manager:
                retrofitted_track = self.track_manager.get_track(retrofitted_track_id)
                if retrofitted_track:
                    wagons_on_track = [w for w in wagons if w in retrofitted_track.wagons]
                    if wagons_on_track:
                        yield from retrofitted_track.remove_wagons(wagons_on_track)

            yield from self._transport_to_parking_with_batch(
                loco, batch_aggregate, parking_track_id, retrofitted_track_id
            )
            yield from self._park_wagons(wagons, parking_track_id)
            yield from self._return_locomotive(loco, parking_track_id)
        finally:
            logger.info('t=%.1f: LOCO[%s] → Releasing', self.config.env.now, loco.id)
            yield from self.config.locomotive_manager.release(loco)
            logger.info('t=%.1f: LOCO[%s] → Released', self.config.env.now, loco.id)
