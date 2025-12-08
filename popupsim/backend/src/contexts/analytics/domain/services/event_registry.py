"""Event registry for dynamic event discovery."""

from collections.abc import Callable
from typing import Any


class EventRegistry:
    """Registry for domain events across all contexts."""

    def __init__(self) -> None:
        self._event_types: list[type[Any]] = []
        self._discovery_functions: list[Callable[[], list[type[Any]]]] = []

    def register_event(self, event_type: type[Any]) -> None:
        """Register a single event type."""
        if event_type not in self._event_types:
            self._event_types.append(event_type)

    def register_events(self, event_types: list[type[Any]]) -> None:
        """Register multiple event types."""
        for event_type in event_types:
            self.register_event(event_type)

    def register_discovery_function(self, func: Callable[[], list[type[Any]]]) -> None:
        """Register a function that discovers events from a context."""
        self._discovery_functions.append(func)

    def discover_all_events(self) -> list[type[Any]]:
        """Discover all registered events by calling discovery functions."""
        for func in self._discovery_functions:
            try:
                discovered = func()
                self.register_events(discovered)
            except ImportError:
                pass
        return self._event_types

    def get_all_events(self) -> list[type[Any]]:
        """Get all registered event types."""
        return self._event_types.copy()

    def clear(self) -> None:
        """Clear all registered events."""
        self._event_types.clear()
