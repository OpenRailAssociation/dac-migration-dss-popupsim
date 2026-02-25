"""Parking Coordinator - moves wagons from retrofitted to parking track."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import ParkingCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
import simpy

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
        """Start coordinator process - single process monitors all retrofitted tracks."""
        logger.info(
            't=%.1f: PARKING → Starting coordinator with strategy=%s', self.config.env.now, self.config.strategy
        )

        retrofitted_tracks = self._get_tracks_by_type('retrofitted')

        if not retrofitted_tracks:
            logger.error('No retrofitted tracks configured')
            return

        logger.info(
            't=%.1f: PARKING → Starting single process monitoring %d retrofitted tracks',
            self.config.env.now,
            len(retrofitted_tracks),
        )
        # Start single process that monitors all retrofitted tracks
        self.config.env.process(self._parking_process_all_tracks(retrofitted_tracks))

    def _parking_process_all_tracks(self, retrofitted_tracks: list[Any]) -> Generator[Any, Any]:
        """Monitor all retrofitted tracks with single process.

        Args:
            retrofitted_tracks: List of all retrofitted tracks to monitor
        """
        try:
            # Create combined queue from all retrofitted tracks using SimPy FilterStore
            combined_queue = simpy.FilterStore(self.config.env)

            # Monitor all track queues and forward to combined queue
            for track in retrofitted_tracks:
                self.config.env.process(self._forward_queue(track, combined_queue))

            # Process wagons from combined queue
            while True:
                item = yield combined_queue.get()
                wagon, retrofitted_track_id = item
                logger.info(
                    't=%.1f: PARKING → Got wagon %s from %s', self.config.env.now, wagon.id, retrofitted_track_id
                )

                # Select parking track
                parking_track = self.config.track_selector.select_track_with_capacity('parking', wagon.length)
                if not parking_track:
                    logger.warning('t=%.1f: All parking tracks full, wagon %s waiting', self.config.env.now, wagon.id)
                    combined_queue.put(item)
                    yield self.config.env.timeout(10.0)
                    continue

                # Collect additional wagons
                wagons = [wagon]
                total_length = wagon.length
                while len(combined_queue.items) > 0:
                    next_item = combined_queue.items[0]
                    next_wagon = next_item[0]
                    if total_length + next_wagon.length <= parking_track.get_available_capacity():
                        retrieved_item = yield combined_queue.get()
                        retrieved_wagon = retrieved_item[0]
                        wagons.append(retrieved_wagon)
                        total_length += retrieved_wagon.length
                    else:
                        break

                # Transport batch
                yield from self._process_wagon_batch_with_wagons(wagons, parking_track, retrofitted_track_id)
        except GeneratorExit:
            pass

    def _forward_queue(self, track: Any, combined_queue: Any) -> Generator[Any, Any]:
        """Forward wagons from track queue to combined queue with track ID."""
        try:
            while True:
                wagon = yield track.queue.get()
                combined_queue.put((wagon, track.track_id))
        except GeneratorExit:
            pass

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
        try:
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
                # Select parking track with required capacity for first wagon
                parking_track = self.config.track_selector.select_track_with_capacity('parking', first_wagon.length)
                if not parking_track:
                    # All parking tracks full - simulation stuck, cannot continue
                    logger.error(
                        't=%.1f: CRITICAL - All parking tracks full, cannot park wagon %s (%.1fm)',
                        self.config.env.now,
                        first_wagon.id,
                        first_wagon.length,
                    )
                    # Put wagon back and stop this coordinator
                    queue.put(first_wagon)
                    return
                logger.info(
                    't=%.1f: TRACK[%s] → Selected for parking (available: %.1fm)',
                    self.config.env.now,
                    parking_track.track_id,
                    parking_track.get_available_capacity(),
                )
                yield from self._process_wagon_batch(first_wagon, parking_track, retrofitted_track_id, queue)
        except GeneratorExit:
            return

    def _parking_process_smart_accumulation(self, retrofitted_track_id: str) -> Generator[Any, Any]:
        """Smart accumulation strategy: accumulate to threshold, then transport.

        Priority logic: If retrofitted track is getting full (>70%), immediately clear it
        to prevent workshop deadlock.

        Args:
            retrofitted_track_id: ID of the retrofitted track to process
        """
        try:
            if not self.track_manager:
                logger.error('Track manager not initialized')
                return

            track = self.track_manager.get_track(retrofitted_track_id)
            if not track:
                logger.error('Track %s not found', retrofitted_track_id)
                return

            queue = track.queue
            high_priority_threshold = 0.7  # 70% full = high priority

            while True:
                logger.info(
                    't=%.1f: PARKING[%s] → Waiting for wagon (queue has %d wagons)',
                    self.config.env.now,
                    retrofitted_track_id,
                    len(queue.items),
                )
                first_wagon: Wagon = yield queue.get()
                logger.info(
                    't=%.1f: PARKING[%s] → Got wagon %s from queue',
                    self.config.env.now,
                    retrofitted_track_id,
                    first_wagon.id,
                )

                # Calculate current fill level
                fill_level = self._calculate_fill_level(retrofitted_track_id)

                if fill_level >= high_priority_threshold:
                    logger.warning(
                        't=%.1f: RETROFITTED[%s] → HIGH PRIORITY (%.1f%% full), clearing immediately',
                        self.config.env.now,
                        retrofitted_track_id,
                        fill_level * 100,
                    )
                else:
                    logger.info(
                        't=%.1f: WAGON[%s] → Retrieved from retrofitted track %s (%.1f%% full)',
                        self.config.env.now,
                        first_wagon.id,
                        retrofitted_track_id,
                        fill_level * 100,
                    )

                # Select parking track with capacity for first wagon
                parking_track = self.config.track_selector.select_track_with_capacity('parking', first_wagon.length)
                if not parking_track:
                    # All parking tracks temporarily full - put wagon back and wait
                    logger.warning(
                        't=%.1f: All parking tracks full, wagon %s waiting - will retry',
                        self.config.env.now,
                        first_wagon.id,
                    )
                    queue.put(first_wagon)
                    # Wait before retrying to avoid busy loop
                    yield self.config.env.timeout(10.0)
                    continue  # Continue loop instead of returning

                # Collect additional wagons that fit in selected parking track
                wagons = yield from self._collect_wagons(first_wagon, parking_track, queue)
                wagon_ids = ','.join(w.id for w in wagons)
                logger.info(
                    't=%.1f: BATCH[%s] → Collected %d wagons for %s (%.1fm available)',
                    self.config.env.now,
                    wagon_ids,
                    len(wagons),
                    parking_track.track_id,
                    parking_track.get_available_capacity(),
                )
                logger.info(
                    't=%.1f: PARKING[%s] → Starting batch transport for %s',
                    self.config.env.now,
                    retrofitted_track_id,
                    wagon_ids,
                )
                yield from self._process_wagon_batch_with_wagons(wagons, parking_track, retrofitted_track_id)
                logger.info(
                    't=%.1f: PARKING[%s] → Completed batch transport for %s',
                    self.config.env.now,
                    retrofitted_track_id,
                    wagon_ids,
                )
        except GeneratorExit:
            return

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

    def _is_end_of_simulation(self) -> bool:
        """Check if simulation is ending (no more wagons will arrive).

        Returns True if:
        - All trains have arrived
        - No wagons in collection, retrofit, or workshop queues
        """
        # Check if all trains arrived by checking if current time is past last train arrival
        # This is a simple heuristic - if no activity for a while, assume end of simulation
        if not self.track_manager:
            return False

        # Check if there are wagons waiting in earlier stages
        collection_tracks = self._get_tracks_by_type('collection')
        retrofit_tracks = self._get_tracks_by_type('retrofit')
        workshop_tracks = self._get_tracks_by_type('workshop')

        # If any earlier stage has wagons, more wagons will come to retrofitted
        return all(len(track.queue.items) <= 0 for track in collection_tracks + retrofit_tracks + workshop_tracks)

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
        try:
            parking_track_id = parking_track.track_id

            batch_wagons = self.config.batch_service.form_batch_for_parking_track(
                wagons, parking_track.get_available_capacity()
            )
            if not batch_wagons:
                return

            batch_aggregate = self.config.batch_service.create_batch_aggregate(batch_wagons, parking_track_id)
            yield from self._transport_batch_aggregate(batch_aggregate, parking_track_id, retrofitted_track_id)
        except GeneratorExit:
            pass

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
        try:
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
        except GeneratorExit:
            pass

    def _collect_wagons(self, first_wagon: Wagon, parking_track: Any, queue: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in available parking capacity.

        Args:
            first_wagon: First wagon in batch
            parking_track: Target parking track
            queue: Queue for this specific retrofitted track
        """
        wagons = [first_wagon]
        total_length = first_wagon.length

        while len(queue.items) > 0:
            next_wagon_length = queue.items[0].length
            # Check if next wagon fits in parking track
            if total_length + next_wagon_length <= parking_track.get_available_capacity():
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
        """Park wagons in parking area - only if capacity available."""
        try:
            if self.track_manager:
                parking_track = self.track_manager.get_track(parking_track_id)
                if parking_track:
                    # Reserve capacity (blocks if full)
                    yield from parking_track.add_wagons(wagons)

            # Only mark as PARKED after successfully adding to track
            for wagon in wagons:
                wagon.park(parking_track_id)
                EventPublisherHelper.publish_wagon_event(
                    self.config.wagon_event_publisher,
                    self.config.env.now,
                    wagon.id,
                    'PARKED',
                    parking_track_id,
                    'PARKED',
                )

            yield self.config.env.timeout(0)
        except GeneratorExit:
            pass

    def _return_locomotive(self, loco: Any, parking_track_id: str) -> Generator[Any, Any]:
        """Return locomotive to home track."""
        try:
            EventPublisherHelper.publish_loco_moving(
                self.config.loco_event_publisher, self.config.env.now, loco.id, parking_track_id, loco.home_track
            )

            return_time = self.config.route_service.get_duration(parking_track_id, loco.home_track)
            yield self.config.env.timeout(return_time)
        except GeneratorExit:
            pass

    def _transport_to_parking_with_batch(  # pylint: disable=too-many-locals
        self, loco: Any, batch_aggregate: Any, parking_track_id: str, retrofitted_track_id: str
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area with proper train formation.

        Args:
            loco: Locomotive
            batch_aggregate: Batch to transport
            parking_track_id: Target parking track ID
            retrofitted_track_id: Source retrofitted track ID
        """
        try:
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
            prep_operations = self.config.train_service.prepare_train(
                train,
                process_times,
                self.config.env.now,
                coupling_event_publisher=self.config.coupling_event_publisher,
            )
            prep_time = prep_operations['total_time'] if isinstance(prep_operations, dict) else prep_operations
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
            dissolve_result = self.config.train_service.dissolve_train(
                train,
                self.config.env.now,
                coupling_event_publisher=self.config.coupling_event_publisher,
            )
            loco_decouple_time = dissolve_result['total_time'] if isinstance(dissolve_result, dict) else dissolve_result
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
        except GeneratorExit:
            pass

    def _transport_batch_aggregate(
        self, batch_aggregate: Any, parking_track_id: str, retrofitted_track_id: str
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to parking area.

        Args:
            batch_aggregate: Batch to transport
            parking_track_id: Target parking track ID
            retrofitted_track_id: Source retrofitted track ID
        """
        try:
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
                    self.config.loco_event_publisher,
                    self.config.env.now,
                    loco.id,
                    loco.home_track,
                    retrofitted_track_id,
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
        except GeneratorExit:
            pass
