"""Route input DTO for configuration context."""

from pydantic import BaseModel


class RouteInputDTO(BaseModel):
    """Data transfer object for route input data."""

    id: str
    description: str | None = None
    duration: float
    track_sequence: list[str] | None = None
    path: list[str] | None = None

    @property
    def from_track(self) -> str:
        """First track in sequence."""
        return self.track_sequence[0] if self.track_sequence else ""

    @property
    def to_track(self) -> str:
        """Last track in sequence."""
        return self.track_sequence[-1] if self.track_sequence else ""
