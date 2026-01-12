"""Railway Yard aggregate root for coordinating yard-level operations."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from contexts.railway_infrastructure.domain.aggregates.track_occupancy import TrackOccupancy
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant


@dataclass
class RailwayYard:
    """Aggregate root managing entire yard operations and track coordination.

    Provides yard-level business rules, capacity management, and coordinated
    operations across multiple tracks while maintaining consistency.
    """

    yard_id: str
    name: str
    tracks: dict[str, Track] = field(default_factory=dict)
    _track_occupancies: dict[str, TrackOccupancy] = field(default_factory=dict)
    _max_capacity_percentage: float = 80.0
    _max_concurrent_shunting: int = 3
    _active_shunting_operations: int = 0

    def add_track(self, track: Track) -> None:
        """Add track to yard and initialize occupancy."""
        self.tracks[track.name] = track
        self._track_occupancies[track.name] = TrackOccupancy(track.id, track)

    def get_track_occupancy(self, track_name: str) -> TrackOccupancy | None:
        """Get track occupancy aggregate."""
        return self._track_occupancies.get(track_name)

    def add_occupant_to_track(self, track_name: str, occupant: TrackOccupant, timestamp: float) -> bool:
        """Add occupant to track with yard-level validation."""
        if not self._can_accommodate_occupant(track_name, occupant):
            return False

        occupancy = self._track_occupancies.get(track_name)
        if not occupancy:
            return False

        occupancy.add_occupant(occupant, timestamp)
        return True

    def move_occupant_between_tracks(self, occupant_id: str, from_track: str, to_track: str, timestamp: float) -> bool:
        """Atomic operation to move occupant between tracks."""
        from_occupancy = self._track_occupancies.get(from_track)
        to_occupancy = self._track_occupancies.get(to_track)

        if not from_occupancy or not to_occupancy:
            return False

        # Find occupant in source track
        occupant = None
        for occ in from_occupancy._occupants:
            if occ.id == occupant_id:
                occupant = occ
                break

        if not occupant:
            return False

        # Check if destination can accommodate
        if not self._can_accommodate_occupant(to_track, occupant):
            return False

        # Atomic operation: remove from source, add to destination
        removed = from_occupancy.remove_occupant(occupant_id, timestamp)
        if removed:
            # Find optimal position in destination track
            position = to_occupancy.find_optimal_position(occupant.effective_length)
            if position is not None:
                # Update occupant position
                updated_occupant = TrackOccupant(
                    occupant.id, occupant.type, occupant.length, position, occupant.buffer_space
                )
                to_occupancy.add_occupant(updated_occupant, timestamp)
                return True
            else:
                # Rollback: add back to source track
                from_occupancy.add_occupant(removed, timestamp)

        return False

    def get_yard_utilization(self) -> float:
        """Get overall yard utilization percentage."""
        total_capacity = sum(track.capacity for track in self.tracks.values())
        if total_capacity == 0:
            return 0.0

        total_occupied = sum(occ.get_current_occupancy_meters() for occ in self._track_occupancies.values())

        return (total_occupied / total_capacity) * 100

    def get_available_tracks_for_type(self, track_type: str) -> list[Track]:
        """Get available tracks of specific type with capacity."""
        available = []
        for track in self.tracks.values():
            if track.type.value == track_type:
                occupancy = self._track_occupancies.get(track.name)
                if occupancy and not occupancy.is_full():
                    available.append(track)
        return available

    def can_start_shunting_operation(self) -> bool:
        """Check if yard can accommodate another shunting operation."""
        return self._active_shunting_operations < self._max_concurrent_shunting

    def start_shunting_operation(self) -> bool:
        """Start a shunting operation if capacity allows."""
        if self.can_start_shunting_operation():
            self._active_shunting_operations += 1
            return True
        return False

    def end_shunting_operation(self) -> None:
        """End a shunting operation."""
        if self._active_shunting_operations > 0:
            self._active_shunting_operations -= 1

    def is_yard_at_capacity(self) -> bool:
        """Check if yard has reached maximum capacity threshold."""
        return self.get_yard_utilization() >= self._max_capacity_percentage

    def get_yard_metrics(self) -> dict[str, Any]:
        """Get comprehensive yard metrics."""
        return {
            'yard_id': self.yard_id,
            'total_tracks': len(self.tracks),
            'utilization_percentage': self.get_yard_utilization(),
            'active_shunting_operations': self._active_shunting_operations,
            'at_capacity': self.is_yard_at_capacity(),
            'track_metrics': {
                name: {
                    'occupancy_meters': occ.get_current_occupancy_meters(),
                    'utilization_percentage': occ.get_utilization_percentage(),
                    'wagon_count': occ.get_wagon_count(),
                    'is_full': occ.is_full(),
                }
                for name, occ in self._track_occupancies.items()
            },
        }

    def _can_accommodate_occupant(self, track_name: str, occupant: TrackOccupant) -> bool:
        """Check if occupant can be accommodated considering yard-level constraints."""
        # Check yard capacity limit
        if self.is_yard_at_capacity():
            return False

        # Check track-specific constraints
        occupancy = self._track_occupancies.get(track_name)
        if not occupancy:
            return False

        return occupancy.can_accommodate_length(occupant.effective_length) and occupancy.can_accommodate_wagon_count()
