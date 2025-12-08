"""Duration tracking service for analytics."""

from collections import defaultdict
from typing import Any


class DurationTracker:
    """Service for tracking durations of various operations."""

    def __init__(self) -> None:
        self._start_times: dict[str, float] = {}
        self._durations: dict[str, list[float]] = defaultdict(list)

    def start_tracking(self, operation_id: str, timestamp: float) -> None:
        """Start tracking duration for an operation."""
        self._start_times[operation_id] = timestamp

    def end_tracking(self, operation_id: str, timestamp: float) -> float | None:
        """End tracking and return duration."""
        start_time = self._start_times.pop(operation_id, None)
        if start_time is None:
            return None

        duration = timestamp - start_time
        self._durations[operation_id].append(duration)
        return duration

    def get_durations(self, operation_id: str) -> list[float]:
        """Get all recorded durations for an operation."""
        return self._durations[operation_id].copy()

    def get_average_duration(self, operation_id: str) -> float:
        """Get average duration for an operation."""
        durations = self._durations[operation_id]
        return sum(durations) / len(durations) if durations else 0.0

    def get_total_duration(self, operation_id: str) -> float:
        """Get total duration for an operation."""
        return sum(self._durations[operation_id])

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get comprehensive duration statistics."""
        stats = {}
        for operation_id, durations in self._durations.items():
            if durations:
                stats[operation_id] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                }
        return stats
