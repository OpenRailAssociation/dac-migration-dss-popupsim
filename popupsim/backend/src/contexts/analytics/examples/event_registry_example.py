"""Example usage of EventRegistry for dynamic event subscription."""

from typing import Any

from contexts.analytics.domain.entities.event_stream_collector import (
    EventStreamCollector,
)
from contexts.analytics.domain.services.event_discoverers import (
    get_all_discoverers,
)
from contexts.analytics.domain.services.event_registry import (
    EventRegistry,
)
from infrastructure.event_bus.event_bus import EventBus


def example_default_usage() -> None:
    """Example: Use default event discovery."""
    event_bus = EventBus()

    # EventStreamCollector automatically discovers all events
    collector = EventStreamCollector(event_bus)

    # All events from all contexts are now subscribed
    collector.compute_statistics()


def example_custom_registry() -> None:
    """Example: Create custom registry with selective contexts."""
    event_bus = EventBus()
    registry = EventRegistry()

    # Only subscribe to specific contexts
    from contexts.analytics.domain.services.event_discoverers import (
        discover_shared_events,
        discover_yard_events,
    )

    registry.register_discovery_function(discover_shared_events)
    registry.register_discovery_function(discover_yard_events)

    EventStreamCollector(event_bus, registry)


def example_runtime_registration() -> None:
    """Example: Register custom events at runtime."""
    event_bus = EventBus()
    collector = EventStreamCollector(event_bus)

    # Define custom event
    class CustomAnalyticsEvent:
        def __init__(self, metric: str, value: float) -> None:
            self.metric = metric
            self.value = value

    # Register at runtime
    collector.register_custom_event(CustomAnalyticsEvent)

    # Publish custom event
    event_bus.publish(CustomAnalyticsEvent("custom_metric", 42.0))

    # Event is now tracked
    collector.compute_statistics()


def example_manual_registry() -> None:
    """Example: Manually build registry without discoverers."""
    event_bus = EventBus()
    registry = EventRegistry()

    # Manually register specific events
    from shared.domain.events.wagon_lifecycle_events import (
        TrainArrivedEvent,
        WagonClassifiedEvent,
    )

    registry.register_events([TrainArrivedEvent, WagonClassifiedEvent])

    EventStreamCollector(event_bus, registry)


def example_add_custom_discoverer() -> None:
    """Example: Add custom discovery function."""
    event_bus = EventBus()
    registry = EventRegistry()

    # Custom discoverer for future context
    def discover_future_context_events() -> list[type[Any]]:
        try:
            from some_future_context.events import FutureEvent

            return [FutureEvent]
        except ImportError:
            return []

    # Register all default discoverers
    for discoverer in get_all_discoverers():
        registry.register_discovery_function(discoverer)

    # Add custom discoverer
    registry.register_discovery_function(discover_future_context_events)

    EventStreamCollector(event_bus, registry)


if __name__ == "__main__":
    example_default_usage()

    example_custom_registry()

    example_runtime_registration()

    example_manual_registry()

    example_add_custom_discoverer()
