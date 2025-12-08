"""Track Input DTO for configuration validation."""

from pydantic import BaseModel


class TrackInputDTO(BaseModel):
    """DTO for track input validation."""

    id: str
    type: str
    edges: list[str]
    name: str | None = None
    capacity: int = 1
