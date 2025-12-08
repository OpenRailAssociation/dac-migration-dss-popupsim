"""Base class for operational areas within a yard."""

from enum import Enum

from MVP.workshop_operations.domain.entities.track import Track


class AreaType(str, Enum):
    """Types of operational areas within a yard."""

    CLASSIFICATION = "classification"
    PARKING = "parking"
    RETROFITTING = "retrofitting"
    MAINTENANCE = "maintenance"
    INTERCHANGE = "interchange"


class YardArea:
    """Base class for operational areas within a yard.

    Parameters
    ----------
    area_id : str
        Unique identifier for the area
    area_type : AreaType
        Type of operational area
    tracks : list[Track]
        Tracks assigned to this area
    """

    def __init__(self, area_id: str, area_type: AreaType, tracks: list[Track]) -> None:
        self.area_id = area_id
        self.area_type = area_type
        self.tracks = tracks

    def get_track_ids(self) -> list[str]:
        """Get list of track IDs in this area.

        Returns
        -------
        list[str]
            List of track IDs
        """
        return [track.id for track in self.tracks]

    def has_capacity(self) -> bool:
        """Check if area has available capacity.

        Returns
        -------
        bool
            True if area has capacity, False otherwise
        """
        return len(self.tracks) > 0
