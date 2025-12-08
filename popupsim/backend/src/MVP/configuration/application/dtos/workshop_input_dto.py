"""Workshop input DTO for configuration context."""

from pydantic import BaseModel, Field


class WorkshopInputDTO(BaseModel):
    """Data transfer object for workshop input data."""

    id: str = Field(min_length=1)
    track: str = Field(min_length=1)
    retrofit_stations: int = Field(gt=0)
