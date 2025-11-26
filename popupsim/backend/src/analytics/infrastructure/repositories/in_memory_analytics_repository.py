"""In-memory analytics repository implementation."""

from analytics.domain.aggregates.analytics_session import AnalyticsSession
from analytics.domain.events.base_event import DomainEvent
from analytics.domain.models.kpi_result import KPIResult
from analytics.domain.repositories.analytics_repository import AnalyticsRepository


class InMemoryAnalyticsRepository(AnalyticsRepository):
    """In-memory implementation of analytics repository."""

    def __init__(self) -> None:
        self._sessions: dict[str, AnalyticsSession] = {}
        self._events: dict[str, list[DomainEvent]] = {}
        self._kpi_results: dict[str, KPIResult] = {}

    def save_session(self, session: AnalyticsSession) -> None:
        """Save analytics session."""
        self._sessions[session.scenario_id] = session

    def get_session(self, scenario_id: str) -> AnalyticsSession | None:
        """Get analytics session by scenario ID."""
        return self._sessions.get(scenario_id)

    def save_events(self, scenario_id: str, events: list[DomainEvent]) -> None:
        """Save domain events for scenario."""
        self._events[scenario_id] = events.copy()

    def get_events(self, scenario_id: str) -> list[DomainEvent]:
        """Get all events for scenario."""
        return self._events.get(scenario_id, []).copy()

    def save_kpi_result(self, scenario_id: str, kpi_result: KPIResult) -> None:
        """Save KPI calculation result."""
        self._kpi_results[scenario_id] = kpi_result

    def get_kpi_result(self, scenario_id: str) -> KPIResult | None:
        """Get KPI result for scenario."""
        return self._kpi_results.get(scenario_id)

    def clear(self) -> None:
        """Clear all stored data (for testing)."""
        self._sessions.clear()
        self._events.clear()
        self._kpi_results.clear()
