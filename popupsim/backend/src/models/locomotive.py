"""Locomotive model for DAC retrofit operations."""

from datetime import UTC
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import field_validator

class LocoStatus(Enum):
    """Locomotive status events"""
    PARKING = "parking"
    MOVING = "moving"
    COUPLING = "coupling"
    DECOUPLING = "decoupling"

class Locomotive(BaseModel):
    """Locomotive configuration for workshop operations."""

    locomotive_id: str
    name: str
    start_date: datetime
    end_date: datetime
    track_id: str
    status: LocoStatus = LocoStatus.PARKING

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_datetime(cls, value: str | datetime) -> datetime:
        """Parse datetime from string."""
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)
        if isinstance(value, datetime):
            return value
        msg = f'Expected str or datetime, got {type(value)}'
        raise TypeError(msg)
