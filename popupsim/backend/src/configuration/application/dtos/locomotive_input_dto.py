"""Locomotive input DTO for configuration context."""

from pydantic import BaseModel


class LocomotiveInputDTO(BaseModel):
    """Data transfer object for locomotive input data."""

    locomotive_id: str
    track_id: str
    status: str = 'AVAILABLE'