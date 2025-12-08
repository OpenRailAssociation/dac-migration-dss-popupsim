"""Track entity for railway infrastructure."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum


class TrackType(Enum):
    """Track types in railway infrastructure."""

    LOCOPARKING = 'loco_parking'
    COLLECTION = 'collection'
    MAINLINE = 'mainline'
    PARKING = 'parking_area'
    RETROFIT = 'retrofit'
    RETROFITTED = 'retrofitted'
    WORKSHOP = 'workshop_area'


@dataclass
class Track:
    """Track entity with capacity management."""

    track_id: str
    track_type: TrackType
    total_length: float
    fill_factor: float = 0.75
    _current_occupancy: float = field(default=0.0, init=False, repr=False)

    @property
    def capacity(self) -> float:
        """Get effective capacity based on fill factor."""
        return self.total_length * self.fill_factor

    @property
    def current_occupancy(self) -> float:
        """Get current occupancy."""
        return self._current_occupancy

    @property
    def available_capacity(self) -> float:
        """Get available capacity."""
        return self.capacity - self._current_occupancy

    @property
    def utilization_percentage(self) -> float:
        """Get utilization as percentage."""
        return (self._current_occupancy / self.capacity * 100) if self.capacity > 0 else 0.0

    def can_accommodate(self, length: float) -> bool:
        """Check if track can accommodate given length."""
        return self._current_occupancy + length <= self.capacity

    def add_wagon(self, wagon_length: float) -> None:
        """Add wagon to track."""
        if not self.can_accommodate(wagon_length):
            msg = (
                f'Track {self.track_id} cannot accommodate wagon of length {wagon_length}. '
                f'Available: {self.available_capacity}, Required: {wagon_length}'
            )
            raise ValueError(msg)
        self._current_occupancy += wagon_length

    def remove_wagon(self, wagon_length: float) -> None:
        """Remove wagon from track."""
        self._current_occupancy = max(0.0, self._current_occupancy - wagon_length)

    def is_empty(self) -> bool:
        """Check if track is empty."""
        return self._current_occupancy == 0.0

    def is_full(self) -> bool:
        """Check if track is at capacity."""
        return self._current_occupancy >= self.capacity
