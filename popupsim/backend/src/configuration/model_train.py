"""
Models and validation logic for train arrivals in train simulations.

This module provides the data models and validation rules for handling
train arrivals within the simulation. It includes functionality to manage
arrival dates, times, and associated wagons, ensuring data integrity
through validation methods.
"""

import logging
import re
from datetime import date, datetime, time
from typing import List

from pydantic import BaseModel, Field, model_validator

from .model_wagon import WagonInfo

# Configure logging
logger = logging.getLogger(__name__)


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
