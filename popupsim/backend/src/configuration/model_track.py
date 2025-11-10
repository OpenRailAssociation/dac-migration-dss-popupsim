"""Module defining track configuration models and validation logic.

Key Features:
- **Track Configuration**: Defines the structure of workshop tracks with properties like capacity and function.
- **Track Function Enum**: Categorizes tracks by their operational purpose.
- **Validation Logic**: Ensures track configurations meet business rules:
  - Valid track ID format (TRACK01-TRACK99)
  - Positive capacity values
  - Proper retrofit time constraints based on track function
  - Werkstattgleis tracks must have retrofit_time_min > 0
  - Non-werkstattgleis tracks must have retrofit_time_min = 0
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

    BAHNHOFSKOPF_1 = 'station_head_1'  # Station head track 1
    BAHNHOFSKOPF_N = 'station_head_n'  # Station head track n
    CIRCULATING_TRACK = 'circulating_track'  # Circulating/loop tracks
    CONNECTION_TRACK = 'connection_track'  # Connection tracks between main tracks
    DISPENSER = 'dispenser'  # Dispenser tracks for wagon distribution
    DISPENSER_2_CONTROL = 'dispenser_2_control'  # Dispenser with 2-way control
    PARKGLEIS = 'parking'  # Parking tracks for temporary storage
    RESOURCE_PARKING = 'shunting_parking'  # Track designated for parking shunting locomotives (resources)
    SAMMELGLEIS = 'collection'  # Collection tracks for grouping trains
    SELECTOR = 'selector'  # Selector/hump tracks for sorting
    TO_PARKING_CONTROL = 'to_parking_control'  # Control tracks to parking areas
    WERKSTATTGLEIS = 'workshop'  # Main retrofit tracks where DAC installation happens (werkstattgleis in German)
    WERKSTATTZUFUEHRUNG = 'to_be_retroffitted'  # Feeder tracks leading to workshop (awaiting retrofit)
    WERKSTATTABFUEHRUNG = 'retrofitted'  # Exit tracks leaving workshop (retrofit completed)


class Track(BaseModel):
    """Configuration model for individual workshop tracks.

    Defines track properties including ID, function, capacity, and retrofit timing.
    """

    id: str = Field(min_length=1, description='Track identifier (any non-empty string)')

    length: float = Field(gt=0, description='Length of the track in meters')

    type: TrackType = Field(description='Operational function/purpose of the track')

    capacity: int | None = Field(
        default=None, ge=1, description='Maximum number of trains that can occupy the track simultaneously'
    )

    sh_1: int = Field(default=0, ge=0, description='Hub position 1')

    sh_n: int = Field(default=0, ge=0, description='Hub position n')

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
    def validate_validity_period(self) -> Self:
        """Validate that valid_from is before valid_to when both are provided.

        Raises
        ------
        ValueError
            If valid_from is after valid_to.

        Returns
        -------
        Self
            The validated Track instance.
        """
        if self.valid_from is not None and self.valid_to is not None and self.valid_from >= self.valid_to:
            raise ValueError(
                f'Invalid validity period for track {self.id}: '
                f'valid_from ({self.valid_from}) must be before valid_to ({self.valid_to})'
            )
        return self
