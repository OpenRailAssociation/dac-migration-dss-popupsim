"""
Models and validation logic for train simulation configuration and arrivals.

This module defines the data models and validation logic for configuring
train simulation scenarios. It includes validation for scenario parameters
such as date ranges, random seeds, workshop configurations, and file references.
"""

import logging

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class Track(BaseModel):
    """
    Model representing a workshop track.

    Each track has a unique identifier, capacity for trains,
    and a retrofit time in minutes.
    """

    id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the track', min_length=1, max_length=20
    )
    capacity: int = Field(
        gt=0, description='Maximum number of trains that can be processed simultaneously on this track'
    )
    retrofit_time_min: int = Field(
        gt=0, description='Time in minutes required to complete retrofit operations on this track'
    )
