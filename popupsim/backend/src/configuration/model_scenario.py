"""Models and validation logic for train simulation configuration and arrivals.

This module defines the data models and validation logic for configuring
train simulation scenarios. It includes validation for scenario parameters
such as date ranges, random seeds, workshop configurations, and file references.
"""

from datetime import date

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from core.i18n import _
from core.logging import Logger
from core.logging import get_logger

from .model_route import Route
from .model_train import Train
from .model_workshop import Workshop

logger: Logger = get_logger(__name__)


class ScenarioConfig(BaseModel):
    """Configuration model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    workshop configuration, and required file references.
    """

    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the scenario', min_length=1, max_length=50
    )
    start_date: date = Field(description='Simulation start date')
    end_date: date = Field(description='Simulation end date')
    random_seed: int | None = Field(default=None, ge=0, description='Random seed for reproducible simulations')
    workshop: Workshop | None = Field(default=None, description='Workshop configuration with available tracks')
    train_schedule_file: str | None = Field(
        pattern=r'^[a-zA-Z0-9_.-]+$', description='File path to the train schedule file', min_length=1, max_length=50
    )
    train: list[Train] | None = Field(default=None, description='Train configuration')
    routes: list[Route] | None = Field(default=None, description='Route configuration')

    @field_validator('train_schedule_file')
    @classmethod
    def validate_train_schedule_file(cls, v: str) -> str:
        """Validate that the train schedule file has a valid extension."""
        if not v.endswith(('.json', '.csv')):
            raise ValueError(
                _(
                    "Invalid file extension for train_schedule_file: '%(file)s'. Expected one of: .json, .csv, .xlsx",
                    file=v,
                )
            )
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'ScenarioConfig':
        """Ensure end_date is after start_date and duration is reasonable."""
        if self.end_date <= self.start_date:
            raise ValueError(
                _(
                    'Invalid date range: end_date (%(end_date)s) must be after start_date (%(start_date)s).',
                    end_date=str(self.end_date),
                    start_date=str(self.start_date),
                )
            )
        duration = (self.end_date - self.start_date).days

        if duration > 365:
            logger.warning(
                'Simulation duration may impact performance',
                translate=True,
                duration=duration,
                scenario_id=self.scenario_id,
            )
        elif duration < 1:
            raise ValueError(
                _('Simulation duration must be at least 1 day. Current duration: %(duration)d days.', duration=duration)
            )
        return self
