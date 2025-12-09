"""Unified metrics calculation service."""

from collections import defaultdict
from typing import Any


class MetricsCalculationService:
    """Calculates all metrics from events in one pass."""

    def __init__(
        self,
        events: list[tuple[float, Any]],
        event_counts: dict[str, int],
        duration_hours: float,
        current_state: dict[str, Any] | None = None,
    ) -> None:
        self.events = events
        self.event_counts = event_counts
        self.duration_hours = duration_hours
        self.current_state = current_state or {}

    def calculate_all(self) -> dict[str, Any]:
        """Calculate all metrics in one pass."""
        return {
            **self._calculate_flow(),
            "throughput_rate_per_hour": self._calculate_throughput(),
            "workshop_statistics": self._calculate_workshop(),
            "locomotive_statistics": self._calculate_locomotive(),
            "shunting_statistics": self._calculate_shunting(),
            "yard_statistics": self._calculate_yard(),
            "capacity_statistics": self._calculate_capacity(),
            "current_state": self.current_state,
        }

    def _calculate_flow(self) -> dict[str, Any]:
        """Calculate flow metrics."""
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
        # Count actual wagon rejections from events
        wagons_rejected = sum(
            1
            for _, e in self.events
            if type(e).__name__ == "WagonRejectedEvent"
        )

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

    def _calculate_throughput(self) -> float:
        """Calculate throughput rate."""
        retrofits = self.event_counts.get(
            "WagonRetrofitCompletedEvent", 0
        ) + self.event_counts.get("RetrofitCompletedEvent", 0)
        return retrofits / self.duration_hours if self.duration_hours > 0 else 0.0

    def _calculate_workshop(self) -> dict[str, Any]:
        """Calculate workshop metrics."""
        workshop_data: dict[Any, dict[str, Any]] = defaultdict(
            lambda: {
                "wagons_processed": 0,
                "retrofits_started": 0,
            }
        )

        for _, event in self.events:
            event_type = type(event).__name__
            workshop_id = getattr(event, "workshop_id", None)

            if workshop_id:
                if event_type in (
                    "WagonRetrofitCompletedEvent",
                    "RetrofitCompletedEvent",
                ):
                    workshop_data[workshop_id]["wagons_processed"] += 1
                elif event_type == "RetrofitStartedEvent":
                    workshop_data[workshop_id]["retrofits_started"] += 1

        return {
            "total_workshops": len(workshop_data),
            "workshops": dict(workshop_data),
            "total_wagons_processed": sum(
                w["wagons_processed"] for w in workshop_data.values()
            ),
        }

    def _calculate_locomotive(self) -> dict[str, Any]:
        """Calculate locomotive metrics."""
        allocated = self.event_counts.get("LocomotiveAllocatedEvent", 0)
        released = self.event_counts.get("LocomotiveReleasedEvent", 0)
        movements = self.event_counts.get("LocomotiveMovementRequestEvent", 0)

        total_loco_events = allocated + released + movements
        utilization_percent = (
            (allocated / max(allocated + released, 1)) * 100
            if (allocated + released) > 0
            else 0.0
        )

        return {
            "utilization_percent": utilization_percent,
            "allocations": allocated,
            "releases": released,
            "movements": movements,
            "total_operations": total_loco_events,
        }

    def _calculate_shunting(self) -> dict[str, Any]:
        """Calculate shunting metrics."""
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

    def _calculate_yard(self) -> dict[str, Any]:
        """Calculate yard metrics."""
        return {
            "wagons_classified": self.event_counts.get("WagonClassifiedEvent", 0),
            "wagons_distributed": self.event_counts.get("WagonDistributedEvent", 0),
            "wagons_parked": self.event_counts.get("WagonParkedEvent", 0),
        }

    def _calculate_capacity(self) -> dict[str, Any]:
        """Calculate capacity metrics."""
        total_wagons = sum(
            len(getattr(e, "wagons", []))
            for _, e in self.events
            if type(e).__name__ == "TrainArrivedEvent"
        )

        return {
            "total_wagon_movements": total_wagons,
            "active_operations": len(self.events),
            "events_per_hour": len(self.events) / max(self.duration_hours, 0.1),
        }
