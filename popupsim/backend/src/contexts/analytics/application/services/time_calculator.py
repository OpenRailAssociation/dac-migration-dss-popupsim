"""Time calculation utilities."""

import time
from typing import Any


class TimeCalculator:
    """Calculates time-based metrics from events."""

    def __init__(self, events: list[tuple[float, Any]], start_time: float) -> None:
        self.events = events
        self.start_time = start_time

    def get_duration_hours(self) -> float:
        """Get simulation duration in hours from timestamps."""
        if not self.events:
            return 0.0

        timestamps = [ts for ts, _ in self.events]
        if len(timestamps) < 2:
            return (time.time() - self.start_time) / 3600

        duration_seconds = max(timestamps) - min(timestamps)
        return duration_seconds / 3600

    def calculate_throughput_rate(self, completed_count: int) -> float:
        """Calculate throughput rate per hour."""
        duration = self.get_duration_hours()
        return completed_count / duration if duration > 0 else 0.0
