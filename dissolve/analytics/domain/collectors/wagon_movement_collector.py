"""Collector for wagon movement events."""

from typing import Any

from analytics.domain.collectors.base import MetricCollector, MetricResult
from analytics.domain.events.base_event import DomainEvent
from analytics.domain.events.simulation_events import WagonArrivedEvent, WagonMovedEvent


class WagonMovementCollector(MetricCollector):
    """Collects wagon movement and arrival events for timeline visualization."""

    def __init__(self) -> None:
        """Initialize wagon movement collector."""
        self.movements: list[dict[str, Any]] = []
        self.arrivals: list[dict[str, Any]] = []

    def record_event(self, event: DomainEvent) -> None:
        """Collect wagon movement events.

        Parameters
        ----------
        event : DomainEvent
            Domain event to collect.
        """
        if isinstance(event, WagonMovedEvent):
            self.movements.append(
                {
                    "timestamp": event.timestamp.value,
                    "wagon_id": event.wagon_id,
                    "from_track": event.from_track,
                    "to_track": event.to_track,
                    "transport_duration": event.transport_duration,
                }
            )
        elif isinstance(event, WagonArrivedEvent):
            self.arrivals.append(
                {
                    "timestamp": event.timestamp.value,
                    "wagon_id": event.wagon_id,
                    "track_id": event.track_id,
                    "wagon_status": event.wagon_status,
                }
            )

    def get_results(self) -> list[MetricResult]:
        """Get metric results for MetricCollector interface.

        Returns
        -------
        list[MetricResult]
            Empty list - this collector provides timeline data via get_movement_timeline().
        """
        return []

    def reset(self) -> None:
        """Reset collector state."""
        self.movements.clear()
        self.arrivals.clear()

    def get_movement_timeline(self) -> dict[str, list[dict[str, Any]]]:
        """Get wagon movement timeline by wagon ID.

        Returns
        -------
        dict[str, list[dict[str, Any]]]
            Timeline of movements and arrivals for each wagon.
        """
        timeline: dict[str, list[dict[str, Any]]] = {}

        # Combine movements and arrivals, sort by timestamp
        all_events = []

        for movement in self.movements:
            all_events.append(
                {
                    "type": "movement_start",
                    "timestamp": movement["timestamp"],
                    "wagon_id": movement["wagon_id"],
                    "from_track": movement["from_track"],
                    "to_track": movement["to_track"],
                }
            )

        for arrival in self.arrivals:
            all_events.append(
                {
                    "type": "arrival",
                    "timestamp": arrival["timestamp"],
                    "wagon_id": arrival["wagon_id"],
                    "track_id": arrival["track_id"],
                    "wagon_status": arrival["wagon_status"],
                }
            )

        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])

        # Group by wagon ID
        for event in all_events:
            wagon_id = event["wagon_id"]
            if wagon_id not in timeline:
                timeline[wagon_id] = []
            timeline[wagon_id].append(event)

        return timeline
