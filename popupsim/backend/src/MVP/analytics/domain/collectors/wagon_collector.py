"""Wagon metrics collector."""

from dataclasses import dataclass, field

from MVP.analytics.domain.events.base_event import DomainEvent
from MVP.analytics.domain.events.simulation_events import (
    WagonDeliveredEvent,
    WagonRejectedEvent,
    WagonRetrofittedEvent,
)
from MVP.analytics.domain.value_objects.metric_value import (
    MetricValue,
)

from .base import MetricCollector, MetricResult


@dataclass
class WagonCollector(MetricCollector):
    """Collect wagon flow time metrics.

    Focuses on flow time calculation which requires start/end timestamps.
    Wagon counts (delivered/retrofitted/rejected) are derived from wagon queues.
    """

    total_flow_time: float = 0.0
    flow_time_count: int = 0
    wagon_start_times: dict[str, float] = field(default_factory=dict)

    def handled_event_types(self) -> set[type[DomainEvent]]:
        """Return wagon event types."""
        return {WagonDeliveredEvent, WagonRetrofittedEvent, WagonRejectedEvent}

    def record_event(self, event: DomainEvent) -> None:
        """Record wagon domain events."""
        if isinstance(event, WagonDeliveredEvent):
            self.wagon_start_times[event.wagon_id] = event.timestamp.to_minutes()

        elif isinstance(event, WagonRetrofittedEvent):
            start_time = self.wagon_start_times.pop(event.wagon_id, None)
            if start_time is not None:
                flow_time = event.timestamp.to_minutes() - start_time
                self.total_flow_time += flow_time
                self.flow_time_count += 1

        elif isinstance(event, WagonRejectedEvent):
            self.wagon_start_times.pop(event.wagon_id, None)

    def get_results(self) -> list[MetricResult]:
        """Get flow time metrics."""
        avg_flow_time = (
            self.total_flow_time / self.flow_time_count
            if self.flow_time_count > 0
            else 0.0
        )

        return [
            MetricResult(
                "avg_flow_time", MetricValue.duration_minutes(avg_flow_time), "wagon"
            ),
            MetricResult(
                "total_flow_time",
                MetricValue.duration_minutes(self.total_flow_time),
                "wagon",
            ),
        ]

    def reset(self) -> None:
        """Reset collector state."""
        self.total_flow_time = 0.0
        self.flow_time_count = 0
        self.wagon_start_times.clear()
