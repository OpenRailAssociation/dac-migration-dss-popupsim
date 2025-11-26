"""Analytics Observer - observes simulation events for analytics collection."""

from abc import ABC
from abc import abstractmethod
from typing import Protocol

from ..events.base_event import DomainEvent


class AnalyticsObserver(Protocol):
    """Observer protocol for analytics events."""

    def handle_event(self, event: DomainEvent) -> None:
        """Handle domain event."""

    def get_events(self) -> list[DomainEvent]:
        """Get collected events."""


class BaseAnalyticsObserver(ABC):
    """Base analytics observer implementation."""

    @abstractmethod
    def handle_event(self, event: DomainEvent) -> None:
        """Handle domain event."""

    @abstractmethod
    def get_events(self) -> list[DomainEvent]:
        """Get collected events."""


class KPIObserver(BaseAnalyticsObserver):
    """Observer for KPI-related events."""

    def __init__(self) -> None:
        """Initialize KPI observer."""
        self.events: list[DomainEvent] = []

    def handle_event(self, event: DomainEvent) -> None:
        """Handle and store KPI-related events."""
        self.events.append(event)

    def get_events(self) -> list[DomainEvent]:
        """Get collected events."""
        return self.events.copy()

    def clear_events(self) -> None:
        """Clear collected events."""
        self.events.clear()


class MetricsObserver(BaseAnalyticsObserver):
    """Observer for metrics collection events."""

    def __init__(self) -> None:
        """Initialize metrics observer."""
        self.metrics: dict[str, list[DomainEvent]] = {}

    def handle_event(self, event: DomainEvent) -> None:
        """Handle and categorize metrics events."""
        event_type = type(event).__name__
        if event_type not in self.metrics:
            self.metrics[event_type] = []
        self.metrics[event_type].append(event)

    def get_metrics_by_type(self, event_type: str) -> list[DomainEvent]:
        """Get metrics by event type."""
        return self.metrics.get(event_type, []).copy()

    def get_all_metrics(self) -> dict[str, list[DomainEvent]]:
        """Get all collected metrics."""
        return {k: v.copy() for k, v in self.metrics.items()}

    def clear_metrics(self) -> None:
        """Clear collected metrics."""
        self.metrics.clear()

    def get_events(self) -> list[DomainEvent]:
        """Get all events as flat list."""
        events = []
        for event_list in self.metrics.values():
            events.extend(event_list)
        return events
