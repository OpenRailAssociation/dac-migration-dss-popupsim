"""Workshop resource utilization metrics collector."""

from dataclasses import dataclass
from dataclasses import field

from ..events.base_event import DomainEvent
from ..events.simulation_events import WorkshopUtilizationChangedEvent
from ..value_objects.metric_value import MetricValue
from .base import MetricCollector
from .base import MetricResult


@dataclass
class WorkshopCollector(MetricCollector):
    """Collect workshop resource utilization metrics.

    Tracks station occupancy and worker utilization over time.
    """

    station_usage: dict[str, dict[str, float]] = field(default_factory=dict)
    active_time: dict[str, float] = field(default_factory=dict)
    idle_time: dict[str, float] = field(default_factory=dict)
    last_event: dict[str, tuple[float, int]] = field(default_factory=dict)

    def handled_event_types(self) -> set[type[DomainEvent]]:
        """Return workshop event types."""
        return {WorkshopUtilizationChangedEvent}

    def record_event(self, event: DomainEvent) -> None:
        """Record workshop domain events."""
        if isinstance(event, WorkshopUtilizationChangedEvent):
            workshop_id = event.workshop_id
            time = event.timestamp.to_minutes()
            stations_used = event.available_stations

            if workshop_id in self.last_event:
                last_time, last_stations = self.last_event[workshop_id]
                duration = time - last_time
                if last_stations > 0:
                    self.active_time[workshop_id] = self.active_time.get(workshop_id, 0.0) + duration
                else:
                    self.idle_time[workshop_id] = self.idle_time.get(workshop_id, 0.0) + duration

            self.last_event[workshop_id] = (time, stations_used)

    def get_results(self) -> list[MetricResult]:
        """Get workshop utilization metrics."""
        results: list[MetricResult] = []

        for workshop_id in set(list(self.active_time.keys()) + list(self.idle_time.keys())):
            active = self.active_time.get(workshop_id, 0.0)
            idle = self.idle_time.get(workshop_id, 0.0)
            total = active + idle

            if total > 0:
                try:
                    utilization = (active / total) * 100
                    results.append(
                        MetricResult(
                            f'{workshop_id}_utilization',
                            MetricValue.percentage(utilization),
                            'workshop',
                        )
                    )
                    results.append(
                        MetricResult(
                            f'{workshop_id}_idle_time',
                            MetricValue.duration_minutes(idle / 60.0),
                            'workshop',
                        )
                    )
                except (ValueError, ZeroDivisionError, TypeError):
                    # Skip invalid metrics but continue processing other workshops
                    continue

        return results

    def reset(self) -> None:
        """Reset collector state."""
        self.station_usage.clear()
        self.active_time.clear()
        self.idle_time.clear()
        self.last_event.clear()
