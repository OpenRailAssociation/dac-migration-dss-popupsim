"""Locomotive ID value object."""

from pydantic import BaseModel, Field


class LocomotiveId(BaseModel):
    """Locomotive identifier."""

    value: str = Field(description="Locomotive identifier value")

    def __str__(self) -> str:
        return self.value
