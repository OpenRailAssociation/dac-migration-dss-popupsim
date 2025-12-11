"""Event collection service - focused on collecting events only."""

from collections import defaultdict
import time
from typing import Any


class EventCollectorService:
    """Collects and stores events with timestamps."""

    def __init__(self) -> None:
        self.events: list[tuple[float, Any]] = []
        self.event_counts: dict[str, int] = defaultdict(int)
        self.start_time = time.time()

    def collect_event(self, event: Any) -> None:
        """Collect event with timestamp."""
        timestamp = getattr(event, 'timestamp', time.time())
        self.events.append((timestamp, event))
        event_type = type(event).__name__
        self.event_counts[event_type] += 1

    def get_events(self) -> list[tuple[float, Any]]:
        """Get all collected events."""
        return self.events.copy()

    def get_event_counts(self) -> dict[str, int]:
        """Get event counts by type."""
        return dict(self.event_counts)

    def get_events_by_type(self, event_type: str) -> list[Any]:
        """Get events of specific type."""
        return [e for _, e in self.events if type(e).__name__ == event_type]

    def get_start_time(self) -> float:
        """Get collection start time."""
        return self.start_time

    def clear(self) -> None:
        """Clear all collected events."""
        self.events.clear()
        self.event_counts.clear()
        self.start_time = time.time()
