"""Time-series data aggregation service."""

from collections import defaultdict
from typing import Any


class TimeSeriesService:
    """Aggregates events into time-series data."""

    def __init__(self, events: list[tuple[float, Any]]) -> None:
        self.events = events

    def get_time_series(self, metric_name: str, interval_seconds: float = 3600.0) -> list[tuple[float, Any]]:
        """Get time-series data for metric with configurable interval.

        Args:
            metric_name: Name of metric to track
            interval_seconds: Time interval in seconds (default: 1 hour)

        Returns
        -------
            List of (timestamp, value) tuples
        """
        if not self.events:
            return []

        # Get time range
        timestamps = [ts for ts, _ in self.events]
        start_time = min(timestamps)
        end_time = max(timestamps)

        # Create time buckets
        time_series: dict[float, Any] = {}
        current_time = start_time

        while current_time <= end_time:
            bucket_end = current_time + interval_seconds
            bucket_events = [e for ts, e in self.events if current_time <= ts < bucket_end]

            value = self._calculate_metric(metric_name, bucket_events)
            time_series[current_time] = value
            current_time = bucket_end

        return sorted(time_series.items())

    # ruff: noqa: PLR0911
    def _calculate_metric(self, metric_name: str, events: list[Any]) -> Any:  # pylint: disable=too-many-return-statements
        """Calculate metric value for time bucket."""
        if metric_name == 'train_arrivals':
            return self._count_train_arrivals(events)
        if metric_name == 'wagons_arrived':
            return self._count_wagons_arrived(events)
        if metric_name == 'retrofits_completed':
            return self._count_retrofits_completed(events)
        if metric_name == 'locomotive_utilization':
            return self._calculate_locomotive_utilization(events)
        if metric_name == 'workshop_utilization':
            return self._calculate_workshop_utilization(events)
        if metric_name == 'track_occupancy':
            return self._calculate_track_occupancy(events)
        return 0

    def _count_train_arrivals(self, events: list[Any]) -> dict[str, int]:
        """Count train arrivals with wagon counts."""
        arrivals = [e for e in events if type(e).__name__ == 'TrainArrivedEvent']
        total_wagons = sum(len(getattr(e, 'wagons', [])) for e in arrivals)
        return {'count': len(arrivals), 'wagons': total_wagons}

    def _count_wagons_arrived(self, events: list[Any]) -> int:
        """Count wagons that arrived."""
        arrivals = [e for e in events if type(e).__name__ == 'TrainArrivedEvent']
        return sum(len(getattr(e, 'wagons', [])) for e in arrivals)

    def _count_retrofits_completed(self, events: list[Any]) -> int:
        """Count completed retrofits."""
        return sum(1 for e in events if type(e).__name__ in ('RetrofitCompletedEvent', 'WagonRetrofitCompletedEvent'))

    def _calculate_locomotive_utilization(self, events: list[Any]) -> dict[str, int]:
        """Calculate locomotive utilization breakdown."""
        breakdown: dict[str, int] = defaultdict(int)
        for e in events:
            event_type = type(e).__name__
            if event_type == 'LocomotiveAllocatedEvent':
                breakdown['moving'] += 1
            elif event_type == 'LocomotiveReleasedEvent':
                breakdown['parking'] += 1
        return dict(breakdown)

    def _calculate_workshop_utilization(self, events: list[Any]) -> dict[str, int]:
        """Calculate workshop utilization."""
        working = sum(1 for e in events if type(e).__name__ == 'RetrofitStartedEvent')
        completed = sum(1 for e in events if type(e).__name__ == 'RetrofitCompletedEvent')
        return {'working': working, 'completed': completed}

    def _calculate_track_occupancy(self, events: list[Any]) -> dict[str, int]:
        """Calculate track occupancy changes."""
        occupancy: dict[str, int] = defaultdict(int)
        for e in events:
            event_type = type(e).__name__
            if event_type == 'WagonDistributedEvent':
                track_id = getattr(e, 'track_id', 'unknown')
                occupancy[track_id] += 1
        return dict(occupancy)

    def get_all_time_series(self, interval_seconds: float = 3600.0) -> dict[str, list[tuple[float, Any]]]:
        """Get all available time-series metrics."""
        metrics = [
            'train_arrivals',
            'wagons_arrived',
            'retrofits_completed',
            'locomotive_utilization',
            'workshop_utilization',
            'track_occupancy',
        ]

        return {metric: self.get_time_series(metric, interval_seconds) for metric in metrics}
