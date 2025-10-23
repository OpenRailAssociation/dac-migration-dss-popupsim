"""
Module defining track configuration models and validation logic.

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

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class TrackFunction(Enum):
    """
    Enumeration of track functions in the workshop.

    Each track serves a specific purpose in the workshop operations.
    """

    WERKSTATTGLEIS = 'werkstattgleis'  # Main retrofit tracks where DAC installation happens
    SAMMELGLEIS = 'sammelgleis'  # Collection tracks for grouping trains
    PARKGLEIS = 'parkgleis'  # Parking tracks for temporary storage
    WERKSTATTZUFUEHRUNG = 'werkstattzufuehrung'  # Feeder tracks leading to workshop
    WERKSTATTABFUEHRUNG = 'werkstattabfuehrung'  # Exit tracks leaving workshop
    BAHNHOFSKOPF = 'bahnhofskopf'  # Station head tracks


class WorkshopTrackConfig(BaseModel):
    """
    Configuration model for individual workshop tracks.

    Defines track properties including ID, function, capacity, and retrofit timing.
    """

    id: str = Field(
        min_length=7, max_length=7, pattern=r'^TRACK\d{2}$', description='Track identifier in format TRACK01-TRACK99'
    )

    function: TrackFunction = Field(description='Operational function/purpose of the track')

    capacity: int = Field(gt=0, description='Maximum number of wagons/trains the track can hold')

    retrofit_time_min: int = Field(ge=0, description='Time in minutes required for retrofit operations on this track')

    @model_validator(mode='after')
    def validate_retrofit_time_by_function(self) -> Self:
        """
        Validate retrofit time based on track function.

        Business Rules:
        - Werkstattgleis tracks must have retrofit_time_min > 0 (actual retrofit work)
        - All other track functions must have retrofit_time_min = 0 (no retrofit work)
        """
        if self.function == TrackFunction.WERKSTATTGLEIS:
            if self.retrofit_time_min <= 0:
                raise ValueError(f'Track {self.id}: retrofit_time_min must be > 0 for werkstattgleis tracks')
        else:
            if self.retrofit_time_min != 0:
                raise ValueError(f'Track {self.id}: retrofit_time_min must be 0 unless function is werkstattgleis')

        return self
