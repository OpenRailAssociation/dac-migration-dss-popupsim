"""Models and validation logic for railway route configurations.

This module provides data models and validation rules for handling
railway routes within the simulation. It includes functionality to manage
route details such as origin/destination tracks, track sequences, distances,
and travel times.
"""

import logging
from typing import Any

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
    track_sequence: list[str] = Field(description='Sequence of tracks forming the complete route')
    distance_m: float = Field(gt=0, description='Total distance of the route in meters')
    time_min: int = Field(gt=0, description='Time required to travel the route in minutes')

    @model_validator(mode='before')
    @classmethod
    def parse_track_sequence(cls, data: dict[str, Any] | list[str] | str) -> dict[str, Any]:
        """Parse track_sequence from string to list if needed."""
        # If data is already a list, wrap it in a dict
        if isinstance(data, list):
            return {'track_sequence': data}

        # If data is a string (direct track_sequence value)
        if isinstance(data, str):
            track_sequences = data.strip('"\'')
            parsed_sequence = [t.strip() for t in track_sequences.split(',')]

            if not all(isinstance(item, str) for item in parsed_sequence):
                raise ValueError('All items in track_sequence must be strings')

            return {'track_sequence': parsed_sequence}

        # If data is a dict, process the track_sequence field
        if isinstance(data, dict):
            if 'track_sequence' not in data:
                return data  # Return as-is if no track_sequence field

            track_sequence = data['track_sequence']

            # If track_sequence is already a list, return the dict as-is
            if isinstance(track_sequence, list):
                return data

            # If track_sequence is a string, parse it
            if isinstance(track_sequence, str):
                # Remove any quotes that might be present in CSV
                track_sequences = track_sequence.strip('"\'')
                parsed_sequence = [t.strip() for t in track_sequences.split(',')]

                # Validate all items are strings
                if not all(isinstance(item, str) for item in parsed_sequence):
                    raise ValueError('All items in track_sequence must be strings')

                data['track_sequence'] = parsed_sequence
                return data

        # This should never be reached due to type hints, but ensures MyPy compliance
        return data

    @model_validator(mode='after')
    def validate_route(self) -> 'Route':
        """Validate route integrity."""
        # Check if track_sequence is empty
        if not self.track_sequence:
            raise ValueError(f'Route {self.route_id} must have a valid track_sequence')

        # Check minimum length
        if len(self.track_sequence) < 2:
            raise ValueError(f'Route {self.route_id} must have at least two tracks in sequence')

        # Validate that sequence contains at least the from and to tracks
        if self.from_track not in self.track_sequence:
            raise ValueError(f'Route {self.route_id} must include from_track "{self.from_track}" in track_sequence')

        if self.to_track not in self.track_sequence:
            raise ValueError(f'Route {self.route_id} must include to_track "{self.to_track}" in track_sequence')

        return self
