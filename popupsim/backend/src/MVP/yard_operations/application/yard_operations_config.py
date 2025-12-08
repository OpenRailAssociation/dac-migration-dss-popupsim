"""Configuration for Yard Operations Context."""

from dataclasses import dataclass

from MVP.workshop_operations.domain.entities.track import Track
from MVP.workshop_operations.domain.services.wagon_operations import (
    WagonSelector,
    WagonStateManager,
)
from MVP.workshop_operations.infrastructure.resources.track_capacity_manager import (
    TrackCapacityManager,
)
from MVP.workshop_operations.infrastructure.resources.workshop_capacity_manager import (
    WorkshopCapacityManager,
)


@dataclass
class YardOperationsConfig:
    """Configuration for Yard Operations Context.

    Parameters
    ----------
    track_capacity : TrackCapacityManager
        Track capacity manager for yard tracks
    wagon_state : WagonStateManager
        Service for managing wagon state transitions
    wagon_selector : WagonSelector
        Service for determining if wagon needs retrofit
    workshop_capacity : WorkshopCapacityManager
        Workshop capacity manager for checking availability
    parking_tracks : list[Track]
        Available parking tracks
    """

    track_capacity: TrackCapacityManager
    wagon_state: WagonStateManager
    wagon_selector: WagonSelector
    workshop_capacity: WorkshopCapacityManager
    parking_tracks: list[Track]
