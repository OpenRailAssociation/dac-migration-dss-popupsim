"""Analytics repository interface."""

from abc import ABC, abstractmethod

from ..aggregates.analytics_session import AnalyticsSession
from ..events.base_event import DomainEvent
from ..models.kpi_result import KPIResult


class AnalyticsRepository(ABC):
    """Repository for analytics data persistence."""
    
    @abstractmethod
    def save_session(self, session: AnalyticsSession) -> None:
        """Save analytics session."""
        raise NotImplementedError
    
    @abstractmethod
    def get_session(self, scenario_id: str) -> AnalyticsSession | None:
        """Get analytics session by scenario ID."""
        raise NotImplementedError
    
    @abstractmethod
    def save_events(self, scenario_id: str, events: list[DomainEvent]) -> None:
        """Save domain events for scenario."""
        raise NotImplementedError
    
    @abstractmethod
    def get_events(self, scenario_id: str) -> list[DomainEvent]:
        """Get all events for scenario."""
        raise NotImplementedError
    
    @abstractmethod
    def save_kpi_result(self, scenario_id: str, kpi_result: KPIResult) -> None:
        """Save KPI calculation result."""
        raise NotImplementedError
    
    @abstractmethod
    def get_kpi_result(self, scenario_id: str) -> KPIResult | None:
        """Get KPI result for scenario."""
        raise NotImplementedError