"""Models and validation logic for railway route configurations.

This module provides data models and validation rules for handling
railway routes within the simulation. It includes functionality to manage
route details such as origin/destination tracks, track sequences, distances,
and travel times.
"""

import logging
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

# Configure logging
logger = logging.getLogger(__name__)


class Route(BaseModel):
    """Information about a railway route between tracks.

    Routes are defined by a path (sequence of track IDs). The from_track and to_track
    are automatically derived as the first and last tracks in the path.
    """

    route_id: str = Field(description='Unique identifier for the route', alias='id')
    path: list[str] = Field(description='Sequence of track IDs forming the complete route')
    description: str | None = Field(default=None, description='Optional description of the route')
    duration: int | None = Field(default=None, description='Optional travel time in minutes')

    @field_validator('path', mode='before')
    @classmethod
    def parse_path(cls, value: Any) -> list[str]:
        """Parse path from string to list if needed."""
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            if not value or value.strip() == '':
                raise ValueError('path cannot be an empty string')
            # Remove quotes and split by comma
            cleaned_value: str = value.strip('"\'')
            parsed_path: list[str] = [track.strip() for track in cleaned_value.split(',')]
            return parsed_path

        raise ValueError(f'path must be a list or comma-separated string, got {type(value)}')

    @model_validator(mode='after')
    def validate_route(self) -> 'Route':
        """Validate route integrity."""
        # Check if path is empty
        if not self.path:
            raise ValueError(f'Route {self.route_id} must have a valid path')

        # Check minimum length - route needs at least start and end track
        if len(self.path) < 2:
            raise ValueError(f'Route {self.route_id} must have at least two tracks in path')

        return self

    @property
    def from_track(self) -> str:
        """Get the starting track ID (first track in path)."""
        return self.path[0]

    @property
    def to_track(self) -> str:
        """Get the ending track ID (last track in path)."""
        return self.path[-1]

    @property
    def track_sequence(self) -> list[str]:
        """Get the complete track sequence (alias for path)."""
        return self.path

    model_config = ConfigDict(populate_by_name=True)  # Allow both 'id' and 'route_id'
