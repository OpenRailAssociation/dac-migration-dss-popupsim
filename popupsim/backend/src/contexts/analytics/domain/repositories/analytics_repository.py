"""Repository interface for Analytics Context."""

from abc import ABC, abstractmethod

from contexts.analytics.domain.aggregates.analytics_session import (
    AnalyticsSession,
)


class AnalyticsRepository(ABC):
    """Repository for persisting analytics sessions."""

    @abstractmethod
    def save(self, session: AnalyticsSession) -> None:
        """Save analytics session."""

    @abstractmethod
    def find_by_id(self, session_id: str) -> AnalyticsSession | None:
        """Find session by ID."""

    @abstractmethod
    def find_all(self) -> list[AnalyticsSession]:
        """Find all sessions."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Delete session."""
