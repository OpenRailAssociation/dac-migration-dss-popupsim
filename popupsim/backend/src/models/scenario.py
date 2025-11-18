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

from .route import Route
from .track import Track
from .train import Train
from .workshop import Workshop

# Configure logging
logger = logging.getLogger(__name__)


class ScenarioConfig(BaseModel):
    """Configuration model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    workshop models, and required file references.
    Timezone for start_date and end_date is enforced to be UTC in the validators.
    """

    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the scenario', min_length=1, max_length=50
    )
    start_date: datetime = Field(description='Simulation start date')
    end_date: datetime = Field(description='Simulation end date')
    # Make model attribute an int (always set) but allow None during input via the before validator
    random_seed: int = Field(default=0, ge=0, description='Random seed for reproducible simulations')
    # TODO: should be a list
    workshop: Workshop | None = Field(default=None, description='Workshop models with available tracks')
    # Todo: should be a wagons list
    train_schedule_file: str = Field(
        pattern=r'^[a-zA-Z0-9_.-]+$', description='File path to the train schedule file', min_length=1, max_length=50
    )  # TODO: make it a Path
    routes_file: str | None = Field(
        default=None, pattern=r'^[a-zA-Z0-9_.-]+$', description='File path to routes file', min_length=1, max_length=50
    )
    tracks_file: str | None = Field(
        default=None,
        pattern=r'^[a-zA-Z0-9_.-]+$',
        description='File path to workshop tracks file',
        min_length=1,
        max_length=50,
    )  # TODO: make it a Path
    routes: list[Route] | None = Field(default=None, description='Route models')
    trains: list[Train] | None = Field(default=None, description='Train models')
    tracks: list[Track] | None = Field(default=None, description='Track models')

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def ensure_utc_timezone(cls, v: datetime | str) -> datetime:
        """Ensure datetime has UTC timezone."""
        dt = datetime.fromisoformat(v) if isinstance(v, str) else v

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    @field_validator('random_seed', mode='before')
    @classmethod
    def validate_random_seed(cls, v: int | None) -> int:
        """Ensure random_seed is never None, defaulting to 0 if None or omitted."""
        if v is None:
            logger.debug('random_seed was None or omitted, defaulting to 0')
            return 0
        if not isinstance(v, int):
            raise ValueError(f'random_seed must be an integer, got {type(v).__name__}')
        if v < 0:
            raise ValueError(f'random_seed must be non-negative, got {v}')
        return v

    @field_validator('train_schedule_file')
    @classmethod
    def validate_train_schedule_file(cls, v: str) -> str:
        """Validate that the train schedule file has a valid extension."""
        if not v.endswith(('.json', '.csv')):
            raise ValueError(f"Invalid file extension for train_schedule_file: '{v}'. Expected one of: .json, .csv")
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'ScenarioConfig':
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
