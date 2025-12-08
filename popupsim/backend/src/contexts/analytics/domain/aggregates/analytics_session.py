"""Analytics session aggregate for Analytics Context."""

from dataclasses import dataclass
from dataclasses import field
import time
from typing import Any

from contexts.analytics.domain.entities.metric_collector import MetricCollector
from contexts.analytics.domain.events.analytics_events import AnalysisCompletedEvent
from contexts.analytics.domain.events.analytics_events import CollectorAddedEvent
from contexts.analytics.domain.events.analytics_events import MetricsCollectedEvent
from contexts.analytics.domain.value_objects.analytics_metrics import AnalyticsMetrics
from contexts.analytics.domain.value_objects.metric_id import MetricId


@dataclass
class AnalyticsSession:
    """Aggregate root managing analytics collection and analysis."""

    session_id: str
    start_time: float = field(default_factory=time.time)
    _collectors: dict[str, MetricCollector] = field(default_factory=dict)
    _domain_events: list[Any] = field(default_factory=list)

    def add_collector(self, collector_id: str) -> MetricCollector:
        """Add a metric collector (entity)."""
        if collector_id in self._collectors:
            msg = f'Collector {collector_id} already exists'
            raise ValueError(msg)

        collector = MetricCollector(MetricId(collector_id))
        self._collectors[collector_id] = collector

        event = CollectorAddedEvent(
            session_id=self.session_id,
            collector_id=collector_id,
        )
        self._domain_events.append(event)

        return collector

    def get_collector(self, collector_id: str) -> MetricCollector | None:
        """Get collector by ID."""
        return self._collectors.get(collector_id)

    def record_metric(
        self, collector_id: str, key: str, value: Any, timestamp: float | None = None
    ) -> MetricsCollectedEvent:
        """Record metric with validation and return event."""
        if not isinstance(value, (int, float, str, bool)):
            msg = f'Invalid metric value type: {type(value)}'
            raise ValueError(msg)

        collector = self.get_collector(collector_id)
        if not collector:
            collector = self.add_collector(collector_id)

        collector.record_metric(key, value, timestamp)

        return MetricsCollectedEvent(
            collector_id=collector.collector_id,
            metrics=collector.get_all_latest(),
            timestamp=timestamp or time.time(),
        )

    def calculate_session_duration(self) -> float:
        """Calculate session duration in seconds."""
        return time.time() - self.start_time

    def analyze_session(self) -> AnalysisCompletedEvent:
        """Analyze collected metrics and return event."""
        total_events = sum(c.events_processed for c in self._collectors.values())
        duration = self.calculate_session_duration()

        throughput = total_events / max(duration / 3600, 0.1)  # Events per hour
        utilization = min(1.0, total_events / (len(self._collectors) * 100)) if self._collectors else 0.0

        total_wagons = sum(c.get_latest('total_wagons') or 0 for c in self._collectors.values())
        processed_wagons = sum(c.get_latest('processed_wagons') or 0 for c in self._collectors.values())

        metrics = AnalyticsMetrics(
            throughput=throughput,
            utilization=utilization,
            total_wagons=total_wagons,
            processed_wagons=processed_wagons,
        )

        return AnalysisCompletedEvent(analysis_id=self.session_id, results=metrics, duration=duration)

    def get_all_collectors(self) -> dict[str, MetricCollector]:
        """Get all collectors (for read-only access)."""
        return self._collectors.copy()

    def get_collector_ids(self) -> list[str]:
        """Get all collector IDs."""
        return list(self._collectors.keys())

    def get_collector_count(self) -> int:
        """Get number of collectors."""
        return len(self._collectors)

    def has_collector(self, collector_id: str) -> bool:
        """Check if collector exists."""
        return collector_id in self._collectors

    def collect_domain_events(self) -> list[Any]:
        """Collect and clear domain events."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
