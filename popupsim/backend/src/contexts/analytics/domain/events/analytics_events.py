"""Domain events for Analytics Context."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from contexts.analytics.domain.value_objects.analytics_metrics import AnalyticsMetrics
from contexts.analytics.domain.value_objects.metric_id import MetricId
from contexts.analytics.domain.value_objects.severity import SeverityLevel


@dataclass(frozen=True)
class MetricsCollectedEvent:
    """Event published when metrics are collected."""

    collector_id: MetricId
    metrics: dict[str, Any]
    timestamp: float
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'metrics_collected'


@dataclass(frozen=True)
class AnalysisCompletedEvent:
    """Event published when analysis is completed."""

    analysis_id: str
    results: AnalyticsMetrics
    duration: float
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    timestamp: float = field(default_factory=__import__('time').time)

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'analysis_completed'


@dataclass(frozen=True)
class ThresholdViolatedEvent:
    """Event published when metric threshold is violated."""

    metric_name: str
    current_value: float
    threshold_value: float
    severity: str | SeverityLevel
    timestamp: float = field(default_factory=__import__('time').time)
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'threshold_violated'

    @property
    def severity_value(self) -> str:
        """Get severity as string for backward compatibility."""
        if isinstance(self.severity, SeverityLevel):
            return self.severity.value
        return self.severity


@dataclass(frozen=True)
class BottleneckDetectedEvent:
    """Event published when bottleneck is detected."""

    bottleneck_type: str
    severity: float
    affected_contexts: list[str]
    description: str
    timestamp: float = field(default_factory=__import__('time').time)
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'bottleneck_detected'


@dataclass(frozen=True)
class SessionStartedEvent:
    """Event published when analytics session starts."""

    session_id: str
    timestamp: float = field(default_factory=__import__('time').time)
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'session_started'


@dataclass(frozen=True)
class SessionEndedEvent:
    """Event published when analytics session ends."""

    session_id: str
    duration: float
    total_events: int
    timestamp: float = field(default_factory=__import__('time').time)
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'session_ended'


@dataclass(frozen=True)
class CollectorAddedEvent:
    """Event published when collector is added to session."""

    session_id: str
    collector_id: str
    timestamp: float = field(default_factory=__import__('time').time)
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return event type."""
        return 'collector_added'


@dataclass(frozen=True)
class ThresholdSetEvent:
    """Event published when threshold is set."""

    session_id: str
    metric_name: str
    warning_value: float
    critical_value: float
    timestamp: float = field(default_factory=__import__('time').time)
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))

    @property
    def event_type(self) -> str:
        """Return type of element."""
        return 'threshold_set'
