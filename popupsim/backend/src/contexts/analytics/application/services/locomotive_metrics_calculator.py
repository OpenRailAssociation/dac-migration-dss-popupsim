"""Locomotive metrics calculator."""

from typing import Any


class LocomotiveMetricsCalculator:
    """Calculates locomotive utilization metrics from events."""

    def __init__(self, event_counts: dict[str, int]) -> None:
        self.event_counts = event_counts

    def calculate(self) -> dict[str, Any]:
        """Calculate locomotive statistics."""
        allocated = self.event_counts.get('LocomotiveAllocatedEvent', 0)
        released = self.event_counts.get('LocomotiveReleasedEvent', 0)
        movements = self.event_counts.get('LocomotiveMovementRequestEvent', 0)

        total_loco_events = allocated + released + movements
        utilization_percent = (allocated / max(allocated + released, 1)) * 100 if (allocated + released) > 0 else 0.0

        return {
            'utilization_percent': utilization_percent,
            'allocations': allocated,
            'releases': released,
            'movements': movements,
            'total_operations': total_loco_events,
        }
