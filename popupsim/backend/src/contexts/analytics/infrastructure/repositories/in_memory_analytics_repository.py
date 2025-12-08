"""In-memory implementation of analytics repository."""

from contexts.analytics.domain.aggregates.analytics_session import AnalyticsSession
from contexts.analytics.domain.repositories.analytics_repository import AnalyticsRepository


class InMemoryAnalyticsRepository(AnalyticsRepository):
    """In-memory storage for analytics sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, AnalyticsSession] = {}

    def save(self, session: AnalyticsSession) -> None:
        """Save analytics session."""
        self._sessions[session.session_id] = session

    def find_by_id(self, session_id: str) -> AnalyticsSession | None:
        """Find session by ID."""
        return self._sessions.get(session_id)

    def find_all(self) -> list[AnalyticsSession]:
        """Find all sessions."""
        return list(self._sessions.values())

    def delete(self, session_id: str) -> None:
        """Delete session."""
        self._sessions.pop(session_id, None)
