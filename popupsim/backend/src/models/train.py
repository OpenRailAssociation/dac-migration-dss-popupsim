"""Models and validation logic for train arrivals in train simulations.

This module provides the data models and validation rules for handling
train arrivals within the simulation. It includes functionality to manage
arrival dates, times, and associated wagons, ensuring data integrity
through validation methods.
"""

from datetime import datetime
import logging

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

from .wagon import Wagon

# Configure logging
logger = logging.getLogger(__name__)

TRAIN_DEFAULT_ID = 'NO_ID'


class Train(BaseModel):
    """Information about a train arrival with its wagons."""

    train_id: str = Field(default=TRAIN_DEFAULT_ID, description='Unique identifier for the train')
    arrival_time: datetime = Field(description='Time of arrival')
    wagons: list[Wagon] = Field(description='List of wagons in the train')

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
            raise ValueError(f'Train {self.train_id} must have at least one wagon')
        return self
