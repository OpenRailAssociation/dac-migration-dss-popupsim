"""Collection Coordinator - moves wagons from collection to retrofit track."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import CollectionCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.services.locomotive_dispatcher import TaskRequest
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.wagon import WagonStatus
from contexts.retrofit_workflow.domain.value_objects.task_priority import TaskType

logger = logging.getLogger(__name__)


class CollectionCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates wagon movement from collection to retrofit track.

    Flow:
    1. Wait for wagons on collection track
    2. Form batch (fits retrofit track capacity)
    3. Request locomotive (via dispatcher if configured, else direct FIFO)
    4. Transport to retrofit track
    5. Release locomotive
    """

    def __init__(self, config: CollectionCoordinatorConfig):
        """Initialize coordinator.

        Args:
            config: Coordinator configuration
        """
        self.config = config
        self.batch_counter = 0
        self.track_manager = config.track_manager
        self.locomotive_dispatcher = None  # Set by context if task_priorities configured

    def start(self) -> None:
        """Start coordinator processes - one per collection track."""
        collection_tracks = self.config.track_selector.get_tracks_of_type('collection')

        if not collection_tracks:
            logger.error('No collection tracks configured')
            return

        for track in collection_tracks:
            self.config.env.process(self._collection_process(track.track_id))

    def add_wagon(self, wagon: Wagon) -> None:
        """Add wagon to the appropriate track queue.

        Args:
            wagon: Wagon to add to queue
        """
        track_id = wagon.current_track_id
        if self.track_manager:
            track = self.track_manager.get_track(track_id)
            if track:
                track.queue.put(wagon)

    def get_pending_length(self, track_id: str) -> float:
        """Get pending wagon length for a track.

        Args:
            track_id: Track ID

        Returns
        -------
            Pending wagon length in meters
        """
        if self.track_manager:
            track = self.track_manager.get_track(track_id)
            if track:
                return sum(w.length for w in track.queue.items)
        return 0.0

    def _collection_process(self, track_id: str) -> Generator[Any, Any]:
        """Run collection process for a specific collection track.

        Args:
            track_id: ID of the collection track to monitor
        """
        if not self.track_manager:
            logger.error('Track manager not initialized')
            return

        track = self.track_manager.get_track(track_id)
        if not track:
            logger.error('Track %s not found', track_id)
            return

        queue = track.queue

        while True:
            first_wagon: Wagon = yield queue.get()

            # Select best retrofit track using configured strategy (least_occupied, round_robin, etc.)
            # Strategy will pick track with most available capacity, but we don't pre-filter by required capacity
            # SimPy's Container.put() in add_wagons() will handle blocking if selected track is full
            retrofit_track = self.config.track_selector.select_track_with_capacity('retrofit', 0.0)
            if not retrofit_track:
                logger.error('No retrofit tracks configured')
                continue

            yield from self._process_wagon_batch(first_wagon, retrofit_track, queue)

    def _process_wagon_batch(self, first_wagon: Wagon, retrofit_track: Any, queue: Any) -> Generator[Any, Any]:
        """Process a batch of wagons from the same collection track.

        Args:
            first_wagon: First wagon in batch
            retrofit_track: Target retrofit track
            queue: Queue for this specific track
        """
        wagons = yield from self._collect_wagons_simple(first_wagon, queue, retrofit_track)
        if not wagons:
            return

        batch_aggregate = self.config.batch_service.create_batch_aggregate(wagons, 'retrofit')
        yield from self._transport_batch_aggregate(batch_aggregate, retrofit_track, queue)

    def _collect_wagons_simple(
        self, first_wagon: Wagon, queue: Any, retrofit_track: Any
    ) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons from track queue that fit in available retrofit track capacity.

        Args:
            first_wagon: First wagon to collect
            queue: Collection track queue
            retrofit_track: Selected retrofit track (already chosen by strategy)
        """
        # Get CURRENT available capacity on the selected retrofit track
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
                    't=%.1f: Batch size limited by retrofit capacity: %d wagons (%.1fm) fits, %d waiting',
                    self.config.env.now,
                    len(wagons),
                    total_length,
                    len(queue.items),
                )
                break

        return wagons

    def _transport_batch_aggregate(
        self, batch_aggregate: Any, retrofit_track: Any, collection_queue: Any = None
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to retrofit track."""
        batch_id = batch_aggregate.id
        # Collection capacity is released inside _transport_to_retrofit_with_batch, AFTER
        # the loco is allocated and the batch is re-sized to the chosen buffer — and only
        # for the wagons that actually travel. Releasing here (before resize) would leave
        # trimmed-off wagons with freed capacity but still on the collection track.
        yield from self._transport_to_retrofit_with_batch(
            None, batch_aggregate, retrofit_track, batch_id, collection_queue
        )

    def _publish_batch_events(self, batch_aggregate: Any) -> None:
        """Publish batch formation events."""
        EventPublisherHelper.publish_batch_events_for_aggregate(
            self.config.batch_event_publisher,
            self.config.env.now,
            batch_aggregate,
            'retrofit',
        )

    def _deliver_wagons(self, wagons: list[Wagon], retrofit_track: Any) -> Generator[Any, Any]:
        """Deliver wagons to retrofit track queue."""
        for wagon in wagons:
            wagon.prepare_for_retrofit()
            retrofit_track.queue.put(wagon)

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

    def _return_locomotive(self, loco: Any, from_track_id: str) -> Generator[Any, Any]:
        """Return locomotive to home track.

        Args:
            loco: Locomotive to return
            from_track_id: Track ID where locomotive currently is
        """
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, from_track_id, loco.home_track
        )

        return_time = self.config.route_service.get_duration(from_track_id, loco.home_track)
        yield self.config.env.timeout(return_time)

        EventPublisherHelper.publish_loco_parking(
            self.config.loco_event_publisher, self.config.env.now, loco.id, loco.home_track
        )

    def _allocate_locomotive(self, wagons: list[Wagon]) -> Generator[Any, Any, Any]:
        """Allocate a locomotive via dispatcher or direct FIFO.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons that need transport (for task metadata).

        Returns
        -------
        Locomotive
            Allocated locomotive.
        """
        if self.locomotive_dispatcher:
            event = self.config.env.event()
            task = TaskRequest(
                task_type=TaskType.COLLECTION_TO_RETROFIT,
                wagons=wagons,
                source_track_id=wagons[0].current_track_id if wagons else '',
                callback=event,
                submitted_at=self.config.env.now,
            )
            self.locomotive_dispatcher.submit_task(task)
            loco = yield event
            return loco

        loco = yield from self.config.locomotive_manager.allocate(purpose='collection_pickup')
        return loco

    def _resize_batch_to_buffer(
        self, retrofit_track: Any, wagons: list[Wagon], collection_queue: Any
    ) -> tuple[Any, list[Wagon]]:
        """Re-select the emptiest retrofit buffer and trim the batch to fit it now.

        Returns the (possibly re-selected) retrofit track and the wagons that fit. Overflow
        wagons are returned to the collection queue ONLY if still CLASSIFIED; wagons already
        advanced in the pipeline are weeded out (never re-introduced). Overflow wagons keep
        their collection-track capacity (the caller releases capacity only for kept wagons).
        """
        candidate = self.config.track_selector.select_track_with_capacity('retrofit', 0.0)
        if candidate is not None:
            retrofit_track = candidate

        available = retrofit_track.get_available_capacity()
        kept: list[Wagon] = []
        overflow: list[Wagon] = []
        used = 0.0
        for wagon in wagons:
            if used + wagon.length <= available:
                kept.append(wagon)
                used += wagon.length
            else:
                overflow.append(wagon)

        weeded = 0
        for wagon in overflow:
            if wagon.status != WagonStatus.CLASSIFIED:
                weeded += 1
                continue
            target_queue = collection_queue
            if target_queue is None and self.track_manager and wagon.current_track_id:
                ct = self.track_manager.get_track(wagon.current_track_id)
                target_queue = ct.queue if ct else None
            if target_queue is not None:
                target_queue.put(wagon)

        if overflow:
            logger.info(
                't=%.1f: COLLECTION → Trimmed to buffer %s: %d kept, %d overflow (%d weeded out)',
                self.config.env.now,
                retrofit_track.track_id,
                len(kept),
                len(overflow),
                weeded,
            )
        return retrofit_track, kept

    def _release_locomotive_no_op(self, loco: Any) -> Generator[Any, Any]:
        """Release a locomotive that was allocated but has no work to do."""
        purpose = 'dispatcher' if self.locomotive_dispatcher else 'collection_pickup'
        yield from self.config.locomotive_manager.release(loco, purpose=purpose)

    def _transport_to_retrofit_with_batch(  # noqa: PLR0915  # pylint: disable=too-many-locals,too-many-statements
        self, loco: Any, batch_aggregate: Any, retrofit_track: Any, batch_id: str, collection_queue: Any = None
    ) -> Generator[Any, Any]:
        """Transport batch aggregate to retrofit track with train formation."""
        wagons = batch_aggregate.wagons

        # Allocate the locomotive FIRST. Reserving retrofit-buffer capacity before we
        # hold a loco (the old order) deadlocks: a batch that fills the buffer can then
        # never win the loco it needs to move that very reservation. With the dispatcher,
        # this is also where the priority/hold_until gate is evaluated.
        logger.info(
            't=%.1f: COLLECTION → Requesting locomotive for %d wagons', self.config.env.now, len(wagons)
        )
        loco = yield from self._allocate_locomotive(wagons)

        # Loco in hand. Re-select the emptiest retrofit buffer and trim the batch to what
        # fits it RIGHT NOW, so the reservation below cannot block while holding the loco
        # (hold-and-wait deadlock). With multiple buffers the track chosen at collection
        # time can be stale. Overflow wagons are returned to the collection queue — but
        # ONLY if still CLASSIFIED (untouched): a wagon already advanced in the pipeline
        # must never be re-introduced (the model does not support re-adding an in-process
        # wagon), so such wagons are weeded out.
        original_count = len(wagons)
        retrofit_track, wagons = self._resize_batch_to_buffer(retrofit_track, wagons, collection_queue)
        if not wagons:
            logger.info(
                't=%.1f: COLLECTION → No retrofit buffer has room; releasing loco', self.config.env.now
            )
            yield from self._release_locomotive_no_op(loco)
            return
        # If the batch was trimmed, rebuild the aggregate so train formation and all
        # downstream events use exactly the wagons that travel.
        if len(wagons) != original_count:
            batch_aggregate = self.config.batch_service.create_batch_aggregate(wagons, 'retrofit')
            batch_id = batch_aggregate.id

        # Release collection capacity for exactly the wagons making this trip (remove_wagons
        # is a container.get and never blocks). Overflow wagons kept their reservation.
        if self.track_manager:
            ct = self.track_manager.get_track(wagons[0].current_track_id)
            if ct:
                on_track = [w for w in wagons if w in ct.wagons]
                if on_track:
                    yield from ct.remove_wagons(on_track)

        # Reserve retrofit buffer capacity (fits by construction; will not block).
        logger.info(
            't=%.1f: COLLECTION → Reserving retrofit buffer %s for %d wagons',
            self.config.env.now,
            retrofit_track.track_id,
            len(wagons),
        )
        yield from retrofit_track.add_wagons(wagons)

        # Get collection track ID from first wagon
        collection_track_id = wagons[0].current_track_id

        # Publish movement immediately
        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, loco.home_track, collection_track_id
        )

        move_time = self.config.route_service.get_duration(loco.home_track, collection_track_id)
        yield self.config.env.timeout(move_time)

        # NOW publish batch formation (after locomotive arrives)
        self._publish_batch_events(batch_aggregate)

        # Locomotive allocated for batch transport
        EventPublisherHelper.publish_loco_allocated(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'batch_transport'
        )

        # Get route type for train formation
        route_type = self.config.route_service.get_route_type(collection_track_id, retrofit_track.track_id)

        # Form train (locomotive + rake)
        train = self.config.train_service.form_train(
            locomotive=loco,
            batch=batch_aggregate,
            origin=collection_track_id,
            destination=retrofit_track.track_id,
            route_type=route_type,
        )

        # Prepare train (loco coupling + brake test + inspection for MAINLINE)
        prep_start_time = self.config.env.now
        prep_operations = self.config.train_service.prepare_train(
            train,
            self.config.scenario.process_times,
            prep_start_time,
            coupling_event_publisher=self.config.coupling_event_publisher,
        )
        prep_time = prep_operations['total_time'] if isinstance(prep_operations, dict) else prep_operations

        # Publish RAKE_COUPLING_STARTED for wagons if rake coupling happens
        if isinstance(prep_operations, dict) and prep_operations.get('rake_coupling'):
            rake_op = prep_operations['rake_coupling']
            for wagon in wagons:
                EventPublisherHelper.publish_wagon_event(
                    self.config.wagon_event_publisher,
                    prep_start_time,
                    wagon.id,
                    'RAKE_COUPLING_STARTED',
                    collection_track_id,
                    'COUPLING',
                    coupler_type=rake_op.get('coupler_type', 'SCREW'),
                )

        logger.info(
            't=%.1f: LOCO[%s] → TRAIN_PREP at collection (coupling + prep, %.1f min)',
            self.config.env.now,
            loco.id,
            prep_time,
        )

        # Wait for rake coupling duration only
        if isinstance(prep_operations, dict) and prep_operations.get('rake_coupling'):
            rake_coupling_time = prep_operations['rake_coupling'].get('duration', 0)
            if rake_coupling_time > 0:
                yield self.config.env.timeout(rake_coupling_time)
                # Publish RAKE_COUPLING_COMPLETED after rake coupling time
                rake_op = prep_operations['rake_coupling']
                for wagon in wagons:
                    EventPublisherHelper.publish_wagon_event(
                        self.config.wagon_event_publisher,
                        self.config.env.now,
                        wagon.id,
                        'RAKE_COUPLING_COMPLETED',
                        collection_track_id,
                        'WAITING',
                        coupler_type=rake_op.get('coupler_type', 'SCREW'),
                    )
                # Wait for remaining prep time (loco coupling + brake test + inspection)
                remaining_time = prep_time - rake_coupling_time
                if remaining_time > 0:
                    yield self.config.env.timeout(remaining_time)
            else:
                # No rake coupling, just wait full prep time
                yield self.config.env.timeout(prep_time)
        else:
            # No rake coupling info, wait full prep time
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
            self.config.loco_event_publisher, self.config.env.now, loco.id, collection_track_id, retrofit_track.track_id
        )

        # Get route path for MOVING state visualization
        route_path = self.config.route_service.get_route_path(collection_track_id, retrofit_track.track_id)

        # Publish MOVING state for all wagons
        for wagon in wagons:
            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher,
                self.config.env.now,
                wagon.id,
                'MOVING',
                collection_track_id,
                'MOVING',
                route_path=route_path,
            )

        # Transport
        base_transport_time = self.config.route_service.get_duration(collection_track_id, retrofit_track.track_id)
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

        # Deliver wagons to retrofit track queue IMMEDIATELY (before train dissolution)
        for wagon in wagons:
            wagon.prepare_for_retrofit()
            retrofit_track.queue.put(wagon)
            EventPublisherHelper.publish_wagon_event(
                self.config.wagon_event_publisher,
                self.config.env.now,
                wagon.id,
                'ON_RETROFIT_TRACK',
                retrofit_track.track_id,
                'WAITING',
            )

        # Dissolve train: loco decoupling + rake decoupling
        dissolve_result = self.config.train_service.dissolve_train(
            train,
            self.config.env.now,
            coupling_event_publisher=self.config.coupling_event_publisher,
        )
        loco_decouple_time = dissolve_result['total_time'] if isinstance(dissolve_result, dict) else dissolve_result
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
        yield from self._return_locomotive(loco, retrofit_track.track_id)
        yield from self.config.locomotive_manager.release(loco)
