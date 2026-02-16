"""Application service for collecting simulation events."""

from typing import TYPE_CHECKING

from contexts.retrofit_workflow.domain.events import CouplingEvent
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted

if TYPE_CHECKING:
    from infrastructure.logging import ProcessLogger


class EventCollectionService:
    """Collects simulation events for later analysis."""

    def __init__(self, process_logger: 'ProcessLogger | None' = None) -> None:
        """Initialize event collection service."""
        self.process_logger = process_logger
        self.wagon_events: list[WagonJourneyEvent] = []
        self.locomotive_events: list[LocomotiveMovementEvent] = []
        self.resource_events: list[ResourceStateChangeEvent] = []
        self.batch_events: list[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination] = []
        self.coupling_events: list[CouplingEvent] = []

    def add_wagon_event(self, event: WagonJourneyEvent) -> None:
        """Add wagon journey event."""
        self.wagon_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            self.process_logger.log(f'Wagon {event.wagon_id}: {event.event_type} at {event.location}')

    def add_locomotive_event(self, event: LocomotiveMovementEvent) -> None:
        """Add locomotive movement event."""
        self.locomotive_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            from_loc = event.from_location or ''
            to_loc = event.to_location or ''
            movement = f'{from_loc} → {to_loc}' if from_loc or to_loc else event.purpose or ''
            self.process_logger.log(f'Loco {event.locomotive_id}: {event.event_type} {movement}')

    def add_resource_event(self, event: ResourceStateChangeEvent) -> None:
        """Add resource state change event."""
        self.resource_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            self._log_resource_event(event)

    def add_batch_event(self, event: BatchFormed | BatchTransportStarted | BatchArrivedAtDestination) -> None:
        """Add batch event."""
        self.batch_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            self._log_batch_event(event)

    def add_coupling_event(self, event: CouplingEvent) -> None:
        """Add coupling event."""
        self.coupling_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            self.process_logger.log(
                f'Loco {event.locomotive_id}: {event.event_type} ({event.coupler_type}) '
                f'at {event.location} - {event.wagon_count} wagons'
            )

    def _log_resource_event(self, event: ResourceStateChangeEvent) -> None:
        """Log resource event to process logger."""
        if not self.process_logger:
            return

        msg: str = ''
        if event.resource_type == 'locomotive':
            msg = (
                f'Locomotive {event.resource_id}: {event.change_type}. '
                f'Busy {event.busy_count_before} → {event.busy_count_after}'
            )
        elif event.resource_type == 'track':
            msg = (
                f'Track {event.resource_id}: {event.change_type}. {event.capacity} '
                f'used: {event.used_before} → {event.used_after} = {event.change_amount}'
            )
        elif event.resource_type == 'workshop':
            msg = (
                f'Workshop {event.resource_id}: {event.change_type}. {event.total_bays} '
                f'busy bays: {event.busy_bays_before} → {event.busy_bays_after}'
            )
        self.process_logger.log(msg)

    def _log_batch_event(self, event: BatchFormed | BatchTransportStarted | BatchArrivedAtDestination) -> None:
        """Log batch event to process logger."""
        if not self.process_logger:
            return

        if isinstance(event, BatchFormed):
            self.process_logger.log(
                f'Batch {event.batch_id}: FORMED with {len(event.wagon_ids)} wagons → {event.destination}'
            )
        elif isinstance(event, BatchTransportStarted):
            self.process_logger.log(
                f'Batch {event.batch_id}: TRANSPORT_STARTED by {event.locomotive_id} → {event.destination}'
            )
        elif isinstance(event, BatchArrivedAtDestination):
            self.process_logger.log(
                f'Batch {event.batch_id}: ARRIVED at {event.destination} ({event.wagon_count} wagons)'
            )
