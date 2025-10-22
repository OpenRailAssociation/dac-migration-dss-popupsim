"""
This module defines the models and validation logic for wagon information
used in train simulations. It provides a structure for representing
individual wagons, including their unique identifiers, physical attributes,
and specific requirements such as loading status and retrofit needs.
"""

import logging

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class WagonInfo(BaseModel):
    """Information about a single wagon."""

    wagon_id: str = Field(description='Unique identifier for the wagon')
    length: float = Field(gt=0, description='Length of the wagon in meters')
    is_loaded: bool = Field(description='Whether the wagon is loaded')
    needs_retrofit: bool = Field(description='Whether the wagon needs retrofit')
