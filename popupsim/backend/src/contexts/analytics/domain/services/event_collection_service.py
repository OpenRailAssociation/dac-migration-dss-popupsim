"""Unified event collection service."""
# pylint: disable=duplicate-code
from collections import defaultdict
from collections import deque
from collections.abc import Callable
from pathlib import Path
import time
import traceback
from typing import Any

from contexts.analytics.domain.value_objects.analytics_config import AnalyticsConfig
from contexts.analytics.infrastructure.persistence.event_log import EventLog

from .event_discoverers import discover_all_events
from .incremental_statistics import IncrementalStatistics
from .state_tracking_service import StateTrackingService


class EventCollectionService:  # pylint: disable=too-many-instance-attributes
    """Collects events with persistence, incremental stats, and caching."""

    def __init__(
        self,
        event_bus: Any,
        log_path: Path | None = None,
        config: AnalyticsConfig | None = None,
    ) -> None:
        self.config = config or AnalyticsConfig()
        self.event_bus = event_bus
        self.events: deque[tuple[float, Any]] = deque(maxlen=self.config.max_events)
        self.event_counts: dict[str, int] = defaultdict(int)
        self.start_time = time.time()
        self.event_log = EventLog(log_path) if log_path else None
        self.incremental_stats = IncrementalStatistics()
        self.state_tracker = StateTrackingService()
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = self.config.cache_ttl_seconds

    def subscribe_to_all_events(self, handler: Callable[[Any], None]) -> None:
        """Subscribe to all domain events."""
        try:
            event_types = discover_all_events()
            for event_type in event_types:
                self.event_bus.subscribe(event_type, handler)
        except Exception as e:  # pylint: disable=(broad-exception-caught
            print(f'ERROR: Failed to subscribe to events: {e}')

            traceback.print_exc()

    def subscribe_to_event(self, event_type: type[Any], handler: Callable[[Any], None]) -> None:
        """Subscribe to specific event type."""
        self.event_bus.subscribe(event_type, handler)

    def collect_event(self, event: Any) -> None:
        """Collect event with persistence and incremental stats."""
        timestamp = getattr(event, 'event_timestamp', getattr(event, 'timestamp', time.time()))
        self.events.append((timestamp, event))
        event_type = type(event).__name__
        self.event_counts[event_type] += 1

        if self.event_log:
            self.event_log.append(timestamp, event)

        self.incremental_stats.update(event)
        self.state_tracker.process_event(event)
        self._invalidate_cache()
        self._prune_old_events()

    def _prune_old_events(self) -> None:
        """Remove events outside time window."""
        if not self.events or self.config.window_hours <= 0:
            return

        # Only prune if timestamps look like wall clock time (> 1000000000)
        if self.events[0][0] > 1000000000:
            cutoff = time.time() - (self.config.window_hours * 3600)
            while self.events and self.events[0][0] < cutoff:
                self.events.popleft()

    def get_events(self) -> list[tuple[float, Any]]:
        """Get all collected events."""
        return list(self.events)

    def get_event_counts(self) -> dict[str, int]:
        """Get event counts (cached)."""
        return self._get_cached('event_counts', lambda: dict(self.event_counts))

    def get_events_by_type(self, event_type: str) -> list[Any]:
        """Get events of specific type."""
        return [e for _, e in self.events if type(e).__name__ == event_type]

    def get_start_time(self) -> float:
        """Get collection start time."""
        return self.start_time

    def get_duration_hours(self) -> float:
        """Get duration in hours from timestamps."""
        if not self.events:
            return 0.0

        timestamps = [ts for ts, _ in self.events]
        if len(timestamps) < 2:
            return (time.time() - self.start_time) / 3600

        duration_seconds = max(timestamps) - min(timestamps)
        return duration_seconds / 3600

    def get_incremental_stats(self) -> dict[str, Any]:
        """Get O(1) incremental statistics."""
        return self.incremental_stats.get_statistics()

    def get_current_state(self) -> dict[str, Any]:
        """Get current system state snapshot."""
        return self.state_tracker.get_current_state()

    def _get_cached(self, key: str, compute_fn: Callable[[], Any]) -> Any:
        """Get cached value or compute."""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return value

        value = compute_fn()
        self._cache[key] = (time.time(), value)
        return value

    def _invalidate_cache(self) -> None:
        """Invalidate cache on new event."""
        self._cache.clear()

    def clear(self) -> None:
        """Clear all collected events."""
        self.events.clear()
        self.event_counts.clear()
        self.incremental_stats.clear()
        self.state_tracker.clear()
        self._cache.clear()
        self.start_time = time.time()
