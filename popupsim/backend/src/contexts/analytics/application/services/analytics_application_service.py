"""Main application service for analytics operations."""

from typing import Any

from contexts.analytics.domain.aggregates.analytics_session import (
    AnalyticsSession,
)
from contexts.analytics.domain.events.analytics_events import (
    SessionEndedEvent,
    SessionStartedEvent,
)
from contexts.analytics.domain.repositories.analytics_repository import (
    AnalyticsRepository,
)
from contexts.analytics.domain.services.metrics_service import (
    BottleneckThresholds,
    MetricsService,
)
from contexts.analytics.domain.value_objects.analytics_metrics import (
    AnalyticsMetrics,
    Threshold,
)
from infrastructure.event_bus.event_bus import EventBus

from .analytics_query_service import AnalyticsQueryService
from .event_stream_service import EventStreamService
from .metric_calculator_factory import MetricCalculatorFactory


class AnalyticsApplicationService:
    """Orchestrates analytics operations."""

    def __init__(
        self,
        event_bus: EventBus,
        repository: AnalyticsRepository,
        event_stream: EventStreamService,
        calculator_factory: MetricCalculatorFactory | None = None,
        query_service: AnalyticsQueryService | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.repository = repository
        self.event_stream = event_stream
        self.calculator_factory = calculator_factory or MetricCalculatorFactory()
        self.query_service = query_service or AnalyticsQueryService(repository)
        self.current_session: AnalyticsSession | None = None

    def start_session(self, session_id: str) -> None:
        self.current_session = AnalyticsSession(session_id)
        self.repository.save(self.current_session)

        event = SessionStartedEvent(session_id=session_id)
        self.event_bus.publish(event)

    def record_metric(
        self, collector_id: str, key: str, value: Any, timestamp: float | None = None
    ) -> None:
        if not self.current_session:
            self.start_session("default")

        assert self.current_session is not None
        event = self.current_session.record_metric(collector_id, key, value, timestamp)
        self.event_bus.publish(event)

        for domain_event in self.current_session.collect_domain_events():
            self.event_bus.publish(domain_event)

        self.repository.save(self.current_session)

    def set_threshold(self, threshold: Threshold) -> None:
        if not self.current_session:
            self.start_session("default")

        assert self.current_session is not None
        self.current_session.set_threshold(threshold)

        for domain_event in self.current_session.collect_domain_events():
            self.event_bus.publish(domain_event)

        self.repository.save(self.current_session)

    def analyze_session(self) -> AnalyticsMetrics:
        if not self.current_session:
            return AnalyticsMetrics(0.0, 0.0, 0, 0)

        event = self.current_session.analyze_session()
        self.event_bus.publish(event)
        self.repository.save(self.current_session)
        return event.results

    def get_metrics(self) -> dict[str, Any]:
        return self.event_stream.compute_statistics()

    def end_session(self) -> None:
        """End current session and publish event."""
        if not self.current_session:
            return

        duration = self.current_session.calculate_session_duration()
        total_events = sum(
            c.events_processed
            for c in self.current_session.get_all_collectors().values()
        )

        event = SessionEndedEvent(
            session_id=self.current_session.session_id,
            duration=duration,
            total_events=total_events,
        )
        self.event_bus.publish(event)
        self.repository.save(self.current_session)
        self.current_session = None

    def check_threshold_violations(self) -> list[Any]:
        """Check threshold violations and publish domain events."""
        if not self.current_session:
            return []

        violations = self.current_session.check_threshold_violations()

        # Publish domain events from aggregate
        for domain_event in self.current_session.collect_domain_events():
            self.event_bus.publish(domain_event)

        return violations

    def clear_all_metrics(self) -> None:
        self.event_stream.clear()

    def get_metrics_report(
        self,
        interval_seconds: float = 3600.0,
        thresholds: BottleneckThresholds | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive metrics including all KPIs, statistics, and bottlenecks.

        Parameters
        ----------
        interval_seconds : float
            Time interval for time-series aggregation (default: 1 hour).
        thresholds : BottleneckThresholds | None
            Custom thresholds for bottleneck detection.

        Returns
        -------
        dict[str, Any]
            Complete metrics report with:
            - Train arrivals with wagon counts over time
            - Wagon state distribution (retrofitted, rejected, parking, etc.)
            - Locomotive utilization breakdown and time-series
            - Workshop performance metrics and utilization
            - Track capacity utilization and state visualization
            - Bottleneck detection across all resources
        """
        # Get event data from event stream
        events = self.event_stream.get_all_events()
        event_counts = self.event_stream.get_event_counts()
        duration_hours = self.event_stream.get_duration_hours()
        current_state = self.event_stream.get_current_state()

        # Create metrics service
        metrics_service = MetricsService(
            events=events,
            event_counts=event_counts,
            duration_hours=duration_hours,
            current_state=current_state,
            thresholds=thresholds,
        )

        # Get all metrics
        return metrics_service.get_all_metrics()
