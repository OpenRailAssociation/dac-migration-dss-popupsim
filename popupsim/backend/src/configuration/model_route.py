"""
Models and validation logic for railway route configurations.

This module provides data models and validation rules for handling
railway routes within the simulation. It includes functionality to manage
route details such as origin/destination tracks, track sequences, distances,
and travel times.
"""

import logging
from typing import List

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

# Configure logging
logger = logging.getLogger(__name__)


class Route(BaseModel):
    """Information about a railway route between tracks."""

    route_id: str = Field(description='Unique identifier for the route')
    from_track: str = Field(description='Track ID where the route starts')
    to_track: str = Field(description='Track ID where the route ends')
    track_sequence: List[str] = Field(description='Sequence of tracks forming the complete route')
    distance_m: float = Field(gt=0, description='Total distance of the route in meters')
    time_min: int = Field(gt=0, description='Time required to travel the route in minutes')

    @model_validator(mode='before')
    @classmethod
    def parse_track_sequence(cls, values):
        """Parse track_sequence from string to list if needed."""
        data = dict(values)
        track_sequence = data.get('track_sequence')

        # If already a list, no need to parse
        if isinstance(track_sequence, list):
            return data

        # If string, parse as comma-separated list
        if isinstance(track_sequence, str):
            # Remove any quotes that might be present in CSV
            track_sequence = track_sequence.strip('"\'')
            data['track_sequence'] = [t.strip() for t in track_sequence.split(',')]

        return data

    @model_validator(mode='after')
    def validate_route(self) -> 'Route':
        """Validate route integrity."""
        # Ensure track_sequence contains at least from_track and to_track
        first_track = self.track_sequence[0] if self.track_sequence else None
        last_track = self.track_sequence[-1] if self.track_sequence else None

        if first_track is None or last_track is None:
            raise ValueError(f'Route {self.route_id} must have a valid track_sequence')

        if not self.track_sequence or len(self.track_sequence) < 2:
            raise ValueError(f'Route {self.route_id} must have at least two tracks in sequence')

        # Validate that sequence contains at least the from and to tracks
        if self.from_track not in self.track_sequence:
            raise ValueError(f'Route {self.route_id} must include from_track "{self.from_track}" in track_sequence')

        if self.to_track not in self.track_sequence:
            raise ValueError(f'Route {self.route_id} must include to_track "{self.to_track}" in track_sequence')

        return self
