"""Real-time monitoring service."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from contexts.analytics.domain.value_objects.analytics_config import AnalyticsConfig


@dataclass
class Alert:
    """Real-time alert."""

    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: float
    context: str


class RealTimeMonitor:
    """Monitors system in real-time and generates alerts."""

    def __init__(self, event_collector: Any, config: AnalyticsConfig | None = None) -> None:
        self.config = config or AnalyticsConfig()
        self.event_collector = event_collector
        self.alerts: deque[Alert] = deque(maxlen=self.config.max_alerts)
        self.alert_handlers: list[Callable[[Alert], None]] = []
        self._last_stats: dict[str, Any] = {}

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add alert handler callback."""
        self.alert_handlers.append(handler)

    def check_alerts(self) -> list[Alert]:
        """Check for alert conditions and generate alerts."""
        current_stats = self.event_collector.compute_statistics()
        new_alerts = []

        # Check completion rate
        wagons_arrived = current_stats.get('wagons_arrived', 0)
        retrofits_completed = current_stats.get('retrofits_completed', 0)

        if wagons_arrived > 0:
            completion_rate = retrofits_completed / wagons_arrived

            if completion_rate < self.config.completion_rate_critical:
                alert = Alert(
                    alert_type='completion_rate',
                    severity='critical',
                    message=f'Critical: Completion rate {completion_rate:.1%} below {self.config.completion_rate_critical:.1%}',
                    timestamp=0.0,  # Would be actual timestamp in real system
                    context='popup_retrofit',
                )
                new_alerts.append(alert)
            elif completion_rate < self.config.completion_rate_warning:
                alert = Alert(
                    alert_type='completion_rate',
                    severity='medium',
                    message=f'Warning: Completion rate {completion_rate:.1%} below {self.config.completion_rate_warning:.1%}',
                    timestamp=0.0,
                    context='popup_retrofit',
                )
                new_alerts.append(alert)

        # Check throughput drop
        if self._last_stats:
            last_completed = self._last_stats.get('retrofits_completed', 0)
            current_completed = current_stats.get('retrofits_completed', 0)

            if last_completed > 0:
                throughput_change = (current_completed - last_completed) / last_completed
                if throughput_change < -self.config.throughput_drop_threshold:
                    alert = Alert(
                        alert_type='throughput_drop',
                        severity='high',
                        message=f'Throughput dropped by {abs(throughput_change):.1%}',
                        timestamp=0.0,
                        context='system',
                    )
                    new_alerts.append(alert)

        # Store alerts and notify handlers
        for alert in new_alerts:
            self.alerts.append(alert)
            for handler in self.alert_handlers:
                handler(alert)

        self._last_stats = current_stats
        return new_alerts

    def get_current_status(self) -> dict[str, Any]:
        """Get current system status."""
        stats = self.event_collector.compute_statistics()
        recent_alerts = list(self.alerts)[-10:]  # Last 10 alerts

        # Determine overall health
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
