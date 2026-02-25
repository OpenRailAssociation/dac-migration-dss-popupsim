"""Route input DTO for configuration context."""

from datetime import timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import field_validator
from pydantic import model_validator


class RouteType(Enum):
    """Route type enumeration for operational modes."""

    MAINLINE = 'MAINLINE'  # Full brake test + inspection required
    SHUNTING = 'SHUNTING'  # Yard shunting - coupling + preparation only


class RouteInputDTO(BaseModel):
    """Data transfer object for route input data."""

    id: str
    description: str | None = None
    duration: timedelta
    track_sequence: list[str] = []
    path: list[str] = []
    route_type: str = 'SHUNTING'  # Default to shunting for backward compatibility

    @field_validator('duration', mode='before')
    @classmethod
    def convert_duration(cls, v: Any) -> timedelta:
        """Convert float minutes to timedelta."""
        if isinstance(v, (int, float)):
            return timedelta(minutes=v)
        if isinstance(v, timedelta):
            return v
        raise ValueError(f'Invalid duration type: {type(v)}')

    @model_validator(mode='after')
    def sync_path_to_track_sequence(self) -> 'RouteInputDTO':
        """Sync path to track_sequence if track_sequence is empty."""
        if not self.track_sequence and self.path:
            self.track_sequence = self.path
        return self

    @property
    def from_track(self) -> str:
        """First track in sequence."""
        return self.track_sequence[0] if self.track_sequence else ''

    @property
    def to_track(self) -> str:
        """Last track in sequence."""
        return self.track_sequence[-1] if self.track_sequence else ''
