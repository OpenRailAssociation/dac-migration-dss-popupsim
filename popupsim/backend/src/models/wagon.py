"""Models and validation logic for wagon information.

This module defines the models and validation logic for wagon information
used in train simulations. It provides a structure for representing
individual wagons, including their unique identifiers, physical attributes,
and specific requirements such as loading status and retrofit needs.
"""

from datetime import datetime
import logging

from pydantic import BaseModel
from pydantic import Field

# Configure logging
logger = logging.getLogger(__name__)


class Wagon(BaseModel):
    """Information about a single wagon."""

    wagon_id: str = Field(description='Unique identifier for the wagon')
    length: float = Field(gt=0, description='Length of the wagon in meters')
    is_loaded: bool = Field(description='Whether the wagon is loaded')
    # TODO: decide if track_id is needed
    track_id: str | None = Field(default=None, description='ID of the track the wagon is on')
    arrival_time: datetime | None = Field(default=None, description='Arrival time of the wagon')
    needs_retrofit: bool = Field(description='Whether the wagon needs retrofit')
    retrofit_start_time: float | None = Field(default=None, description='Retrofit start time as counter')
    retrofit_end_time: float | None = Field(default=None, description='Retrofit end time as counter')

    @property
    def waiting_time(self) -> float | None:
        """Calculate the waiting time between arrival and retrofit start.

        Returns
        -------
        float | None
            Waiting time in seconds if both arrival_time and retrofit_start_time are set,
            None otherwise.
        """
        if self.arrival_time is not None and self.retrofit_start_time is not None:
            arrival_timestamp: float = self.arrival_time.timestamp()
            return self.retrofit_start_time - arrival_timestamp
        return None
