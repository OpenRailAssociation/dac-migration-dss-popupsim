"""Track Input DTO for configuration validation."""

from pydantic import BaseModel


class TrackInputDTO(BaseModel):
    """DTO for track input validation."""

    id: str
    type: str | None = None
    edges: list[str] | None = None
    name: str | None = None
    length: float = 100.0
