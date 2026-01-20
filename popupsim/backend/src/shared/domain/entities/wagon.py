"""Wagon entity - shared across all bounded contexts.

This is a shared kernel entity with a unique identity across the entire system.
All contexts reference the same Wagon entity but only use/modify relevant attributes.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class CouplerType(Enum):
    """Coupler type for wagons and locomotives."""

    SCREW = 'screw'
    DAC = 'dac'
    HYBRID = 'hybrid'  # Can couple both SCREW and DAC


class WagonStatus(Enum):
    """Wagon status events."""

    PARKING = 'parking'
    TO_BE_RETROFFITED = 'to_be_retrofitted'
    ON_RETROFIT_TRACK = 'on_retrofit_track'
    MOVING_TO_STATION = 'moving_to_station'
    RETROFITTING = 'retrofitting'
    RETROFITTED = 'retrofitted'
    MOVING = 'moving'
    SELECTING = 'selecting'
    UNKNOWN = 'unknown'
    SELECTED = 'selected'
    REJECTED = 'rejected'


class Wagon(BaseModel):
    """Wagon entity - unique identity across all contexts.

    This is a shared kernel entity. Each context uses only the attributes
    it cares about, but all contexts reference the same wagon instance.
    """

    model_config = {'frozen': False}  # Allow mutations

    id: str = Field(description='Unique identifier for the wagon')
    length: float = Field(gt=0, description='Length of the wagon in meters')
    is_loaded: bool = Field(description='Whether the wagon is loaded')
    track: str | None = Field(default=None, description='ID of the track the wagon is on')
    source_track_id: str | None = Field(default=None, description='Source track when moving')
    destination_track_id: str | None = Field(default=None, description='Destination track when moving')
    arrival_time: datetime | None = Field(default=None, description='Arrival time of the wagon')
    needs_retrofit: bool = Field(description='Whether the wagon needs retrofit')
    retrofit_start_time: float | None = Field(default=None, description='Retrofit start time as counter')
    retrofit_end_time: float | None = Field(default=None, description='Retrofit end time as counter')
    status: WagonStatus = Field(default=WagonStatus.UNKNOWN, description='Status of the wagon')
    coupler_type: CouplerType = Field(default=CouplerType.SCREW, description='Type of coupler on the wagon')
    workshop_id: str | None = Field(default=None, description='ID of the workshop the wagon is assigned to')
    rake_id: str | None = Field(default=None, description='ID of the rake the wagon is assigned to')
    train_id: str | None = Field(default=None, description='ID of the train the wagon arrived with')
    rejection_reason: str | None = Field(default=None, description='Reason for rejection during classification')
    detailed_rejection_reason: str | None = Field(default=None, description='Detailed reason for rejection')
    rejection_time: float | None = Field(default=None, description='Time when wagon was rejected')
    collection_track_id: str | None = Field(default=None, description='Collection track ID for rejected wagons')

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

    # Domain behavior methods

    def assign_to_workshop(self, workshop_id: str) -> None:
        """Assign wagon to workshop for retrofit."""
        if self.status not in [WagonStatus.ON_RETROFIT_TRACK, WagonStatus.TO_BE_RETROFFITED]:
            raise ValueError(f'Wagon {self.id} not ready for workshop assignment (status: {self.status})')

        self.workshop_id = workshop_id
        self.status = WagonStatus.MOVING_TO_STATION

    def start_retrofit(self, start_time: float) -> None:
        """Start retrofit process."""
        if self.status != WagonStatus.MOVING_TO_STATION:
            raise ValueError(f'Wagon {self.id} not at workshop (status: {self.status})')

        self.retrofit_start_time = start_time
        self.status = WagonStatus.RETROFITTING

    def complete_retrofit(self, end_time: float) -> None:
        """Complete retrofit process."""
        if self.status != WagonStatus.RETROFITTING:
            raise ValueError(f'Wagon {self.id} not in retrofit (status: {self.status})')

        self.retrofit_end_time = end_time
        self.coupler_type = CouplerType.DAC
        self.status = WagonStatus.RETROFITTED

    def mark_classified(self) -> None:
        """Mark wagon as classified and ready for retrofit."""
        self.status = WagonStatus.TO_BE_RETROFFITED

    def mark_rejected(self, reason: str) -> None:
        """Mark wagon as rejected during classification."""
        self.status = WagonStatus.REJECTED
        self.rejection_reason = reason

    def can_be_transported(self) -> bool:
        """Check if wagon can be transported."""
        return self.status in [
            WagonStatus.TO_BE_RETROFFITED,
            WagonStatus.ON_RETROFIT_TRACK,
            WagonStatus.RETROFITTED,
            WagonStatus.MOVING_TO_STATION,
        ]

    def move_to_track(self, track_id: str) -> None:
        """Move wagon to specified track."""
        self.track = track_id
        self.status = WagonStatus.MOVING
