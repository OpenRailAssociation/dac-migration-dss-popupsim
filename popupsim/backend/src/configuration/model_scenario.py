"""
Models and validation logic for train simulation configuration and arrivals.

This module defines the data models and validation logic for configuring
train simulation scenarios. It includes validation for scenario parameters
such as date ranges, random seeds, workshop configurations, and file references.
"""

import logging
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .model_route import Route
from .model_train import Train
from .model_workshop import Workshop

# Configure logging
logger = logging.getLogger(__name__)


class ScenarioConfig(BaseModel):
    """
    Configuration model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    workshop configuration, and required file references.
    """

    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the scenario', min_length=1, max_length=50
    )
    start_date: date = Field(description='Simulation start date')
    end_date: date = Field(description='Simulation end date')
    random_seed: Optional[int] = Field(default=None, ge=0, description='Random seed for reproducible simulations')
    workshop: Optional[Workshop] = Field(default=None, description='Workshop configuration with available tracks')
    train_schedule_file: Optional[str] = Field(
        pattern=r'^[a-zA-Z0-9_.-]+$', description='File path to the train schedule file', min_length=1, max_length=50
    )
    train: Optional[List[Train]] = Field(default=None, description='Train configuration')
    routes: Optional[List[Route]] = Field(default=None, description='Route configuration')

    @field_validator('train_schedule_file')
    @classmethod
    def validate_train_schedule_file(cls, v: str) -> str:
        """Validate that the train schedule file has a valid extension."""
        if not v.endswith(('.json', '.csv')):
            raise ValueError(
                f"Invalid file extension for train_schedule_file: '{v}'. Expected one of: .json, .csv, .xlsx"
            )
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'ScenarioConfig':
        """Ensure end_date is after start_date and duration is reasonable."""
        if self.end_date <= self.start_date:
            raise ValueError(
                f'Invalid date range: end_date ({self.end_date}) must be after start_date ({self.start_date}).'
            )
        duration = (self.end_date - self.start_date).days

        if duration > 365:
            logger.warning(
                "Simulation duration of %d days for scenario '%s' may impact performance.", duration, self.scenario_id
            )
        elif duration < 1:
            raise ValueError(f'Simulation duration must be at least 1 day. Current duration: {duration} days.')
        return self
