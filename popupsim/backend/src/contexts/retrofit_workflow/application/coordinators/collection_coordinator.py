"""Collection Coordinator - moves wagons from collection to retrofit track."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import CollectionCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
import simpy

logger = logging.getLogger(__name__)


class CollectionCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates wagon movement from collection to retrofit track.

    Flow:
    1. Wait for wagons on collection track
    2. Form batch (fits retrofit track capacity)
    3. Request locomotive
    4. Transport to retrofit track
    5. Release locomotive
    """

    def __init__(self, config: CollectionCoordinatorConfig, coordination: CoordinationService):
        """Initialize coordinator.

        Args:
            config: Coordinator configuration
            coordination: Coordination service
        """
        self.config = config
        self.coordination = coordination
        self.batch_counter = 0
        self.track_queues: dict[str, Any] = {}  # One queue per collection track
        self.pending_length: dict[str, float] = {}  # Track pending wagon length per track
        self.track_manager = config.track_manager  # Add track manager for capacity management

    def start(self) -> None:
        """Start coordinator processes - one per collection track."""
        # Get all collection tracks
        collection_tracks = self.config.track_selector.get_tracks_of_type('collection')

        if not collection_tracks:
            logger.error('No collection tracks configured')
            return

        # Create one queue per collection track
        for track in collection_tracks:
            self.track_queues[track.track_id] = simpy.Store(self.config.env)
            self.pending_length[track.track_id] = 0.0
            self.config.env.process(self._collection_process(track.track_id))

    def add_wagon(self, wagon: Wagon) -> None:
        """Add wagon to the appropriate track queue.

        Args:
            wagon: Wagon to add to queue
        """
        track_id = wagon.current_track_id
        if track_id in self.track_queues:
            self.track_queues[track_id].put(wagon)
            self.pending_length[track_id] += wagon.length

    def get_pending_length(self, track_id: str) -> float:
        """Get pending wagon length for a track.

        Args:
            track_id: Track ID

        Returns
        -------
            Pending wagon length in meters
        """
        return self.pending_length.get(track_id, 0.0)

    def _collection_process(self, track_id: str) -> Generator[Any, Any]:
        """Run collection process for a specific collection track.

        Args:
            track_id: ID of the collection track to monitor
        """
        queue = self.track_queues[track_id]

        while True:
            # Get next wagon from this track's queue (FIFO guaranteed)
            first_wagon: Wagon = yield queue.get()

            retrofit_tracks = self.config.track_selector.get_tracks_of_type('retrofit')
            retrofit_track = retrofit_tracks[0] if retrofit_tracks else None
            if not retrofit_track:
                logger.error('No retrofit tracks configured')
                continue

            yield from self._process_wagon_batch(first_wagon, retrofit_track, track_id, queue)

    def _process_wagon_batch(
        self, first_wagon: Wagon, retrofit_track: Any, source_track_id: str, queue: Any
    ) -> Generator[Any, Any]:
        """Process a batch of wagons from the same collection track.

        Args:
            first_wagon: First wagon in batch
            retrofit_track: Target retrofit track
            source_track_id: Collection track ID to process from
            queue: Queue for this specific track
        """
        # Collect wagons
        wagons = yield from self._collect_wagons_simple(first_wagon, queue)
        if not wagons:
            return

        # Update pending length
        total_length = sum(w.length for w in wagons)
        self.pending_length[source_track_id] -= total_length

        # Create batch aggregate directly
        batch_aggregate = self.config.batch_service.create_batch_aggregate(wagons, 'retrofit')
        yield from self._transport_batch_aggregate(batch_aggregate, retrofit_track)

    def _collect_wagons_simple(self, first_wagon: Wagon, queue: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons from track queue that fit in available retrofit track capacity.

        CRITICAL: Only form batches that will fit on the retrofit track to prevent deadlock.
        If retrofit track is full, this will block until capacity becomes available.
        """
        retrofit_tracks = self.config.track_selector.get_tracks_of_type('retrofit')
        retrofit_track = retrofit_tracks[0] if retrofit_tracks else None
        if not retrofit_track:
            return [first_wagon]

        # Get CURRENT available capacity on retrofit track
        retrofit_capacity = retrofit_track.get_available_capacity()

        # If first wagon doesn't fit, wait for capacity to be freed
        while first_wagon.length > retrofit_capacity:
            logger.warning(
                't=%s: Retrofit track full (%s: m available, need %s: m). Waiting for capacity...',
                self.config.env.now,
                retrofit_capacity,
                first_wagon.length,
            )
            # Wait a bit and check again (SimPy will handle blocking in add_wagons)
            yield self.config.env.timeout(1)
            retrofit_capacity = retrofit_track.get_available_capacity()

        wagons = [first_wagon]
        total_length = first_wagon.length

        # Collect additional wagons from this track's queue that fit in AVAILABLE capacity
        while len(queue.items) > 0:
            next_wagon = queue.items[0]
            # Check if adding this wagon would exceed available retrofit track capacity
            if total_length + next_wagon.length <= retrofit_capacity:
                wagon: Wagon = yield queue.get()
                wagons.append(wagon)
                total_length += wagon.length
            else:
                # Stop collecting - batch is full based on retrofit track capacity
                logger.info(
                    't=%f: Batch size limited by retrofit capacity: %d wagons %1fm) fits, but %d wagons still waiting',
                    self.config.env.now,
                    len(wagons),
                    total_length,
                    len(queue.items),
                )
                break

        return wagons

    def _transport_batch_aggregate(self, batch_aggregate: Any, retrofit_track: Any) -> Generator[Any, Any]:
        """Transport batch aggregate to retrofit track."""
        batch_id = batch_aggregate.id
        wagons = batch_aggregate.wagons

        # Release capacity from collection track BEFORE transport
        # Only if wagons are actually on the track (check wagon count)
        if self.track_manager and wagons:
            collection_track_id = wagons[0].current_track_id
            if collection_track_id:
                collection_track = self.track_manager.get_track(collection_track_id)
                if collection_track and any(w in collection_track.wagons for w in wagons):
                    yield from collection_track.remove_wagons(wagons)

        # Batch events published AFTER locomotive arrives in _transport_to_retrofit_with_batch
        yield from self._transport_to_retrofit_with_batch(None, batch_aggregate, retrofit_track, batch_id)

    def _publish_batch_events(self, batch_aggregate: Any) -> None:
        """Publish batch formation events."""
        EventPublisherHelper.publish_batch_events_for_aggregate(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_aggregate,
            'retrofit',
        )

    def _deliver_wagons(self, wagons: list[Wagon], retrofit_track: Any) -> Generator[Any, Any]:
        """Deliver wagons to retrofit queue."""
        for wagon in wagons:
            wagon.prepare_for_retrofit()
            self.config.retrofit_queue.put(wagon)

            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher,
                self.config.env.now,
                wagon.id,
                'ON_RETROFIT_TRACK',
                retrofit_track.track_id,
                'WAITING',
            )

        # Yield to make this a generator
        yield self.config.env.timeout(0)

    def _return_locomotive(self, loco: Any) -> Generator[Any, Any]:
        """Return locomotive to home track."""
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'retrofit', loco.home_track
        )

        return_time = self.config.route_service.get_duration('retrofit', 'loco_parking')
        yield self.config.env.timeout(return_time)

        EventPublisherHelper.publish_loco_parking(
            self.config.loco_event_publisher, self.config.env.now, loco.id, loco.home_track
        )

    def _transport_to_retrofit_with_batch(
        self, loco: Any, batch_aggregate: Any, retrofit_track: Any, batch_id: str
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to retrofit track with train formation."""
        wagons = batch_aggregate.wagons

        # CRITICAL: Reserve retrofit track capacity BEFORE allocating locomotive to prevent deadlock
        logger.info(
            't=%.1f: COLLECTION → Reserving retrofit track capacity for %d wagons', self.config.env.now, len(wagons)
        )
        yield from retrofit_track.add_wagons(wagons)
        logger.info('t=%.1f: COLLECTION → Capacity reserved, allocating locomotive', self.config.env.now)

        # Allocate locomotive and move to collection
        loco = yield from self.config.locomotive_manager.allocate(purpose='collection_pickup')

        # Publish movement immediately
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'loco_parking', 'collection'
        )

        move_time = self.config.route_service.get_duration('loco_parking', 'collection')
        yield self.config.env.timeout(move_time)

        # NOW publish batch formation (after locomotive arrives)
        self._publish_batch_events(batch_aggregate)

        # Locomotive allocated for batch transport
        EventPublisherHelper.publish_loco_allocated(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'batch_transport'
        )

        # Get route type for train formation
        route_type = self.config.route_service.get_route_type('collection', 'retrofit')

        # Form train (locomotive + rake)
        train = self.config.train_service.form_train(
            locomotive=loco,
            batch=batch_aggregate,
            origin='collection',
            destination='retrofit',
            route_type=route_type,
        )

        # Prepare train (loco coupling + brake test + inspection for MAINLINE)
        prep_time = self.config.train_service.prepare_train(
            train,
            self.config.scenario.process_times,
            self.config.env.now,
            coupling_event_publisher=self.config.coupling_event_publisher,
        )
        logger.info(
            't=%.1f: LOCO[%s] → TRAIN_PREP at collection (coupling + prep, %.1f min)',
            self.config.env.now,
            loco.id,
            prep_time,
        )
        yield self.config.env.timeout(prep_time)

        EventPublisherHelper.publish_batch_transport_started(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            loco.id,
            'retrofit',
            len(wagons),
        )

        # Depart
        train.depart(self.config.env.now)
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'collection', 'retrofit'
        )

        # Transport
        base_transport_time = self.config.route_service.get_duration('collection', 'retrofit')
        yield self.config.env.timeout(base_transport_time)

        # Arrive and publish batch arrived event
        train.arrive(self.config.env.now)
        EventPublisherHelper.publish_batch_arrived(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_id,
            'retrofit',
            len(wagons),
        )

        # Deliver wagons to retrofit queue IMMEDIATELY (before train dissolution)
        for wagon in wagons:
            wagon.prepare_for_retrofit()
            self.config.retrofit_queue.put(wagon)
            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher,
                self.config.env.now,
                wagon.id,
                'ON_RETROFIT_TRACK',
                retrofit_track.track_id,
                'WAITING',
            )

        # Dissolve train: loco decoupling + rake decoupling
        loco_decouple_time = self.config.train_service.dissolve_train(
            train,
            self.config.env.now,
            coupling_event_publisher=self.config.coupling_event_publisher,
        )
        logger.info(
            't=%.1f: LOCO[%s] → DECOUPLING at retrofit (%.1f min)', self.config.env.now, loco.id, loco_decouple_time
        )
        yield self.config.env.timeout(loco_decouple_time)

        rake_decouple_time = self.config.train_service.coupling_service.get_rake_decoupling_time(wagons)
        wagon_ids = ','.join(w.id for w in wagons)
        logger.info(
            't=%.1f: RAKE[%s] → DECOUPLING at retrofit (%d couplings, %.1f min)',
            self.config.env.now,
            wagon_ids,
            len(wagons) - 1,
            rake_decouple_time,
        )
        yield self.config.env.timeout(rake_decouple_time)

        # Dissolve train (separate loco from rake)
        _, _ = train.dissolve()

        # Return locomotive
        yield from self._return_locomotive(loco)
        yield from self.config.locomotive_manager.release(loco)
