"""Input DTO for scenario configuration data."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ScenarioInputDTO(BaseModel):
    """Raw input DTO for scenario configuration from JSON files."""

    id: str = Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        min_length=1,
        max_length=50,
        description="Unique scenario identifier",
    )
    start_date: str | datetime
    end_date: str | datetime
    random_seed: int | None = Field(default=None, ge=0)
    train_schedule_file: str | None = Field(default=None, min_length=1)
    routes_file: str | None = Field(default=None, min_length=1)
    workshop_tracks_file: str | None = Field(default=None, min_length=1)
    track_selection_strategy: str | None = Field(
        default=None, pattern=r"^(round_robin|least_occupied|first_available|random)$"
    )
    retrofit_selection_strategy: str | None = Field(
        default=None, pattern=r"^(round_robin|least_occupied|first_available|random)$"
    )
    loco_delivery_strategy: str | None = Field(
        default=None, pattern=r"^(return_to_parking|direct_delivery)$"
    )

    # Optional nested collections for complex scenarios
    trains: list[Any] | None = Field(default=None)
    workshops: list[Any] | None = Field(default=None)
    routes: list[Any] | None = Field(default=None)
    locomotives: list[Any] | None = Field(default=None)
    tracks: list[Any] | None = Field(default=None)
    topology: dict[str, Any] | None = Field(default=None)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, v: str | datetime) -> str:
        """Ensure dates are strings for DTO."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @model_validator(mode="after")
    def validate_date_order(self) -> "ScenarioInputDTO":
        """Validate end_date is after start_date."""
        start = datetime.fromisoformat(str(self.start_date))
        end = datetime.fromisoformat(str(self.end_date))

        if end <= start:
            msg = "end_date must be after start_date"
            raise ValueError(msg)

        return self
