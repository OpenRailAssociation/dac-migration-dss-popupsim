"""Event subscription service - focused on managing subscriptions."""

from collections.abc import Callable
from typing import Any

from infrastructure.event_bus.event_bus import EventBus

from .event_discoverers import get_all_discoverers
from .event_registry import EventRegistry


class EventSubscriptionService:
    """Manages event subscriptions to event bus."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.event_registry = EventRegistry()
        self._initialize_registry()

    def _initialize_registry(self) -> None:
        """Initialize registry with all discoverers."""
        for discoverer in get_all_discoverers():
            self.event_registry.register_discovery_function(discoverer)

    def subscribe_to_all_events(self, handler: Callable[[Any], None]) -> None:
        """Subscribe handler to all discovered events."""
        event_types = self.event_registry.discover_all_events()
        for event_type in event_types:
            self.event_bus.subscribe(event_type, handler)

    def subscribe_to_event(
        self, event_type: type[Any], handler: Callable[[Any], None]
    ) -> None:
        """Subscribe handler to specific event type."""
        self.event_registry.register_event(event_type)
        self.event_bus.subscribe(event_type, handler)

    def get_registered_event_types(self) -> list[type[Any]]:
        """Get all registered event types."""
        return self.event_registry.get_all_events()
