"""Scenario model for configuration context."""

from collections.abc import Sequence
from datetime import datetime
from datetime import timedelta
from enum import Enum
import logging
from typing import Any

from contexts.configuration.application.dtos import LocomotiveInputDTO
from contexts.configuration.application.dtos import RouteInputDTO
from contexts.configuration.application.dtos import TrackInputDTO
from contexts.configuration.application.dtos import WorkshopInputDTO
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from shared.value_objects.timezone_utils import ensure_utc
from shared.value_objects.timezone_utils import validate_timezone_aware

from .process_times import ProcessTimes

logger = logging.getLogger(__name__)


class TrackSelectionStrategy(str, Enum):
    """Strategy for selecting tracks."""

    ROUND_ROBIN = 'round_robin'
    LEAST_OCCUPIED = 'least_occupied'
    FIRST_AVAILABLE = 'first_available'
    RANDOM = 'random'


class LocoDeliveryStrategy(str, Enum):
    """Strategy for locomotive delivery."""

    RETURN_TO_PARKING = 'return_to_parking'
    DIRECT_DELIVERY = 'direct_delivery'


class LocoPriorityStrategy(str, Enum):
    """Strategy for locomotive task prioritization."""

    WORKSHOP_PRIORITY = 'workshop_priority'  # Park wagons immediately when loco available
    BATCH_COMPLETION = 'batch_completion'  # Complete workshop pickups before parking


class Scenario(BaseModel):
    """Scenario configuration for simulation."""

    id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$', min_length=1, max_length=50)
    start_date: datetime
    end_date: datetime
    track_selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED
    retrofit_selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED
    workshop_selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.ROUND_ROBIN
    parking_selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED
    loco_delivery_strategy: LocoDeliveryStrategy = LocoDeliveryStrategy.RETURN_TO_PARKING
    loco_priority_strategy: LocoPriorityStrategy = LocoPriorityStrategy.WORKSHOP_PRIORITY
    locomotives: list[LocomotiveInputDTO] | None = None
    process_times: ProcessTimes | None = None
    routes: list[RouteInputDTO] | None = None
    topology: Any = None
    trains: Any | None = None
    tracks: Sequence[TrackInputDTO] = []
    workshops: list[WorkshopInputDTO] | None = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def ensure_utc_timezone_validator(cls, v: datetime | str) -> datetime:
        """Ensure datetime has UTC timezone."""
        return ensure_utc(v)

    @model_validator(mode='after')
    def validate_dates(self) -> 'Scenario':
        """Validate date range."""
        validate_timezone_aware(self.start_date, 'start_date')
        validate_timezone_aware(self.end_date, 'end_date')

        if self.end_date <= self.start_date:
            msg = f'Invalid date range: end_date ({self.end_date}) must be after start_date ({self.start_date}).'
            raise ValueError(msg)
        duration: int = (self.end_date - self.start_date).days

        if duration > 365:
            logger.warning(
                "Simulation duration of %d days for scenario '%s' may impact performance.",
                duration,
                self.id,
            )
        return self

    @property
    def duration(self) -> timedelta:
        """Get simulation duration."""
        return self.end_date - self.start_date

    @property
    def duration_hours(self) -> float:
        """Get simulation duration in hours."""
        return self.duration.total_seconds() / 3600.0

    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes for SimPy."""
        return self.duration.total_seconds() / 60.0

    def validate_simulation_requirements(self) -> 'Scenario':
        """Validate scenario has required resources for simulation."""
        if not self.locomotives:
            msg = 'Scenario must have at least one locomotive'
            raise ValueError(msg)
        if not self.trains:
            msg = 'Scenario must have at least one train'
            raise ValueError(msg)
        if not self.tracks or not self.topology:
            msg = 'Scenario must have tracks and topology'
            raise ValueError(msg)

        return self

    model_config = {'arbitrary_types_allowed': True}
