"""
Models and validation logic for train simulation configuration and arrivals.
"""

import logging
import re
from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# Configure logging
logger = logging.getLogger(__name__)


class WagonInfo(BaseModel):
    """Information about a single wagon."""

    wagon_id: str = Field(description='Unique identifier for the wagon')
    length: float = Field(gt=0, description='Length of the wagon in meters')
    is_loaded: bool = Field(description='Whether the wagon is loaded')
    needs_retrofit: bool = Field(description='Whether the wagon needs retrofit')


class TrainArrival(BaseModel):
    """Information about a train arrival with its wagons."""

    train_id: str = Field(description='Unique identifier for the train')
    arrival_date: date = Field(description='Date of arrival')
    arrival_time: time = Field(description='Time of arrival')
    wagons: List[WagonInfo] = Field(description='List of wagons in the train')

    @property
    def arrival_datetime(self) -> datetime:
        """Combined arrival date and time."""
        return datetime.combine(self.arrival_date, self.arrival_time)

    @model_validator(mode='after')
    def validate_wagons(self) -> 'TrainArrival':
        """Ensure train has at least one wagon."""
        if not self.wagons:
            raise ValueError(f'Train {self.train_id} must have at least one wagon')
        return self

    @model_validator(mode='before')
    @classmethod
    def validate_and_parse_arrival_time(cls, values):  # pylint: disable=E0213
        """Parse and validate arrival_time field, ensuring correct format and type."""
        data = dict(values)
        arrival_time_value = data.get('arrival_time')

        if arrival_time_value is None or isinstance(arrival_time_value, time):
            data['arrival_time'] = arrival_time_value
        elif isinstance(arrival_time_value, str):
            if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', arrival_time_value):
                raise ValueError('arrival_time must be in HH:MM format (00:00-23:59)')
            hour_str, minute_str = arrival_time_value.split(':')
            data['arrival_time'] = time(int(hour_str), int(minute_str))
        else:
            raise ValueError('arrival_time must be a string in HH:MM format or a time object')

        return data


class ScenarioConfig(BaseModel):
    """
    Configuration model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    and required file references.
    """

    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the scenario', min_length=1, max_length=50
    )
    start_date: date = Field(description='Simulation start date')
    end_date: date = Field(description='Simulation end date')
    random_seed: Optional[int] = Field(default=None, ge=0, description='Random seed for reproducible simulations')
    train_schedule_file: str = Field(description='Path to the train schedule file', min_length=1)

    @field_validator('train_schedule_file')
    @classmethod
    def validate_train_schedule_file(cls, v: str) -> str:  # pylint: disable=E0213
        """Validate that the train schedule file has a valid extension."""
        if not v.endswith(('.json', '.csv', '.xlsx')):
            raise ValueError(
                f"Invalid file extension for train_schedule_file: '{v}'. Expected one of: .json, .csv, .xlsx"
            )
        return v

    # mode="after" gives you the constructed instance (Field),
    # so you can safely compare self.end_date and self.start_date.
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
