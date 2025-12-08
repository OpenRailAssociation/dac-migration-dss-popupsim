"""Locomotive utilization metrics collector."""

from dataclasses import dataclass

from ..events.base_event import DomainEvent
from ..events.locomotive_events import LocomotiveStatusChangeEvent
from .base import MetricResult, ResourceUtilizationCollector


@dataclass
class LocomotiveCollector(ResourceUtilizationCollector):
    """Collect locomotive utilization metrics.

    Tracks locomotive status changes and calculates time spent in each state.
    """

    category: str = "locomotive"

    def handled_event_types(self) -> set[type[DomainEvent]]:
        """Return locomotive event types."""
        return {LocomotiveStatusChangeEvent}

    def record_event(self, event: DomainEvent) -> None:
        """Record locomotive domain events."""
        if isinstance(event, LocomotiveStatusChangeEvent):
            self._record_state_change(
                event.locomotive_id, event.status, event.timestamp.to_minutes()
            )

    def get_results(self) -> list[MetricResult]:
        """Get locomotive utilization metrics."""
        return self._calculate_utilization()
