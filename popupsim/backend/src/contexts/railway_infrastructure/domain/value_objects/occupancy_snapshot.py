"""Occupancy snapshot value object for audit trail."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant


@dataclass(frozen=True)
class OccupancySnapshot:
    """Point-in-time occupancy state for audit trail."""

    timestamp: float
    occupancy_meters: float
    occupancy_percentage: float
    occupant_count: int
    occupants: tuple['TrackOccupant', ...]  # Immutable snapshot
