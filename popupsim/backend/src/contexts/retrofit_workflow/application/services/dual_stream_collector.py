"""Dual-stream event collector for clean separation of concerns."""

from typing import TYPE_CHECKING

from shared.domain.events.dual_stream_events import LocationChangeEvent
from shared.domain.events.dual_stream_events import ProcessEvent
from shared.domain.events.dual_stream_events import StateChangeEvent

if TYPE_CHECKING:
    from infrastructure.logging import ProcessLogger


class DualStreamEventCollector:
    """Collects events in two separate streams: state and location."""

    def __init__(self, process_logger: 'ProcessLogger | None' = None) -> None:
        """Initialize dual-stream collector."""
        self.process_logger = process_logger
        self.state_events: list[StateChangeEvent] = []
        self.location_events: list[LocationChangeEvent] = []
        self.process_events: list[ProcessEvent] = []

    def record_state_change(self, event: StateChangeEvent) -> None:
        """Record state change event."""
        self.state_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            self.process_logger.log(
                f'{event.resource_type.capitalize()} {event.resource_id}: STATE={event.state.value}'
            )

    def record_location_change(self, event: LocationChangeEvent) -> None:
        """Record location change event."""
        self.location_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            prev = f' (from {event.previous_location})' if event.previous_location else ''
            self.process_logger.log(
                f'{event.resource_type.capitalize()} {event.resource_id}: LOCATION={event.location}{prev}'
            )

    def record_process_event(self, event: ProcessEvent) -> None:
        """Record process event."""
        self.process_events.append(event)
        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            process_info = (
                f'{event.resource_type.capitalize()} {event.resource_id}: '
                f'PROCESS={event.process_state.value} at {event.location}'
            )
            self.process_logger.log(process_info)
