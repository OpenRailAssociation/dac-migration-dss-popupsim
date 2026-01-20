"""Parking Coordinator - moves wagons from retrofitted to parking track."""

from collections.abc import Generator
import logging
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import ParkingCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.event_publisher_helper import EventPublisherHelper
from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted

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
        self.env = config.env
        self.retrofitted_queue = config.retrofitted_queue
        self.locomotive_manager = config.locomotive_manager
        self.track_selector = config.track_selector
        self.batch_service = config.batch_service
        self.route_service = config.route_service
        self.wagon_event_publisher = config.wagon_event_publisher
        self.loco_event_publisher = config.loco_event_publisher
        self.batch_event_publisher = config.batch_event_publisher
        self.coordination = coordination
        self.batch_counter = 0

    def start(self) -> None:
        """Start coordinator process."""
        self.env.process(self._parking_process())

    def _parking_process(self) -> Generator[Any, Any]:
        """Run main parking process continuously."""
        while True:
            first_wagon = yield self.retrofitted_queue.get()
            wagons = yield from self._collect_parking_batch(first_wagon)

            if not wagons:
                continue

            yield from self._process_parking_batch(wagons)

    def _collect_parking_batch(self, first_wagon: Wagon) -> Generator[Any, Any, list[Wagon]]:
        """Collect wagons for parking batch."""
        wagons = [first_wagon]
        max_batch_size = 4  # Fixed batch size - no need for configuration

        while len(wagons) < max_batch_size and len(self.retrofitted_queue.items) > 0:
            next_wagon = yield self.retrofitted_queue.get()
            wagons.append(next_wagon)

        return wagons

    def _process_parking_batch(self, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Process a batch of wagons for parking."""
        # self.coordination.start_operation('parking')  # Method not available

        try:
            parking_track = self.track_selector.select_track_with_capacity('parking_area')
            if not parking_track:
                logger.error('No parking tracks configured')
                return

            batch = self.batch_service.form_batch_for_parking_track(wagons, parking_track.get_available_capacity())
            if not batch:
                return

            batch_id = self._publish_batch_events(batch)
            loco = yield from self.locomotive_manager.allocate(purpose='parking')
            EventPublisherHelper.publish_loco_allocated(self.loco_event_publisher, self.env.now, loco.id)

            try:
                yield from self._transport_to_parking(loco, batch, batch_id)
                yield from self._park_wagons(batch)
                yield from self._return_locomotive(loco)
            finally:
                yield from self.locomotive_manager.release(loco)
        finally:
            pass  # self.coordination.complete_operation('parking')  # Method not available

    def _publish_batch_events(self, batch: list[Wagon]) -> str:
        """Publish batch formation events."""
        self.batch_counter += 1
        batch_id = f'RETROFITTED-PARK-{int(self.env.now)}-{self.batch_counter}'

        if self.batch_event_publisher:
            self.batch_event_publisher(
                BatchFormed(
                    timestamp=self.env.now,
                    event_id=f'batch_formed_{batch_id}',
                    batch_id=batch_id,
                    wagon_ids=[w.id for w in batch],
                    destination='parking_area',
                    total_length=sum(w.length for w in batch),
                )
            )

        return batch_id

    def _transport_to_parking(self, loco: Any, batch: list[Wagon], batch_id: str) -> Generator[Any, Any]:
        """Transport batch to parking area."""
        if self.batch_event_publisher:
            self.batch_event_publisher(
                BatchTransportStarted(
                    timestamp=self.env.now,
                    event_id=f'batch_transport_{batch_id}',
                    batch_id=batch_id,
                    locomotive_id=loco.id,
                    destination='parking_area',
                    wagon_count=len(batch),
                )
            )

        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'retrofitted', 'parking_area'
        )

        transport_time = self.route_service.get_duration('retrofitted', 'parking_area')
        yield self.env.timeout(transport_time)

        if self.batch_event_publisher:
            self.batch_event_publisher(
                BatchArrivedAtDestination(
                    timestamp=self.env.now,
                    event_id=f'batch_arrived_{batch_id}',
                    batch_id=batch_id,
                    destination='parking_area',
                    wagon_count=len(batch),
                )
            )

    def _park_wagons(self, batch: list[Wagon]) -> Generator[Any, Any]:
        """Park wagons in parking area."""
        for wagon in batch:
            wagon.park('parking_area')
            EventPublisherHelper.publish_wagon_event(
                self.wagon_event_publisher, self.env.now, wagon.id, 'PARKED', 'parking_area', 'PARKED'
            )

        # Yield to make this a generator
        yield self.env.timeout(0)

    def _return_locomotive(self, loco: Any) -> Generator[Any, Any]:
        """Return locomotive to home track."""
        EventPublisherHelper.publish_loco_moving(
            self.loco_event_publisher, self.env.now, loco.id, 'parking_area', loco.home_track
        )

        return_time = self.route_service.get_duration('parking_area', 'loco_parking')
        yield self.env.timeout(return_time)
