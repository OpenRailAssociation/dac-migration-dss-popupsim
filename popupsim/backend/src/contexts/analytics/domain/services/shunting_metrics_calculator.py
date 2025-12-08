"""Shunting metrics calculator."""

from typing import Any


class ShuntingMetricsCalculator:
    """Calculates shunting operations metrics from events."""

    def __init__(
        self, events: list[tuple[float, Any]], event_counts: dict[str, int]
    ) -> None:
        self.events = events
        self.event_counts = event_counts

    def calculate(self) -> dict[str, Any]:
        """Calculate shunting statistics."""
        operations_completed = self.event_counts.get(
            "ShuntingOperationCompletedEvent", 0
        )

        successful_ops = sum(
            1
            for _, e in self.events
            if type(e).__name__ == "ShuntingOperationCompletedEvent"
            and getattr(e, "success", True)
        )

        return {
            "total_operations": operations_completed,
            "successful_operations": successful_ops,
            "success_rate": successful_ops / max(operations_completed, 1) * 100,
        }
