"""Query service for analytics data."""

from dataclasses import dataclass
from typing import Any

from contexts.analytics.domain.aggregates.analytics_session import AnalyticsSession
from contexts.analytics.domain.repositories.analytics_repository import AnalyticsRepository


@dataclass
class TimeSeriesMetrics:
    """Time series metrics result."""

    session_id: str
    start_time: float
    end_time: float
    metrics: dict[str, list[tuple[float, Any]]]


@dataclass
class TrendAnalysis:
    """Trend analysis result."""

    metric_name: str
    sessions: list[str]
    values: list[float]
    trend: str  # 'increasing', 'decreasing', 'stable'


class AnalyticsQueryService:
    """Handles analytics queries."""

    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    def get_session(self, session_id: str) -> AnalyticsSession | None:
        return self.repository.find_by_id(session_id)

    def get_all_sessions(self) -> list[AnalyticsSession]:
        return self.repository.find_all()

    def get_metrics_for_period(self, session_id: str, start: float, end: float) -> TimeSeriesMetrics | None:
        session = self.repository.find_by_id(session_id)
        if not session:
            return None

        filtered_metrics: dict[str, list[tuple[float, Any]]] = {}
        for collector_id, collector in session.get_all_collectors().items():
            for key in collector.get_metric_keys():
                time_series = collector.get_time_series(key)
                filtered = [(ts, val) for ts, val in time_series if start <= ts <= end]
                if filtered:
                    metric_key = f'{collector_id}_{key}'
                    filtered_metrics[metric_key] = filtered

        return TimeSeriesMetrics(
            session_id=session_id,
            start_time=start,
            end_time=end,
            metrics=filtered_metrics,
        )

    def get_trend_analysis(self, metric_name: str, session_ids: list[str]) -> TrendAnalysis:
        values: list[float] = []
        valid_sessions: list[str] = []

        for session_id in session_ids:
            session = self.repository.find_by_id(session_id)
            if session:
                for collector in session.get_all_collectors().values():
                    value = collector.get_latest(metric_name)
                    if value is not None:
                        values.append(float(value))
                        valid_sessions.append(session_id)
                        break

        trend = self._calculate_trend(values)

        return TrendAnalysis(metric_name=metric_name, sessions=valid_sessions, values=values, trend=trend)

    def _calculate_trend(self, values: list[float]) -> str:
        if len(values) < 2:
            return 'stable'

        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])

        if increases > decreases * 1.5:
            return 'increasing'
        if decreases > increases * 1.5:
            return 'decreasing'
        return 'stable'
