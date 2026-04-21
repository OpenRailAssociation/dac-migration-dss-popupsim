"""Domain service for track group operations."""

import random

from contexts.railway_infrastructure.domain.aggregates.track_group import TrackGroup
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
from shared.domain.value_objects.selection_strategy import SelectionStrategy


class TrackGroupService:
    """Service for track group operations with occupancy management."""

    def __init__(self, occupancy_repository: TrackOccupancyRepository) -> None:
        """Initialize with repository."""
        self._repository = occupancy_repository
        self._round_robin_index = 0

    def select_track_for_wagon(self, track_group: TrackGroup, wagon_length: float) -> Track | None:
        """Select best track for wagon using group's strategy."""
        available = self._get_available_tracks(track_group, wagon_length)
        if not available:
            return None

        strategy = track_group.selection_strategy
        if strategy == SelectionStrategy.LEAST_OCCUPIED:
            return min(available, key=lambda t: self._repository.get_or_create(t).get_utilization_percentage())
        if strategy == SelectionStrategy.FIRST_AVAILABLE:
            return available[0]
        if strategy == SelectionStrategy.ROUND_ROBIN:
            track = available[self._round_robin_index % len(available)]
            self._round_robin_index += 1
            return track
        if strategy == SelectionStrategy.RANDOM:
            return random.choice(available)  # noqa: S311
        return available[0]  # Default to first available

    def _get_available_tracks(self, track_group: TrackGroup, wagon_length: float) -> list[Track]:
        """Get tracks that can accommodate the wagon."""
        available = []
        for track in track_group.get_all_tracks():
            occupancy = self._repository.get_or_create(track)
            if (
                occupancy.can_accommodate_length(wagon_length)
                and occupancy.can_accommodate_wagon_count()
                and occupancy.find_optimal_position(wagon_length) is not None
            ):
                available.append(track)
        return available

    def try_add_wagon(
        self, track_group: TrackGroup, wagon_id: str, wagon_length: float, timestamp: float
    ) -> tuple[Track | None, bool]:
        """Try to add wagon to group."""
        track = self.select_track_for_wagon(track_group, wagon_length)
        if track is None:
            return (None, False)

        occupancy = self._repository.get_or_create(track)
        position = occupancy.find_optimal_position(wagon_length)
        if position is None:
            return (track, False)

        occupant = TrackOccupant(wagon_id, OccupantType.WAGON, wagon_length, position)
        try:
            occupancy.add_occupant(occupant, timestamp)
            return (track, True)
        except ValueError:
            return (track, False)

    def remove_wagon(self, track_group: TrackGroup, track_id: str, wagon_id: str, timestamp: float) -> bool:
        """Remove wagon from specific track."""
        from uuid import UUID

        track_uuid = UUID(track_id)

        if track_uuid not in track_group.tracks:
            return False

        occupancy = self._repository.get(track_uuid)
        if occupancy is None:
            return False

        removed = occupancy.remove_occupant(wagon_id, timestamp)
        return removed is not None

    def get_group_occupancy(self, track_group: TrackGroup) -> float:
        """Get total occupancy across all tracks in group."""
        total = 0.0
        for track in track_group.get_all_tracks():
            occupancy = self._repository.get_or_create(track)
            total += occupancy.get_current_occupancy_meters()
        return total

    def get_group_utilization(self, track_group: TrackGroup) -> float:
        """Get average utilization across all tracks."""
        if track_group.is_empty():
            return 0.0

        total_util = 0.0
        for track in track_group.get_all_tracks():
            occupancy = self._repository.get_or_create(track)
            total_util += occupancy.get_utilization_percentage()

        return total_util / len(track_group.tracks)

    def is_group_full(self, track_group: TrackGroup, min_length: float = 15.0) -> bool:
        """Check if all tracks in group are full."""
        for track in track_group.get_all_tracks():
            occupancy = self._repository.get_or_create(track)
            if not occupancy.is_full(min_length):
                return False
        return True
