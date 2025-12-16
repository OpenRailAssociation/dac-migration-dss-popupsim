"""Unified analytics service for cross-context analysis and monitoring."""

# pylint: disable=duplicate-code
from collections import deque
from dataclasses import dataclass
from typing import Any

from contexts.analytics.domain.events.analytics_events import BottleneckDetectedEvent
from contexts.analytics.domain.value_objects.analytics_config import AnalyticsConfig


@dataclass
class BottleneckAnalysis:
    """Analysis of system bottlenecks."""

    bottleneck_type: str
    severity: float
    affected_contexts: list[str]
    description: str


@dataclass
class Alert:
    """Real-time alert."""

    alert_type: str
    severity: str  # Keep as string for simplicity in this service
    message: str
    timestamp: float
    context: str


class AnalyticsService:
    """Unified service for cross-context analysis and real-time monitoring."""

    def __init__(
        self,
        event_collector: Any,
        event_bus: Any | None = None,
        config: AnalyticsConfig | None = None,
    ) -> None:
        self.config = config or AnalyticsConfig()
        self.event_collector = event_collector
        self.event_bus = event_bus
        self.alerts: deque[Alert] = deque(maxlen=self.config.max_alerts)
        self._last_stats: dict[str, Any] = {}

    def analyze_bottlenecks(self) -> list[BottleneckAnalysis]:
        """Identify bottlenecks and publish events."""
        stats = self.event_collector.compute_statistics()
        bottlenecks = []

        wagons_arrived = stats.get('wagons_arrived', 0)
        retrofits_completed = stats.get('retrofits_completed', 0)

        if wagons_arrived > 0:
            completion_rate = retrofits_completed / wagons_arrived
            if completion_rate < 0.8:
                severity = 1.0 - completion_rate
                bottleneck = BottleneckAnalysis(
                    bottleneck_type='retrofit_capacity',
                    severity=severity,
                    affected_contexts=['external_trains', 'popup_retrofit'],
                    description=f'Retrofit completion rate {completion_rate:.1%} indicates capacity bottleneck',
                )
                bottlenecks.append(bottleneck)

                if self.event_bus:
                    event = BottleneckDetectedEvent(
                        bottleneck_type=bottleneck.bottleneck_type,
                        severity=bottleneck.severity,
                        affected_contexts=bottleneck.affected_contexts,
                        description=bottleneck.description,
                    )
                    self.event_bus.publish(event)

        return bottlenecks

    def check_alerts(self) -> list[Alert]:
        """Check for alert conditions."""
        current_stats = self.event_collector.compute_statistics()
        new_alerts = []

        wagons_arrived = current_stats.get('wagons_arrived', 0)
        retrofits_completed = current_stats.get('retrofits_completed', 0)

        if wagons_arrived > 0:
            completion_rate = retrofits_completed / wagons_arrived

            if completion_rate < self.config.completion_rate_critical:
                alert = Alert(
                    alert_type='completion_rate',
                    severity='critical',
                    message=f'Critical: Completion rate {completion_rate:.1%}',
                    timestamp=0.0,
                    context='popup_retrofit',
                )
                new_alerts.append(alert)
            elif completion_rate < self.config.completion_rate_warning:
                alert = Alert(
                    alert_type='completion_rate',
                    severity='medium',
                    message=f'Warning: Completion rate {completion_rate:.1%}',
                    timestamp=0.0,
                    context='popup_retrofit',
                )
                new_alerts.append(alert)

        for alert in new_alerts:
            self.alerts.append(alert)

        self._last_stats = current_stats
        return new_alerts

    def get_cross_context_metrics(self) -> dict[str, Any]:
        """Get comprehensive cross-context metrics."""
        bottlenecks = self.analyze_bottlenecks()
        stats = self.event_collector.compute_statistics()

        trains_arrived = stats.get('trains_arrived', 0)
        retrofits_completed = stats.get('retrofits_completed', 0)
        wagons_arrived = stats.get('wagons_arrived', 0)

        flow_efficiency = retrofits_completed / wagons_arrived if wagons_arrived > 0 else 0.0

        return {
            'bottlenecks': [
                {
                    'type': b.bottleneck_type,
                    'severity': b.severity,
                    'contexts': b.affected_contexts,
                    'description': b.description,
                }
                for b in bottlenecks
            ],
            'flow_analysis': {
                'throughput': retrofits_completed,
                'efficiency': flow_efficiency,
                'utilization': {
                    'external_trains': 1.0 if trains_arrived > 0 else 0.0,
                    'popup_retrofit': flow_efficiency,
                },
                'idle_ratio': 1.0 - flow_efficiency,
            },
        }

    def get_current_status(self) -> dict[str, Any]:
        """Get current system status."""
        stats = self.event_collector.compute_statistics()
        recent_alerts = list(self.alerts)[-10:]

        critical_alerts = [a for a in recent_alerts if a.severity == 'critical']
        health_status = 'critical' if critical_alerts else 'healthy'

        return {
            'health_status': health_status,
            'active_alerts': len(recent_alerts),
            'critical_alerts': len(critical_alerts),
            'recent_alerts': [
                {
                    'type': a.alert_type,
                    'severity': a.severity,
                    'message': a.message,
                    'context': a.context,
                }
                for a in recent_alerts
            ],
            'key_metrics': {
                'completion_rate': stats.get('completion_rate', 0.0),
                'total_throughput': stats.get('retrofits_completed', 0),
                'active_contexts': len([k for k, v in stats.get('event_counts', {}).items() if v > 0]),
            },
        }
