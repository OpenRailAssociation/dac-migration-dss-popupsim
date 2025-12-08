"""Locomotive input DTO for configuration context."""

from pydantic import BaseModel


class LocomotiveInputDTO(BaseModel):
    """Data transfer object for locomotive input data."""

    id: str
    track: str
    status: str = "AVAILABLE"
