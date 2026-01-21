"""Route input DTO for configuration context."""

from enum import Enum

from pydantic import BaseModel
from pydantic import model_validator


class RouteType(Enum):
    """Route type enumeration for transport operations."""

    MAINLINE = 'MAINLINE'
    SHUNTING = 'SHUNTING'


class RouteInputDTO(BaseModel):
    """Data transfer object for route input data."""

    id: str
    description: str | None = None
    duration: float
    track_sequence: list[str] = []
    path: list[str] = []

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
