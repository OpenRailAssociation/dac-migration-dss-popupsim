"""Example usage of track capacity monitoring."""

from contexts.analytics.application.analytics_context import (
    AnalyticsContext,
)
from contexts.analytics.infrastructure.repositories.in_memory_analytics_repository import (
    InMemoryAnalyticsRepository,
)
from infrastructure.event_bus.event_bus import EventBus


def example_track_capacity_monitoring() -> None:
    """Demonstrate track capacity monitoring."""
    # Setup
    event_bus = EventBus()
    repository = InMemoryAnalyticsRepository()

    # Mock TrackConfig (in real simulation, this comes from configuration context)
    class MockTrackConfig:
        def __init__(self, id: str, length: float) -> None:
            self.id = id
            self.length = length

    track_configs = [
        MockTrackConfig("retrofit_track_1", 666.0),
        MockTrackConfig("retrofit_track_2", 800.0),
        MockTrackConfig("retrofitted_track_1", 1066.0),
        MockTrackConfig("parking_track_1", 533.0),
    ]

    # Capacity calculated as: length * fill_factor (default 0.75)
    context = AnalyticsContext(event_bus, repository, track_configs, fill_factor=0.75)

    # Start session
    context.start_session("track_capacity_demo")

    # Simulate wagon distribution events
    # (In real simulation, these would come from yard operations)
    class WagonDistributedEvent:
        def __init__(
            self, wagon_id: str, track_id: str, wagon_length: float, timestamp: float
        ) -> None:
            self.wagon_id = wagon_id
            self.track_id = track_id
            self.wagon_length = wagon_length
            self.timestamp = timestamp

    # Distribute wagons to tracks
    event_bus.publish(
        WagonDistributedEvent("wagon_001", "retrofit_track_1", 15.0, 100.0)
    )
    event_bus.publish(
        WagonDistributedEvent("wagon_002", "retrofit_track_1", 18.0, 105.0)
    )
    event_bus.publish(
        WagonDistributedEvent("wagon_003", "retrofit_track_2", 20.0, 110.0)
    )
    event_bus.publish(
        WagonDistributedEvent("wagon_004", "retrofit_track_1", 16.0, 115.0)
    )

    # Get track metrics (capacities calculated from track length * fill_factor)
    track_metrics = context.get_track_metrics()

    for _metrics in track_metrics["tracks"].values():
        pass

    # Get current system state
    state = context.get_current_state()
    for _track_id, _info in state["track_occupancy"].items():
        pass

    context.end_session()


if __name__ == "__main__":
    example_track_capacity_monitoring()
