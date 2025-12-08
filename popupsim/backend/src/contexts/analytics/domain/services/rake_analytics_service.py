"""Rake analytics service for tracking rake formations and movements."""

from dataclasses import dataclass
from typing import Any

from shared.domain.entities.rake import Rake
from shared.domain.value_objects.rake_type import RakeType


@dataclass
class RakeSnapshot:  # pylint: disable=too-many-instance-attributes
    """Snapshot of rake state at a specific time."""

    timestamp: float
    rake_id: str
    rake_type: RakeType
    track: str
    wagon_count: int
    wagon_ids: list[str]
    total_length: float
    status: str  # 'formed', 'transporting', 'processing', 'completed'


@dataclass
class RakeFormationEvent:
    """Event capturing rake formation details."""

    timestamp: float
    rake_id: str
    formation_track: str
    target_track: str
    wagon_count: int
    formation_strategy: str
    workshop_capacity_used: int


class RakeAnalyticsService:
    """Service for collecting and analyzing rake formation data."""

    def __init__(self) -> None:
        self.rake_snapshots: list[RakeSnapshot] = []
        self.formation_events: list[RakeFormationEvent] = []
        self.track_occupancy: dict[str, list[tuple[float, int]]] = {}  # track -> [(time, wagon_count)]

    def record_rake_formation(self, timestamp: float, rake: Rake, strategy: str, workshop_capacity: int = 0) -> None:
        """Record rake formation event."""
        event = RakeFormationEvent(
            timestamp=timestamp,
            rake_id=rake.rake_id,
            formation_track=rake.formation_track,
            target_track=rake.target_track or 'unknown',
            wagon_count=rake.wagon_count,
            formation_strategy=strategy,
            workshop_capacity_used=workshop_capacity,
        )
        self.formation_events.append(event)

        # Record initial snapshot
        self._record_rake_snapshot(timestamp, rake, 'formed')

        # Update track occupancy
        self._update_track_occupancy(rake.formation_track, timestamp, rake.wagon_count)

    def record_rake_transport(self, timestamp: float, rake: Rake, from_track: str, to_track: str) -> None:
        """Record rake transport between tracks."""
        self._record_rake_snapshot(timestamp, rake, 'transporting')

        # Update track occupancy (remove from source, add to destination)
        self._update_track_occupancy(from_track, timestamp, -rake.wagon_count)
        self._update_track_occupancy(to_track, timestamp, rake.wagon_count)

    def record_rake_processing(self, timestamp: float, rake: Rake, status: str) -> None:
        """Record rake processing status change."""
        self._record_rake_snapshot(timestamp, rake, status)

    def _record_rake_snapshot(self, timestamp: float, rake: Rake, status: str) -> None:
        """Record rake state snapshot."""
        snapshot = RakeSnapshot(
            timestamp=timestamp,
            rake_id=rake.rake_id,
            rake_type=rake.rake_type,
            track=rake.formation_track,
            wagon_count=rake.wagon_count,
            wagon_ids=rake.wagon_ids,
            total_length=rake.total_length,
            status=status,
        )
        self.rake_snapshots.append(snapshot)

    def _update_track_occupancy(self, track: str, timestamp: float, wagon_delta: int) -> None:
        """Update track occupancy over time."""
        if track not in self.track_occupancy:
            self.track_occupancy[track] = [(0.0, 0)]

        # Get current occupancy
        current_occupancy = self.track_occupancy[track][-1][1] if self.track_occupancy[track] else 0
        new_occupancy = max(0, current_occupancy + wagon_delta)

        self.track_occupancy[track].append((timestamp, new_occupancy))

    def get_rake_formations_by_time(self) -> list[RakeFormationEvent]:
        """Get rake formations sorted by time."""
        return sorted(self.formation_events, key=lambda x: x.timestamp)

    def get_track_occupancy_timeline(self, track: str) -> list[tuple[float, int]]:
        """Get wagon count over time for specific track."""
        return self.track_occupancy.get(track, [])

    def get_rake_size_distribution(self) -> dict[int, int]:
        """Get distribution of rake sizes."""
        size_counts: dict[int, int] = {}
        for event in self.formation_events:
            size = event.wagon_count
            size_counts[size] = size_counts.get(size, 0) + 1
        return size_counts

    def get_formation_strategy_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics by formation strategy."""
        strategy_stats: dict[str, Any] = {}

        for event in self.formation_events:
            strategy = event.formation_strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'count': 0,
                    'total_wagons': 0,
                    'avg_size': 0.0,
                    'capacity_utilization': [],
                }

            stats = strategy_stats[strategy]
            stats['count'] += 1
            stats['total_wagons'] += event.wagon_count
            stats['avg_size'] = stats['total_wagons'] / stats['count']

            if event.workshop_capacity_used > 0:
                utilization = event.wagon_count / event.workshop_capacity_used
                stats['capacity_utilization'].append(utilization)

        return strategy_stats

    def get_rake_timeline_for_track(self, track: str) -> list[RakeSnapshot]:
        """Get all rake events for specific track over time."""
        track_snapshots = [snapshot for snapshot in self.rake_snapshots if snapshot.track == track]
        return sorted(track_snapshots, key=lambda x: x.timestamp)

    def get_concurrent_rakes_at_time(self, timestamp: float) -> list[RakeSnapshot]:
        """Get all active rakes at specific timestamp."""
        active_rakes = []

        # Group snapshots by rake_id
        rake_timelines: dict[str, list[RakeSnapshot]] = {}
        for snapshot in self.rake_snapshots:
            if snapshot.rake_id not in rake_timelines:
                rake_timelines[snapshot.rake_id] = []
            rake_timelines[snapshot.rake_id].append(snapshot)

        # Find active rakes at timestamp
        for timeline in rake_timelines.values():
            timeline.sort(key=lambda x: x.timestamp)

            # Find latest snapshot before or at timestamp
            latest_snapshot = None
            for snapshot in timeline:
                if snapshot.timestamp <= timestamp:
                    latest_snapshot = snapshot
                else:
                    break

            if latest_snapshot and latest_snapshot.status not in [
                'completed',
                'departed',
            ]:
                active_rakes.append(latest_snapshot)

        return active_rakes
