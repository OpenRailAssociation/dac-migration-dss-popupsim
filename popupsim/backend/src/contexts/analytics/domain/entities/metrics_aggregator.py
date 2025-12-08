"""Aggregates metrics from collected events."""

# pylint: disable=duplicate-code
import time
from typing import Any

from contexts.analytics.domain.services.metrics_calculation_service import MetricsCalculationService


class MetricsAggregator:  # pylint: disable=R0903
    """Aggregates metrics from event stream."""

    def __init__(
        self,
        events: list[tuple[float, Any]],
        event_counts: dict[str, int],
        start_time: float,
        current_state: dict[str, Any] | None = None,
    ) -> None:
        self.events = events
        self.event_counts = event_counts
        self.start_time = start_time
        self.current_state = current_state or {}

    def compute_all_metrics(self) -> dict[str, Any]:
        """Compute all metrics from events."""
        duration_hours = self._get_duration_hours()

        calc = MetricsCalculationService(self.events, self.event_counts, duration_hours, self.current_state)
        metrics = calc.calculate_all()

        return {
            'total_events': len(self.events),
            'event_counts': dict(self.event_counts),
            **metrics,
        }

    def _get_duration_hours(self) -> float:
        """Get duration in hours from timestamps."""
        if not self.events:
            return 0.0

        timestamps = [ts for ts, _ in self.events]
        if len(timestamps) < 2:
            return (time.time() - self.start_time) / 3600

        duration_seconds = max(timestamps) - min(timestamps)
        return duration_seconds / 3600
