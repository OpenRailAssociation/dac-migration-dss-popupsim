"""Collection Coordinator - moves wagons from collection to retrofit track."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import CollectionCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted

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

    def start(self) -> None:
        """Start coordinator process."""
        self.config.env.process(self._collection_process())

    def _collection_process(self) -> Generator[Any, Any]:
        """Run main collection process continuously."""
        while True:
            first_wagon: Wagon = yield self.config.collection_queue.get()
            retrofit_track = self.config.track_selector.select_track_with_capacity('retrofit')

            if not retrofit_track:
                logger.error('No retrofit tracks configured')
                continue

            yield from self._process_wagon_batch(first_wagon, retrofit_track)

    def _process_wagon_batch(self, first_wagon: Wagon, retrofit_track: Any) -> Generator[Any, Any]:
        """Process a batch of wagons."""
        # Wait for batch formation window (1 minute for locomotive to arrive)
        yield self.config.env.timeout(1)

        wagons = yield from self._collect_wagons(first_wagon, retrofit_track)
        if not wagons:
            return

        batch = self.config.batch_service.form_batch_for_retrofit_track(wagons, retrofit_track.get_available_capacity())
        if not batch:
            return

        yield from self._transport_batch(batch, retrofit_track)

    def _collect_wagons(self, first_wagon: Wagon, retrofit_track: Any) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons that fit in available capacity."""
        retrofit_capacity = retrofit_track.get_available_capacity()
        wagons = [first_wagon]
        total_length = first_wagon.length

        while len(self.config.collection_queue.items) > 0:
            next_wagon_length = self.config.collection_queue.items[0].length
            if total_length + next_wagon_length <= retrofit_capacity:
                next_wagon: Wagon = yield self.config.collection_queue.get()
                wagons.append(next_wagon)
                total_length += next_wagon.length
            else:
                break

        return wagons

    def _transport_batch(self, batch: list[Wagon], retrofit_track: Any) -> Generator[Any, Any]:
        """Transport batch to retrofit track."""
        batch_id = self._publish_batch_events(batch)

        loco = yield from self.config.locomotive_manager.allocate(purpose='collection_to_retrofit')
        EventPublisherHelper.publish_loco_allocated(self.config.loco_event_publisher, self.config.env.now, loco.id)

        try:
            yield from self._transport_to_retrofit(loco, batch, retrofit_track, batch_id)
            yield from self._deliver_wagons(batch, retrofit_track)
            yield from self._return_locomotive(loco)
        finally:
            yield from self.config.locomotive_manager.release(loco)

    def _publish_batch_events(self, batch: list[Wagon]) -> str:
        """Publish batch formation events."""
        self.batch_counter += 1
        batch_id = f'COL-RET-{int(self.config.env.now)}-{self.batch_counter}'

        if self.config.batch_event_publisher:
            self.config.batch_event_publisher(
                BatchFormed(
                    timestamp=self.config.env.now,
                    event_id=f'batch_formed_{batch_id}',
                    batch_id=batch_id,
                    wagon_ids=[w.id for w in batch],
                    destination='retrofit',
                    total_length=sum(w.length for w in batch),
                )
            )

        return batch_id

    def _transport_to_retrofit(
        self, loco: Any, batch: list[Wagon], retrofit_track: Any, batch_id: str
    ) -> Generator[Any, Any]:
        """Transport batch to retrofit track."""
        if self.config.batch_event_publisher:
            self.config.batch_event_publisher(
                BatchTransportStarted(
                    timestamp=self.config.env.now,
                    event_id=f'batch_transport_{batch_id}',
                    batch_id=batch_id,
                    locomotive_id=loco.id,
                    destination='retrofit',
                    wagon_count=len(batch),
                )
            )

        EventPublisherHelper.publish_loco_moving(
            self.config.loco_event_publisher, self.config.env.now, loco.id, 'collection', 'retrofit'
        )

        yield from retrofit_track.add_wagons(batch)
        transport_time = self.config.route_service.get_duration('collection', 'retrofit')
        yield self.config.env.timeout(transport_time)

        if self.config.batch_event_publisher:
            self.config.batch_event_publisher(
                BatchArrivedAtDestination(
                    timestamp=self.config.env.now,
                    event_id=f'batch_arrived_{batch_id}',
                    batch_id=batch_id,
                    destination='retrofit',
                    wagon_count=len(batch),
                )
            )

    def _deliver_wagons(self, batch: list[Wagon], retrofit_track: Any) -> Generator[Any, Any]:
        """Deliver wagons to retrofit queue."""
        for wagon in batch:
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
