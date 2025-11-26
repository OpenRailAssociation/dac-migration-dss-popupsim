"""Workshop input DTO for configuration context."""

from pydantic import BaseModel
from pydantic import Field


class WorkshopInputDTO(BaseModel):
    """Data transfer object for workshop input data."""

    workshop_id: str = Field(min_length=1)
    track_id: str = Field(min_length=1)
    retrofit_stations: int = Field(gt=0)
