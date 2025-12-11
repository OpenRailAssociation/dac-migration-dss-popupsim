"""Capacity metrics calculator."""

from typing import Any


class CapacityMetricsCalculator:
    """Calculates capacity utilization metrics from events."""

    def __init__(self, events: list[tuple[float, Any]], duration_hours: float) -> None:
        self.events = events
        self.duration_hours = duration_hours

    def calculate(self) -> dict[str, Any]:
        """Calculate capacity statistics."""
        total_wagons = sum(
            len(getattr(e, 'wagons', [])) for _, e in self.events if type(e).__name__ == 'TrainArrivedEvent'
        )

        return {
            'total_wagon_movements': total_wagons,
            'active_operations': len(self.events),
            'events_per_hour': len(self.events) / max(self.duration_hours, 0.1),
        }
