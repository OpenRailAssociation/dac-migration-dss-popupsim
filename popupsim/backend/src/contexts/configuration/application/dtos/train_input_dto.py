"""Input DTO for train schedule data."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from .wagon_input_dto import WagonInputDTO


class TrainInputDTO(BaseModel):
    """Raw input DTO for train data from CSV files."""

    train_id: str = Field(min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    arrival_time: str | datetime
    departure_time: str | datetime
    locomotive_id: str | None = None
    route_id: str | None = None
    arrival_track: str | None = None
    wagons: list[WagonInputDTO] = Field(min_length=1)
    priority: int | None = Field(default=None, ge=1, le=10)

    @field_validator('arrival_time', 'departure_time', mode='before')
    @classmethod
    def parse_times(cls, v: str | datetime | None) -> str | None:
        """Ensure times are strings for DTO."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @model_validator(mode="after")
    def validate_time_order(self) -> "TrainInputDTO":
        """Validate departure_time is after arrival_time."""
        arrival = datetime.fromisoformat(str(self.arrival_time))
        departure = datetime.fromisoformat(str(self.departure_time))

        if departure < arrival:
            msg = "departure_time must be after arrival_time"
            raise ValueError(msg)

        return self
