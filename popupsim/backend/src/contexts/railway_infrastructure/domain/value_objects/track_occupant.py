"""Definition of the TrackOccupant value object."""

from dataclasses import dataclass
from enum import Enum


class OccupantType(Enum):
    """Enumerationd efining the different occupant types."""

    WAGON = 'wagon'
    RAKE = 'rake'
    LOCOMOTIVE = 'locomotive'


@dataclass(frozen=True)
class TrackOccupant:
    """Value object representing anything that occupies track space."""

    id: str
    type: OccupantType
    length: float
    position_start: float
    buffer_space: float = 0.0

    @property
    def position_end(self) -> float:
        """Position on the track where the occupant ends.

        Returns
        -------
        float
            Position where the occupant ends.
        """
        return self.position_start + self.length

    @property
    def effective_length(self) -> float:
        """Total space consumed including buffers.

        Returns
        -------
        float
            Effective length of the track occupant.
        """
        return self.length + self.buffer_space
