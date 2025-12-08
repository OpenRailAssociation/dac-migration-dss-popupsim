"""Statistics computation service - focused on computing metrics."""

from typing import Any


class StatisticsComputationService:
    """Computes statistics from collected events."""

    def compute_statistics(
        self,
        events: list[tuple[float, Any]],
        event_counts: dict[str, int],
        start_time: float,
        current_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute all statistics from events."""
        from contexts.analytics.domain.entities.metrics_aggregator import (
            MetricsAggregator,
        )

        aggregator = MetricsAggregator(events, event_counts, start_time, current_state)
        return aggregator.compute_all_metrics()

    def compute_filtered_statistics(
        self,
        events: list[tuple[float, Any]],
        event_counts: dict[str, int],
        start_time: float,
        context_filter: str | None = None,
        current_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute statistics with optional context filter."""
        if context_filter:
            filtered_events = [
                (ts, e)
                for ts, e in events
                if context_filter.lower() in type(e).__name__.lower()
            ]
            filtered_counts = {
                k: v
                for k, v in event_counts.items()
                if context_filter.lower() in k.lower()
            }
            return self.compute_statistics(
                filtered_events, filtered_counts, start_time, current_state
            )

        return self.compute_statistics(events, event_counts, start_time, current_state)
