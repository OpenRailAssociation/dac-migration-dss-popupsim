"""Track occupancy aggregate root for position-aware occupancy management."""

from dataclasses import dataclass
from dataclasses import field
from uuid import UUID

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackAccess
from contexts.railway_infrastructure.domain.value_objects.occupancy_snapshot import OccupancySnapshot
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant


@dataclass
class TrackOccupancy:
    """Aggregate root managing all occupancy state for a single track.

    Provides position-aware occupancy management with collision detection
    and optimal space allocation.
    """

    track_id: UUID | str
    track_specification: Track
    _occupants: list[TrackOccupant] = field(default_factory=list)
    _occupancy_history: list[OccupancySnapshot] = field(default_factory=list)

    def add_occupant(self, occupant: TrackOccupant, timestamp: float) -> None:
        """Add occupant to track with collision detection."""
        if not self._can_accommodate(occupant):
            raise ValueError('Occupant overlaps with existing occupant')

        self._occupants.append(occupant)
        self._occupants.sort(key=lambda x: x.position_start)  # Keep sorted by position
        self._record_snapshot(timestamp)

    def remove_occupant(self, occupant_id: str, timestamp: float) -> TrackOccupant | None:
        """Remove occupant by ID."""
        for i, occupant in enumerate(self._occupants):
            if occupant.id == occupant_id:
                removed = self._occupants.pop(i)
                self._record_snapshot(timestamp)
                return removed
        return None

    def can_accommodate_length(self, required_length: float) -> bool:
        """Check if track can accommodate required length."""
        available = self.get_available_capacity()
        return available >= required_length

    def can_accommodate_wagon_count(self) -> bool:
        """Check if track can accommodate one more wagon (for workshop tracks)."""
        if self.track_specification.max_wagons is None:
            return True
        return self.get_wagon_count() < self.track_specification.max_wagons

    def find_optimal_position(self, required_length: float) -> float | None:
        """Find position respecting track access direction (simple position-based)."""
        # Check if track can accommodate the length first
        if not self.can_accommodate_length(required_length):
            return None

        # For empty track, start at position 0
        if not self._occupants:
            return 0.0

        # Sort occupants by position
        sorted_occupants = sorted(self._occupants, key=lambda x: x.position_start)

        # Check track access constraints
        can_add_front = self.track_specification.access in (TrackAccess.FRONT_ONLY, TrackAccess.BOTH_ENDS)
        can_add_rear = self.track_specification.access in (TrackAccess.REAR_ONLY, TrackAccess.BOTH_ENDS)

        # Try front (position 0) if allowed and space available
        if can_add_front and sorted_occupants[0].position_start >= required_length:
            return 0.0

        # Try rear (end of track) if allowed and space available
        if can_add_rear:
            last_end = sorted_occupants[-1].position_start + sorted_occupants[-1].effective_length
            if self.track_specification.capacity - last_end >= required_length:
                return last_end

        return None  # No valid position available

    def get_current_occupancy_meters(self) -> float:
        """Get total occupied length in meters."""
        return sum(occ.effective_length for occ in self._occupants)

    def get_current_occupancy_percentage(self) -> float:
        """Get occupancy as percentage of track capacity."""
        if self.track_specification.capacity == 0:
            return 0.0
        return (self.get_current_occupancy_meters() / self.track_specification.capacity) * 100

    def get_available_capacity(self) -> float:
        """Get available capacity in meters."""
        return self.track_specification.capacity - self.get_current_occupancy_meters()

    def get_wagon_count(self) -> int:
        """Get current wagon count on track."""
        return len([occ for occ in self._occupants if occ.type.value == 'wagon'])

    def get_utilization_percentage(self) -> float:
        """Get utilization percentage (alias for occupancy percentage)."""
        return self.get_current_occupancy_percentage()

    def is_empty(self) -> bool:
        """Check if track has no occupants."""
        return len(self._occupants) == 0

    def is_full(self, min_length: float = 15.0) -> bool:
        """Check if track cannot accommodate minimum length."""
        return not self.can_accommodate_length(min_length) or not self.can_accommodate_wagon_count()

    def _can_accommodate(self, occupant: TrackOccupant) -> bool:
        """Check if occupant can be accommodated (length + position + count)."""
        # Check length capacity
        if not self.can_accommodate_length(occupant.effective_length):
            return False

        # Check wagon count for workshop tracks
        if not self.can_accommodate_wagon_count():
            return False

        # Check position availability
        return self._has_position_available(occupant)

    def _has_position_available(self, occupant: TrackOccupant) -> bool:
        """Check if occupant's position doesn't collide with existing occupants."""
        occupant_end = occupant.position_start + occupant.effective_length

        # Check track bounds
        if occupant.position_start < 0 or occupant_end > self.track_specification.capacity:
            return False

        # Check collisions with existing occupants
        for existing in self._occupants:
            existing_end = existing.position_start + existing.effective_length

            # Check overlap
            if not (occupant_end <= existing.position_start or occupant.position_start >= existing_end):
                return False

        return True

    def _record_snapshot(self, timestamp: float) -> None:
        """Record current state snapshot for audit trail."""
        snapshot = OccupancySnapshot(
            timestamp=timestamp,
            occupancy_meters=self.get_current_occupancy_meters(),
            occupancy_percentage=self.get_current_occupancy_percentage(),
            occupant_count=len(self._occupants),
            occupants=tuple(self._occupants),  # Immutable snapshot
        )
        self._occupancy_history.append(snapshot)
