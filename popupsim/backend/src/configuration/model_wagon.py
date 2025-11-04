"""Models and validation logic for wagon information.

This module defines the models and validation logic for wagon information
used in train simulations. It provides a structure for representing
individual wagons, including their unique identifiers, physical attributes,
and specific requirements such as loading status and retrofit needs.
"""

from pydantic import BaseModel
from pydantic import Field

from core.logging import Logger
from core.logging import get_logger

logger: Logger = get_logger(__name__)


class Wagon(BaseModel):
    """Information about a single wagon."""

    wagon_id: str = Field(description='Unique identifier for the wagon')
    train_id: str = Field(description='ID of the train this wagon belongs to')
    length: float = Field(gt=0, description='Length of the wagon in meters')
    is_loaded: bool = Field(description='Whether the wagon is loaded')
    needs_retrofit: bool = Field(description='Whether the wagon needs retrofit')
    arrival_time: float | None = Field(default=None, description='Arrival time of the wagon')
    retrofit_start_time: float | None = Field(default=None, description='Retrofit start time')
    retrofit_end_time: float | None = Field(default=None, description='Retrofit end time')
    track_id: str | None = Field(default=None, description='ID of the track the wagon is on')

    @property
    def waiting_time(self) -> float | None:
        """Calculate the waiting time between arrival and retrofit start.

        Returns
        -------
            Optional[float]: Waiting time in minutes if both arrival_time and
                retrofit_start_time are set, None otherwise.

        """
        if self.arrival_time is not None and self.retrofit_start_time is not None:
            return self.retrofit_start_time - self.arrival_time
        return None
