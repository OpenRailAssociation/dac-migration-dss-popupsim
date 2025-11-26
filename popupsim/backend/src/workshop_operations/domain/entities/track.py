"""Module defining track models models and validation logic.

Defines the TrackType enumeration and the Track configuration model,
including validation methods to ensure data integrity.
"""

from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


class TrackType(Enum):
    """Enumeration of track functions in the workshop.

    Each track serves a specific purpose in the workshop operations.
    """

    LOCOPARKING = 'loco_parking'  # Locomotive parking tracks
    COLLECTION = 'collection'  # Tracks for collecting wagons
    MAINLINE = 'mainline'  # Mainline tracks outside the workshop area
    PARKING = 'parking_area'  # General parking area tracks
    RETROFIT = 'retrofit'  # Tracks specifically for retrofit operations
    RETROFITTED = 'retrofitted'  # Tracks for wagons that have been retrofitted
    WORKSHOP = 'workshop_area'  # General workshop area tracks


class Track(BaseModel):
    """Configuration model for individual workshop tracks.

    Defines track properties including ID, function, capacity, and retrofit timing.
    """

    id: str = Field(min_length=1, description='Track identifier (any non-empty string)')

    type: TrackType = Field(description='Operational function/purpose of the track')

    edges: list[str] = Field(description='List of edge IDs connected to this track')

    valid_from: datetime | None = Field(default=None, description='Start of track validity period')

    valid_to: datetime | None = Field(default=None, description='End of track validity period')

    @model_validator(mode='after')
    def validate_track_by_type_value(self) -> Self:
        """Validate that the track type is a valid TrackType enum member.

        Raises
        ------
        ValueError
            If the provided track type is not a valid TrackType.

        Returns
        -------
        Self
            The validated Track instance.
        """
        try:
            TrackType(self.type)
        except ValueError as err:
            raise ValueError(f'Invalid track type: {self.type}') from err
        return self

    @model_validator(mode='after')
    def validate_edges(self) -> Self:
        """Validate that the edges list is not empty.

        Raises
        ------
        ValueError
            If the edges list is empty.

        Returns
        -------
        Self
            The validated Track instance.
        """
        if not self.edges:
            raise ValueError(f'Edges list cannot be empty for track {self.id}')
        return self
