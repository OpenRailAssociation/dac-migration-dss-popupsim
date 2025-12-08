"""Event stream collector - orchestrates event collection and analysis."""

from typing import Any

from contexts.analytics.domain.entities.metrics_aggregator import (
    MetricsAggregator,
)
from contexts.analytics.domain.services.event_collection_service import (
    EventCollectionService,
)
from infrastructure.event_bus.event_bus import EventBus


class EventStreamCollector:
    """Orchestrates event collection from all contexts."""

    def __init__(self, event_bus: EventBus) -> None:
        self.collector = EventCollectionService(event_bus)
        self._subscribe_to_all_events()

    def _subscribe_to_all_events(self) -> None:
        """Subscribe to all domain events."""
        self.collector.subscribe_to_all_events(self.collector.collect_event)

    def register_custom_event(self, event_type: type[Any]) -> None:
        """Register and subscribe to custom event type."""
        self.collector.subscribe_to_event(event_type, self.collector.collect_event)

    def compute_statistics(self) -> dict[str, Any]:
        """Compute all statistics from collected events."""
        aggregator = MetricsAggregator(
            self.collector.get_events(),
            self.collector.get_event_counts(),
            self.collector.get_start_time(),
        )
        return aggregator.compute_all_metrics()

    def get_events_by_type(self, event_type: str) -> list[Any]:
        """Get events of specific type."""
        return self.collector.get_events_by_type(event_type)

    def clear(self) -> None:
        """Clear all collected events."""
        self.collector.clear()
