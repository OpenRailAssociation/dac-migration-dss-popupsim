"""Models and validation logic for train simulation models and arrivals.

This module defines the data models and validation logic for configuring
train simulation scenarios. It includes validation for scenario parameters
such as date ranges, random seeds, workshop configurations, and file references.
"""

from datetime import UTC
from datetime import datetime
import logging

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from typing import Any

from .locomotive import Locomotive
from .process_times import ProcessTimes
from .route import Route
from .track import Track
from .train import Train
from .workshop import Workshop

# Configure logging
logger = logging.getLogger(__name__)


class Scenario(BaseModel):
    """Scenario model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    workshop models, and required file references.
    Timezone for start_date and end_date is enforced to be UTC in the validators.
    """

    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the scenario', min_length=1, max_length=50
    )
    start_date: datetime = Field(description='Simulation start date')
    end_date: datetime = Field(description='Simulation end date')
    locomotives: list[Locomotive] | None = Field(default=None, description='Locomotive models')
    process_times: ProcessTimes | None = Field(default=None, description='Process timing configuration')
    routes: list[Route] | None = Field(default=None, description='Route models')
    topology: Any = Field(default=None, description='Topology model')
    trains: list[Train] | None = Field(default=None, description='Train models')
    tracks: list[Track] | None = Field(default=None, description='Track models')
    workshops: list[Workshop] | None = Field(default=None, description='Workshop models with available tracks')

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def ensure_utc_timezone(cls, v: datetime | str) -> datetime:
        """Ensure datetime has UTC timezone."""
        dt = datetime.fromisoformat(v) if isinstance(v, str) else v

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    @model_validator(mode='after')
    def validate_dates(self) -> 'Scenario':
        """Ensure end_date is after start_date and duration is reasonable."""
        if self.end_date <= self.start_date:
            raise ValueError(
                f'Invalid date range: end_date ({self.end_date}) must be after start_date ({self.start_date}).'
            )
        duration: int = (self.end_date - self.start_date).days

        if duration > 365:
            logger.warning(
                "Simulation duration of %d days for scenario '%s' may impact performance.", duration, self.scenario_id
            )
        elif duration < 1:
            raise ValueError(f'Simulation duration must be at least 1 day. Current duration: {duration} days.')
        return self
    
    model_config = {'arbitrary_types_allowed': True}
