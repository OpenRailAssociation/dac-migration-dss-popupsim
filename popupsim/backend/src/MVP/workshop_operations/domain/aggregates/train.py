"""Models and validation logic for train arrivals in train simulations.

This module provides the data models and validation rules for handling
train arrivals within the simulation. It includes functionality to manage
arrival dates, times, and associated wagons, ensuring data integrity
through validation methods.
"""

import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from MVP.workshop_operations.domain.entities.wagon import Wagon

# Configure logging
logger = logging.getLogger(__name__)

TRAIN_DEFAULT_ID = "NO_ID"


class Train(BaseModel):
    """Information about a train arrival with its wagons."""

    train_id: str = Field(
        default=TRAIN_DEFAULT_ID, description="Unique identifier for the train"
    )
    arrival_time: datetime = Field(description="Time of arrival")
    arrival_track: str = Field(description="Track where train arrives")
    wagons: list[Wagon] = Field(description="List of wagons in the train")

    @field_validator("arrival_time", mode="before")
    @classmethod
    def ensure_utc_timezone(cls, v: datetime | str) -> datetime:
        """Ensure datetime has UTC timezone."""
        dt = datetime.fromisoformat(v) if isinstance(v, str) else v
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    @model_validator(mode="after")
    def validate_wagons(self) -> "Train":
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
            msg = f"Train {self.train_id} must have at least one wagon"
            raise ValueError(msg)
        return self
