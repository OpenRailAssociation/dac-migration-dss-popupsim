"""Input DTO for train schedule data."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from .wagon_input_dto import WagonInputDTO


class TrainInputDTO(BaseModel):
    """Raw input DTO for train data from CSV files."""

    train_id: str = Field(min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    arrival_time: str | datetime
    departure_time: str | datetime | None = None
    locomotive_id: str | None = None
    route_id: str | None = None
    arrival_track: str | None = None
    wagons: list[WagonInputDTO] = Field(min_length=1)
    priority: int | None = Field(default=None, ge=1, le=10)

    @field_validator("arrival_time", "departure_time", mode="before")
    @classmethod
    def parse_times(cls, v: str | datetime | None) -> str | None:
        """Ensure times are strings for DTO."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return v
