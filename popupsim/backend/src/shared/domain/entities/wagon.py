"""Wagon entity - shared across all bounded contexts.

This is a shared kernel entity with a unique identity across the entire system.
All contexts reference the same Wagon entity but only use/modify relevant attributes.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CouplerType(Enum):
    """Coupler type for wagons and locomotives."""

    SCREW = "screw"
    DAC = "dac"
    HYBRID = "hybrid"  # Can couple both SCREW and DAC


class WagonStatus(Enum):
    """Wagon status events."""

    PARKING = "parking"
    TO_BE_RETROFFITED = "to_be_retrofitted"
    ON_RETROFIT_TRACK = "on_retrofit_track"
    MOVING_TO_STATION = "moving_to_station"
    RETROFITTING = "retrofitting"
    RETROFITTED = "retrofitted"
    MOVING = "moving"
    SELECTING = "selecting"
    UNKNOWN = "unknown"
    SELECTED = "selected"
    REJECTED = "rejected"


class Wagon(BaseModel):
    """Wagon entity - unique identity across all contexts.

    This is a shared kernel entity. Each context uses only the attributes
    it cares about, but all contexts reference the same wagon instance.
    """

    id: str = Field(description="Unique identifier for the wagon")
    length: float = Field(gt=0, description="Length of the wagon in meters")
    is_loaded: bool = Field(description="Whether the wagon is loaded")
    track: str | None = Field(
        default=None, description="ID of the track the wagon is on"
    )
    source_track_id: str | None = Field(
        default=None, description="Source track when moving"
    )
    destination_track_id: str | None = Field(
        default=None, description="Destination track when moving"
    )
    arrival_time: datetime | None = Field(
        default=None, description="Arrival time of the wagon"
    )
    needs_retrofit: bool = Field(description="Whether the wagon needs retrofit")
    retrofit_start_time: float | None = Field(
        default=None, description="Retrofit start time as counter"
    )
    retrofit_end_time: float | None = Field(
        default=None, description="Retrofit end time as counter"
    )
    status: WagonStatus = Field(
        default=WagonStatus.UNKNOWN, description="Status of the wagon"
    )
    coupler_type: CouplerType = Field(
        default=CouplerType.SCREW, description="Type of coupler on the wagon"
    )

    @property
    def waiting_time(self) -> float | None:
        """Calculate the waiting time between arrival and retrofit start.

        Returns
        -------
        float | None
            Waiting time in seconds if both arrival_time and retrofit_start_time are set,
            None otherwise.
        """
        if self.arrival_time is not None and self.retrofit_start_time is not None:
            arrival_timestamp: float = self.arrival_time.timestamp()
            return self.retrofit_start_time - arrival_timestamp
        return None
