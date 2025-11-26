"""Event Publisher - manages observers and publishes domain events."""

from ..events.base_event import DomainEvent
from .analytics_observer import AnalyticsObserver


class EventPublisher:
    """Publisher for domain events using observer pattern."""

    def __init__(self) -> None:
        """Initialize event publisher."""
        self._observers: list[AnalyticsObserver] = []

    def subscribe(self, observer: AnalyticsObserver) -> None:
        """Subscribe observer to events."""
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: AnalyticsObserver) -> None:
        """Unsubscribe observer from events."""
        if observer in self._observers:
            self._observers.remove(observer)

    def publish(self, event: DomainEvent) -> None:
        """Publish event to all observers."""
        for observer in self._observers:
            observer.handle_event(event)

    def get_observer_count(self) -> int:
        """Get number of subscribed observers."""
        return len(self._observers)

    def clear_observers(self) -> None:
        """Clear all observers."""
        self._observers.clear()
