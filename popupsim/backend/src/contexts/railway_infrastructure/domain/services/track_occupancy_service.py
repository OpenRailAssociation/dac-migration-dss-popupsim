"""Unified track occupancy domain service."""

from uuid import UUID

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant


class TrackOccupancyService:
    """Domain service for high-level track occupancy operations."""

    def __init__(self, repository: TrackOccupancyRepository) -> None:
        """Initialize with repository."""
        self._repository = repository

    def allocate_wagon(self, track: Track, wagon_id: str, wagon_length: float, timestamp: float) -> bool:
        """Allocate wagon to track with optimal positioning."""
        occupancy = self._repository.get_or_create(track)

        if not occupancy.can_accommodate_length(wagon_length) or not occupancy.can_accommodate_wagon_count():
            return False

        position = occupancy.find_optimal_position(wagon_length)
        if position is None:
            return False

        occupant = TrackOccupant(id=wagon_id, type=OccupantType.WAGON, length=wagon_length, position_start=position)

        try:
            occupancy.add_occupant(occupant, timestamp)
            return True
        except ValueError:
            return False

    def deallocate_wagon(self, track: Track, wagon_id: str, timestamp: float) -> bool:
        """Remove wagon from track."""
        occupancy = self._repository.get(track.id)
        if occupancy is None:
            return False

        removed = occupancy.remove_occupant(wagon_id, timestamp)
        return removed is not None

    def allocate_rake(self, track: Track, rake_id: str, rake_length: float, timestamp: float) -> bool:
        """Allocate entire rake to track."""
        occupancy = self._repository.get_or_create(track)

        if not occupancy.can_accommodate_length(rake_length):
            return False

        position = occupancy.find_optimal_position(rake_length)
        if position is None:
            return False

        occupant = TrackOccupant(
            id=rake_id,
            type=OccupantType.RAKE,
            length=rake_length,
            position_start=position,
            buffer_space=2.0,  # Inter-rake spacing
        )

        try:
            occupancy.add_occupant(occupant, timestamp)
            return True
        except ValueError:
            return False

    def can_accommodate(self, track: Track, required_length: float) -> bool:
        """Check if track can accommodate required length."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.can_accommodate_length(required_length) and occupancy.can_accommodate_wagon_count()

    def get_current_occupancy(self, track: Track) -> float:
        """Get current occupancy in meters."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.get_current_occupancy_meters()

    def get_available_capacity(self, track: Track) -> float:
        """Get available capacity in meters."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.get_available_capacity()

    def get_utilization_percentage(self, track: Track) -> float:
        """Get utilization percentage."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.get_utilization_percentage()

    def get_wagon_count(self, track: Track) -> int:
        """Get current wagon count."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.get_wagon_count()

    def is_empty(self, track: Track) -> bool:
        """Check if track is empty."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.is_empty()

    def is_full(self, track: Track, min_length: float = 15.0) -> bool:
        """Check if track is full."""
        occupancy = self._repository.get_or_create(track)
        return occupancy.is_full(min_length)

    def reset_track(self, track_id: UUID) -> None:
        """Reset specific track occupancy."""
        self._repository.reset(track_id)

    def reset_all_tracks(self) -> None:
        """Reset all track occupancies."""
        self._repository.reset()
