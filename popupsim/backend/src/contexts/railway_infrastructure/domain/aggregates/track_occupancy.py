"""Track occupancy aggregate root with wagon queue management."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from uuid import UUID

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackAccess
from contexts.railway_infrastructure.domain.value_objects.occupancy_snapshot import OccupancySnapshot
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
from contexts.railway_infrastructure.domain.value_objects.track_wagon_queue import TrackWagonQueue


@dataclass
class TrackOccupancy:
    """Aggregate root managing occupancy state and wagon queue for a single track.

    Combines position-aware occupancy management with wagon sequence tracking.
    """

    track_id: UUID | str
    track_specification: Track
    _occupants: list[TrackOccupant] = field(default_factory=list)
    _occupancy_history: list[OccupancySnapshot] = field(default_factory=list)
    _wagon_queue: TrackWagonQueue = field(init=False)

    def __post_init__(self) -> None:
        """Initialize wagon queue after dataclass initialization."""
        self._wagon_queue = TrackWagonQueue(str(self.track_id))

    def add_wagon(self, wagon: Any, timestamp: float) -> None:
        """Add wagon to both occupancy and queue."""
        # Find optimal position for occupancy tracking
        position = self.find_optimal_position(wagon.length)
        if position is None:
            raise ValueError(f'No space for wagon {wagon.id}')

        # Add to occupancy tracking
        occupant = TrackOccupant(id=wagon.id, type=OccupantType.WAGON, length=wagon.length, position_start=position)
        self.add_occupant(occupant, timestamp)

        # Add to sequence queue
        self._wagon_queue.add_wagon(wagon)

    def remove_wagon(self, wagon_id: str, timestamp: float) -> Any | None:
        """Remove wagon from both occupancy and queue."""
        # Remove from occupancy
        self.remove_occupant(wagon_id, timestamp)

        # Remove from queue
        return self._wagon_queue.remove_wagon(wagon_id)

    def get_wagons_in_sequence(self) -> list[Any]:
        """Get wagons in arrival sequence."""
        return self._wagon_queue.get_wagons()

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
        """Find position using simple sequential filling from track access point.

        For railway operations, wagons are typically added sequentially from one end.
        This implements a simple, robust algorithm that respects track access constraints.
        """
        # Check if track can accommodate the length first
        if not self.can_accommodate_length(required_length):
            return None

        # For empty track, start at position 0 (standard railway practice)
        if not self._occupants:
            return 0.0

        # Sort occupants by position for sequential processing
        sorted_occupants = sorted(self._occupants, key=lambda x: x.position_start)

        # Determine filling direction based on track access
        # Most collection tracks fill from front (position 0) sequentially
        if self.track_specification.access in (TrackAccess.FRONT_ONLY, TrackAccess.BOTH_ENDS):
            # Fill from front: find the end of the last occupant and add there
            last_occupant_end = max(occ.position_start + occ.effective_length for occ in sorted_occupants)

            # Check if there's space at the end
            if last_occupant_end + required_length <= self.track_specification.capacity:
                return last_occupant_end

        # If front filling failed or track is REAR_ONLY, try rear filling
        if self.track_specification.access in (TrackAccess.REAR_ONLY, TrackAccess.BOTH_ENDS):
            # Fill from rear: find space before the first occupant
            first_occupant_start = min(occ.position_start for occ in sorted_occupants)

            # Check if there's space at the beginning
            if first_occupant_start >= required_length:
                return first_occupant_start - required_length

        return None  # No space available

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
        """Check if track has no wagons."""
        return len(self._occupants) == 0

    def is_full(self, min_length: float = 15.0) -> bool:
        """Check if track cannot accommodate minimum length."""
        return not self.can_accommodate_length(min_length) or not self.can_accommodate_wagon_count()

    def get_occupants(self) -> list[TrackOccupant]:
        """Get list of current occupants."""
        return self._occupants.copy()

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
