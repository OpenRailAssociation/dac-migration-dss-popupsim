"""Yard metrics calculator."""

from typing import Any


class YardMetricsCalculator:
    """Calculates yard operations metrics from events."""

    def __init__(self, event_counts: dict[str, int]) -> None:
        self.event_counts = event_counts

    def calculate(self) -> dict[str, Any]:
        """Calculate yard statistics."""
        return {
            'wagons_classified': self.event_counts.get('WagonClassifiedEvent', 0),
            'wagons_distributed': self.event_counts.get('WagonDistributedEvent', 0),
            'wagons_parked': self.event_counts.get('WagonParkedEvent', 0),
        }
