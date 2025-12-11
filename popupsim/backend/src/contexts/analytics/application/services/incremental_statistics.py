"""Incremental statistics without full recomputation."""

from collections import defaultdict
import time
from typing import Any


class IncrementalStatistics:
    """Maintains running statistics (O(1) retrieval)."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = defaultdict(int)
        self.start_time = time.time()

    def update(self, event: Any) -> None:
        """Update statistics incrementally."""
        event_type = type(event).__name__
        self.counters[event_type] += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get current statistics (O(1))."""
        return {
            'event_counts': dict(self.counters),
            'total_events': sum(self.counters.values()),
            'duration_seconds': time.time() - self.start_time,
        }

    def clear(self) -> None:
        """Clear statistics."""
        self.counters.clear()
        self.start_time = time.time()
