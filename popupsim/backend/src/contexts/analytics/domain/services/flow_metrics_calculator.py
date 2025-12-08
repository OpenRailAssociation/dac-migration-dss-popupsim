"""Flow metrics calculator."""

from typing import Any


class FlowMetricsCalculator:
    """Calculates flow-related metrics from events."""

    def __init__(
        self, events: list[tuple[float, Any]], event_counts: dict[str, int]
    ) -> None:
        self.events = events
        self.event_counts = event_counts

    def calculate(self) -> dict[str, Any]:
        """Calculate all flow metrics."""
        trains_arrived = self.event_counts.get("TrainArrivedEvent", 0)
        wagons_arrived = sum(
            len(getattr(e, "wagons", []))
            for _, e in self.events
            if type(e).__name__ == "TrainArrivedEvent"
        )
        retrofits_completed = self.event_counts.get(
            "WagonRetrofitCompletedEvent", 0
        ) + self.event_counts.get("RetrofitCompletedEvent", 0)
        wagons_classified = self.event_counts.get("WagonClassifiedEvent", 0)
        wagons_distributed = self.event_counts.get("WagonDistributedEvent", 0)
        wagons_parked = self.event_counts.get("WagonParkedEvent", 0)
        wagons_rejected = max(0, wagons_arrived - retrofits_completed)

        return {
            "trains_arrived": trains_arrived,
            "wagons_arrived": wagons_arrived,
            "wagons_classified": wagons_classified,
            "wagons_distributed": wagons_distributed,
            "wagons_parked": wagons_parked,
            "retrofits_completed": retrofits_completed,
            "wagons_rejected": wagons_rejected,
            "completion_rate": retrofits_completed / wagons_arrived
            if wagons_arrived > 0
            else 0.0,
        }
