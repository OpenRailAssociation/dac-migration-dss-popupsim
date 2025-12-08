"""Wagon Input DTO for configuration validation."""

from pydantic import BaseModel, Field


class WagonInputDTO(BaseModel):
    """DTO for individual wagon input validation."""

    id: str = Field(min_length=1)
    length: float = Field(gt=0)
    is_loaded: bool = Field(default=False)
    needs_retrofit: bool = Field(default=True)
    track: str | None = None
