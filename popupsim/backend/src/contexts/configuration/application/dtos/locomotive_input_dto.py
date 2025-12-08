"""Locomotive input DTO for configuration context."""

from pydantic import BaseModel, ConfigDict, Field


class LocomotiveInputDTO(BaseModel):
    """Data transfer object for locomotive input data."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    track: str = Field(alias="home track")
    status: str = "AVAILABLE"
