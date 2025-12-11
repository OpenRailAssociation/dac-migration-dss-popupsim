"""Port interface for Analytics Context."""

from abc import ABC
from abc import abstractmethod
from typing import Any

from contexts.analytics.domain.value_objects.analytics_metrics import AnalyticsMetrics
from contexts.analytics.domain.value_objects.analytics_metrics import Threshold


class AnalyticsContextPort(ABC):
    """Port interface for Analytics Context operations."""

    @abstractmethod
    def start_session(self, session_id: str) -> None:
        """Start analytics session."""

    @abstractmethod
    def end_session(self) -> None:
        """End current analytics session."""

    @abstractmethod
    def record_metric(self, collector_id: str, key: str, value: Any, timestamp: float | None = None) -> None:
        """Record metric value with optional timestamp."""

    @abstractmethod
    def set_threshold(self, threshold: Threshold) -> None:
        """Set threshold for metric monitoring."""

    @abstractmethod
    def subscribe_to_event(self, event_type: type[Any]) -> None:
        """Subscribe to specific event type."""

    @abstractmethod
    def analyze_session(self) -> AnalyticsMetrics:
        """Analyze current session."""

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""

    @abstractmethod
    def get_context_metrics(self, context_name: str) -> dict[str, Any]:
        """Get metrics for specific context."""

    @abstractmethod
    def clear_all_metrics(self) -> None:
        """Clear all metrics."""

    @abstractmethod
    def get_cross_context_analysis(self) -> dict[str, Any]:
        """Get cross-context analysis."""

    @abstractmethod
    def get_real_time_status(self) -> dict[str, Any]:
        """Get real-time status."""

    @abstractmethod
    def get_advanced_kpis(self) -> dict[str, Any]:
        """Get advanced KPIs."""

    @abstractmethod
    def get_current_state(self) -> dict[str, Any]:
        """Get current system state snapshot."""

    @abstractmethod
    def get_time_series(self, metric_name: str, interval_seconds: float = 3600.0) -> list[tuple[float, Any]]:
        """Get time-series data for metric."""

    @abstractmethod
    def get_all_time_series(self, interval_seconds: float = 3600.0) -> dict[str, list[tuple[float, Any]]]:
        """Get all time-series metrics."""
