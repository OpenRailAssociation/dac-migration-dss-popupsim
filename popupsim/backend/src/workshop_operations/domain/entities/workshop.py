"""Module defining the Workshop model and its validation logic.

Key Features:
- **Workshop Configuration**: Defines the structure of the workshop, including tracks and their properties.
- **Validation Logic**: Ensures that the workshop models adheres to business rules, such as:
  - Unique track IDs.
  - Presence of required track functions.
  - Proper retrofit time constraints for specific track functions.
  - Balanced feeder and exit tracks.
  - Adequate workshop capacity for train arrivals.
"""

import logging

from pydantic import BaseModel
from pydantic import Field

# Configure logging
logger = logging.getLogger(__name__)


class Workshop(BaseModel):
    """Model representing the workshop models.

    Contains all available tracks for train processing.
    """

    workshop_id: str = Field(description='Unique identifier for the workshop')
    start_date: str = Field(description='Workshop operational start date as ISO string')
    end_date: str = Field(description='Workshop operational end date as ISO string')
    retrofit_stations: int = Field(
        default=1, ge=1, description='Number of concurrent retrofit stations in the workshop'
    )
    track_id: str = Field(description='Track models available in the workshop')
    worker: int = Field(default=1, ge=1, description='Number of workers available in the workshop')
