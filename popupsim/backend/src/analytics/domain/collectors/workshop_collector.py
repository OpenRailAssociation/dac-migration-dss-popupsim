"""Workshop resource utilization metrics collector."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from .base import MetricCollector
from .base import MetricResult


@dataclass
class WorkshopCollector(MetricCollector):
    """Collect workshop resource utilization metrics.

    Tracks station occupancy and worker utilization over time.
    """

    workshop_station_usage: dict[str, dict[str, float]] = field(default_factory=dict)
    workshop_active_time: dict[str, float] = field(default_factory=dict)
    workshop_idle_time: dict[str, float] = field(default_factory=dict)
    workshop_last_event: dict[str, tuple[float, int]] = field(default_factory=dict)

    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record workshop events."""
        if event_type == 'workshop_station_occupied':
            workshop_id = data.get('workshop_id')
            time = data.get('time', 0.0)
            stations_used = data.get('stations_used', 0)

            if workshop_id:
                if workshop_id in self.workshop_last_event:
                    last_time, last_stations = self.workshop_last_event[workshop_id]
                    duration = time - last_time
                    if last_stations > 0:
                        self.workshop_active_time[workshop_id] = (
                            self.workshop_active_time.get(workshop_id, 0.0) + duration
                        )
                    else:
                        self.workshop_idle_time[workshop_id] = self.workshop_idle_time.get(workshop_id, 0.0) + duration

                self.workshop_last_event[workshop_id] = (time, stations_used)

        elif event_type == 'simulation_end':
            end_time = data.get('time', 0.0)
            for workshop_id, (last_time, last_stations) in self.workshop_last_event.items():
                duration = end_time - last_time
                if last_stations > 0:
                    self.workshop_active_time[workshop_id] = self.workshop_active_time.get(workshop_id, 0.0) + duration
                else:
                    self.workshop_idle_time[workshop_id] = self.workshop_idle_time.get(workshop_id, 0.0) + duration

    def get_results(self) -> list[MetricResult]:
        """Get workshop utilization metrics."""
        results: list[MetricResult] = []

        for workshop_id in set(list(self.workshop_active_time.keys()) + list(self.workshop_idle_time.keys())):
            active = self.workshop_active_time.get(workshop_id, 0.0)
            idle = self.workshop_idle_time.get(workshop_id, 0.0)
            total = active + idle

            if total > 0:
                utilization = (active / total) * 100
                results.append(
                    MetricResult(
                        f'{workshop_id}_utilization',
                        round(utilization, 1),
                        '%',
                        'workshop',
                    )
                )
                results.append(
                    MetricResult(
                        f'{workshop_id}_idle_time',
                        round(idle / 60.0, 1),
                        'min',
                        'workshop',
                    )
                )

        return results

    def reset(self) -> None:
        """Reset collector state."""
        self.workshop_station_usage.clear()
        self.workshop_active_time.clear()
        self.workshop_idle_time.clear()
        self.workshop_last_event.clear()
