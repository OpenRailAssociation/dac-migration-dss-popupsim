"""Models and validation logic for train arrivals in train simulations.

This module provides the data models and validation rules for handling
train arrivals within the simulation. It includes functionality to manage
arrival dates, times, and associated wagons, ensuring data integrity
through validation methods.
"""

from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import time
import re

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

from core.i18n import _
from core.logging import Logger
from core.logging import get_logger

from .model_wagon import Wagon

logger: Logger = get_logger(__name__)


class Train(BaseModel):
    """Information about a train arrival with its wagons."""

    train_id: str = Field(description='Unique identifier for the train')
    arrival_date: date = Field(description='Date of arrival')
    arrival_time: time = Field(description='Time of arrival')
    wagons: list[Wagon] = Field(description='List of wagons in the train')

    @property
    def arrival_datetime(self) -> datetime:
        """Combined arrival date and time.

        Returns
        -------
        datetime
            Combined arrival date and time with UTC timezone.
        """
        return datetime.combine(self.arrival_date, self.arrival_time, tzinfo=UTC)

    @model_validator(mode='after')
    def validate_wagons(self) -> 'Train':
        """Ensure train has at least one wagon.

        Returns
        -------
        Train
            Validated train instance.

        Raises
        ------
        ValueError
            If train has no wagons.
        """
        if not self.wagons:
            raise ValueError(_('Train %(train_id)s must have at least one wagon', train_id=self.train_id))
        return self

    @model_validator(mode='before')
    @classmethod
    def validate_and_parse_arrival_time(cls, values: dict) -> dict:
        """Parse and validate arrival_time field, ensuring correct format and type.

        Parameters
        ----------
        values : dict
            Raw field values from validation.

        Returns
        -------
        dict
            Processed values with parsed arrival_time.

        Raises
        ------
        ValueError
            If arrival_time format is invalid.
        """
        data = dict(values)
        arrival_time_value = data.get('arrival_time')

        if arrival_time_value is None or isinstance(arrival_time_value, time):
            data['arrival_time'] = arrival_time_value
        elif isinstance(arrival_time_value, str):
            if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', arrival_time_value):
                raise ValueError(_('arrival_time must be in HH:MM format (00:00-23:59)'))
            hour_str, minute_str = arrival_time_value.split(':')
            data['arrival_time'] = time(int(hour_str), int(minute_str))
        else:
            raise ValueError(_('arrival_time must be a string in HH:MM format or a time object'))

        return data
