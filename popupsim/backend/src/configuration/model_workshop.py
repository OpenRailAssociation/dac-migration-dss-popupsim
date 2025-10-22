"""
This module provides models and validation logic for configuring
train simulation scenarios and managing train arrivals.

It includes classes and methods to define and validate the structure
of simulation configurations, ensuring data integrity and consistency.
"""

import logging
from typing import List

from pydantic import BaseModel, Field, field_validator

from .model_track import Track

# Configure logging
logger = logging.getLogger(__name__)


class Workshop(BaseModel):
    """
    Model representing the workshop configuration.

    Contains all available tracks for train processing.
    """

    tracks: List[Track] = Field(min_length=1, description='List of available tracks in the workshop')

    @field_validator('tracks')
    @classmethod
    def validate_unique_track_ids(cls, v: List[Track]) -> List[Track]:
        """Ensure all track IDs are unique."""
        track_ids = [track.id for track in v]
        if len(track_ids) != len(set(track_ids)):
            duplicates = [id for id in track_ids if track_ids.count(id) > 1]
            raise ValueError(f'Duplicate track IDs found: {list(set(duplicates))}')
        return v
