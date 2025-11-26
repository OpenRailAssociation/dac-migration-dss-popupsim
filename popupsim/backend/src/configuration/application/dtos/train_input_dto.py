"""Input DTO for train schedule data."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from configuration.application.dtos.wagon_input_dto import WagonInputDTO


class TrainInputDTO(BaseModel):
    """Raw input DTO for train data from CSV files."""

    train_id: str = Field(min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    arrival_time: str | datetime
    departure_time: str | datetime
    locomotive_id: str = Field(min_length=1, max_length=50)
    route_id: str = Field(min_length=1, max_length=50)
    wagons: list[WagonInputDTO] = Field(min_length=1)
    priority: int | None = Field(default=None, ge=1, le=10)

    @field_validator('arrival_time', 'departure_time', mode='before')
    @classmethod
    def parse_times(cls, v: str | datetime) -> str:
        """Ensure times are strings for DTO."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @model_validator(mode='after')
    def validate_time_order(self) -> 'TrainInputDTO':
        """Validate departure_time is after arrival_time."""
        arrival = datetime.fromisoformat(str(self.arrival_time))
        departure = datetime.fromisoformat(str(self.departure_time))

        if departure < arrival:
            raise ValueError('departure_time must be after arrival_time')

        return self
