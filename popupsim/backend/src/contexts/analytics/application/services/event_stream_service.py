"""Event stream application service."""
# pylint: disable=duplicate-code
import time
from typing import Any

from contexts.analytics.domain.entities.metrics_aggregator import MetricsAggregator
from contexts.analytics.domain.services.event_collection_service import EventCollectionService
from contexts.analytics.domain.services.track_occupancy_tracker import TrackOccupancyTracker
from infrastructure.event_bus.event_bus import EventBus
from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent


class EventStreamService:
    """Application service for event stream management."""

    def __init__(
        self,
        event_bus: EventBus,
        collector: EventCollectionService | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.collector = collector or EventCollectionService(event_bus)
        self.track_occupancy = TrackOccupancyTracker()
        self._subscribe_to_all_events()
        self._subscribe_to_wagon_events()
        self._wagon_tracks = {}

    def _subscribe_to_all_events(self) -> None:
        """Subscribe to all domain events."""
        self.collector.subscribe_to_all_events(self.collector.collect_event)

    def _subscribe_to_wagon_events(self) -> None:
        """Subscribe to wagon movement events for track occupancy."""
        self.event_bus.subscribe(TrainArrivedEvent, self._handle_train_arrived)
        # Subscribe to all events to track wagon movements
        self.collector.subscribe_to_all_events(self._track_wagon_locations)

    def _handle_train_arrived(self, event: Any) -> None:
        """Handle train arrived event."""
        if hasattr(event, 'arrival_track') and hasattr(event, 'wagons'):
            for _ in event.wagons:
                self.track_occupancy.record_wagon_arrival(event.arrival_track, event.event_timestamp)

    def _track_wagon_locations(self, event: Any) -> None:
        """Track wagon locations from all events."""
        if hasattr(event, 'wagon') and hasattr(event, 'event_timestamp'):
            wagon = event.wagon
            if hasattr(wagon, 'track'):
                track = wagon.track
                if track and track not in ['', 'unknown']:
                    wagon_id = wagon.id
                    if wagon_id not in self._wagon_tracks or self._wagon_tracks[wagon_id] != track:
                        if wagon_id in self._wagon_tracks:
                            old_track = self._wagon_tracks[wagon_id]
                            self.track_occupancy.record_wagon_departure(old_track, event.event_timestamp)
                        self.track_occupancy.record_wagon_arrival(track, event.event_timestamp)
                        self._wagon_tracks[wagon_id] = track

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

    def get_all_events(self) -> list[tuple[float, Any]]:
        """Get all collected events with timestamps.

        Returns
        -------
        list[tuple[float, Any]]
            List of (timestamp, event) tuples.
        """
        return self.collector.get_events()

    def get_event_counts(self) -> dict[str, int]:
        """Get count of each event type.

        Returns
        -------
        dict[str, int]
            Event type name to count mapping.
        """
        return self.collector.get_event_counts()

    def get_duration_hours(self) -> float:
        """Get simulation duration in hours.

        Returns
        -------
        float
            Duration in hours since start.
        """
        start_time = self.collector.get_start_time()
        if start_time == 0.0:
            return 0.0
        return (time.time() - start_time) / 3600.0

    def get_current_state(self) -> dict[str, Any]:
        """Get current system state from state tracking.

        Returns
        -------
        dict[str, Any]
            Current state snapshot including:
            - wagons_retrofitting: Number of wagons currently being retrofitted
            - wagons_on_retrofit_track: Number of wagons on retrofit tracks
            - wagons_on_retrofitted_track: Number of wagons on retrofitted tracks
            - workshop_states: Workshop utilization states
            - locomotive_action_breakdown: Locomotive activity breakdown
            - track_occupancy: Track occupancy information
        """
        return self.collector.get_current_state()
