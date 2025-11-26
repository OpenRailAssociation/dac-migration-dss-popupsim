"""Wagon metrics collector."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from .base import MetricCollector
from .base import MetricResult
from ..events.base_event import DomainEvent
from ..events.simulation_events import WagonDeliveredEvent, WagonRetrofittedEvent, WagonRejectedEvent
from ..value_objects.metric_value import MetricValue


@dataclass
class WagonCollector(MetricCollector):
    """Collect wagon metrics.

    Tracks wagon delivery, retrofit completion, and processing times.
    """

    wagons_delivered: int = 0
    wagons_retrofitted: int = 0
    wagons_rejected: int = 0
    total_flow_time: float = 0.0
    wagon_start_times: dict[str, float] = field(default_factory=dict)

    def record_event(self, event: DomainEvent) -> None:
        """Record wagon domain events."""
        if isinstance(event, WagonDeliveredEvent):
            self.wagons_delivered += 1
            self.wagon_start_times[event.wagon_id] = event.timestamp.to_minutes()

        elif isinstance(event, WagonRetrofittedEvent):
            self.wagons_retrofitted += 1
            if event.wagon_id in self.wagon_start_times:
                flow_time = event.timestamp.to_minutes() - self.wagon_start_times[event.wagon_id]
                self.total_flow_time += flow_time
                
        elif isinstance(event, WagonRejectedEvent):
            self.wagons_rejected += 1

    def get_results(self) -> list[MetricResult]:
        """Get wagon metrics."""
        avg_flow_time = self.total_flow_time / self.wagons_retrofitted if self.wagons_retrofitted > 0 else 0.0

        return [
            MetricResult('wagons_delivered', MetricValue.count(self.wagons_delivered), 'wagon'),
            MetricResult('wagons_retrofitted', MetricValue.count(self.wagons_retrofitted), 'wagon'),
            MetricResult('wagons_rejected', MetricValue.count(self.wagons_rejected), 'wagon'),
            MetricResult('avg_flow_time', MetricValue.duration_minutes(avg_flow_time), 'wagon'),
        ]

    def reset(self) -> None:
        """Reset collector state."""
        self.wagons_delivered = 0
        self.wagons_retrofitted = 0
        self.wagons_rejected = 0
        self.total_flow_time = 0.0
        self.wagon_start_times.clear()
