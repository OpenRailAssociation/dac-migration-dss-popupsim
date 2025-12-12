"""Metric collector entity for Analytics Context."""
# pylint: disable=duplicate-code
from dataclasses import dataclass
from dataclasses import field
import time
from typing import Any

from contexts.analytics.domain.value_objects.metric_id import MetricId


@dataclass
class MetricEntry:
    """Single metric entry with timestamp."""

    key: str
    value: Any
    timestamp: float


@dataclass
class MetricCollector:
    """Entity collecting time-series metrics."""

    collector_id: MetricId
    _metrics: dict[str, list[MetricEntry]] = field(default_factory=dict)
    events_processed: int = 0

    def record_metric(self, key: str, value: Any, timestamp: float | None = None) -> None:
        """Record a metric value with timestamp."""
        ts = timestamp if timestamp is not None else time.time()
        entry = MetricEntry(key, value, ts)

        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(entry)
        self.events_processed += 1

    def get_latest(self, key: str) -> Any | None:
        """Get latest metric value."""
        entries = self._metrics.get(key, [])
        return entries[-1].value if entries else None

    def get_time_series(self, key: str) -> list[tuple[float, Any]]:
        """Get time series for metric."""
        return [(e.timestamp, e.value) for e in self._metrics.get(key, [])]

    def get_all_latest(self) -> dict[str, Any]:
        """Get latest value for all metrics."""
        return {key: entries[-1].value for key, entries in self._metrics.items() if entries}

    def get_metric_keys(self) -> list[str]:
        """Get all metric keys."""
        return list(self._metrics.keys())

    def has_metric(self, key: str) -> bool:
        """Check if metric exists."""
        return key in self._metrics

    def get_metric_count(self, key: str) -> int:
        """Get number of entries for metric."""
        return len(self._metrics.get(key, []))

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics with their complete time series."""
        return {
            key: {
                'latest': entries[-1].value if entries else None,
                'count': len(entries),
                'time_series': [(e.timestamp, e.value) for e in entries],
            }
            for key, entries in self._metrics.items()
        }

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self.events_processed = 0
