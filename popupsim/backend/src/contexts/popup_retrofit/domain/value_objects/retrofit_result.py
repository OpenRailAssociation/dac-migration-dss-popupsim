"""Retrofit result value object."""

from pydantic import BaseModel
from pydantic import Field


class RetrofitResult(BaseModel):
    """Result of DAC retrofit operation."""

    success: bool = Field(description='Whether retrofit was successful')
    duration: float = Field(description='Time taken for retrofit in minutes')
    reason: str = Field(description='Reason for success or failure')
    wagon_id: str = Field(description='ID of retrofitted wagon')

    @classmethod
    def successful(cls, wagon_id: str, duration: float, reason: str) -> 'RetrofitResult':
        """Create successful retrofit result."""
        return cls(success=True, duration=duration, reason=reason, wagon_id=wagon_id)

    @classmethod
    def failed(cls, wagon_id: str, reason: str) -> 'RetrofitResult':
        """Create failed retrofit result."""
        return cls(success=False, duration=0.0, reason=reason, wagon_id=wagon_id)
