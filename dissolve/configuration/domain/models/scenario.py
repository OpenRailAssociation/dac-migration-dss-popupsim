"""Configuration models for train simulation scenarios.

This module defines the configuration data models for setting up
train simulation scenarios. It includes validation for scenario parameters
such as date ranges, strategies, and file references.

Operational models (locomotives, wagons, trains, tracks, workshops, routes)
have been moved to workshop_operations context.
"""

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from configuration.application.dtos.route_input_dto import RouteInputDTO
from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from shared.value_objects.timezone_utils import ensure_utc, validate_timezone_aware

from .process_times import ProcessTimes

# Configure logging
logger = logging.getLogger(__name__)


class TrackSelectionStrategy(str, Enum):
    """Strategy for selecting collection tracks when multiple are available."""

    ROUND_ROBIN = "round_robin"
    LEAST_OCCUPIED = "least_occupied"
    FIRST_AVAILABLE = "first_available"
    RANDOM = "random"


class LocoDeliveryStrategy(str, Enum):
    """Strategy for locomotive delivery to workshop stations."""

    RETURN_TO_PARKING = "return_to_parking"
    DIRECT_DELIVERY = "direct_delivery"


class Scenario(BaseModel):
    """Scenario model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    workshop models, and required file references.
    Timezone for start_date and end_date is enforced to be UTC in the validators.
    """

    id: str = Field(
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique identifier for the scenario",
        min_length=1,
        max_length=50,
    )
    start_date: datetime = Field(description="Simulation start date")
    end_date: datetime = Field(description="Simulation end date")
    track_selection_strategy: TrackSelectionStrategy = Field(
        default=TrackSelectionStrategy.LEAST_OCCUPIED,
        description="Strategy for selecting collection tracks",
    )
    retrofit_selection_strategy: TrackSelectionStrategy = Field(
        default=TrackSelectionStrategy.LEAST_OCCUPIED,
        description="Strategy for selecting retrofit tracks",
    )
    loco_delivery_strategy: LocoDeliveryStrategy = Field(
        default=LocoDeliveryStrategy.RETURN_TO_PARKING,
        description="Strategy for locomotive delivery to workshop stations",
    )
    locomotives: list[LocomotiveInputDTO] | None = Field(
        default=None, description="Locomotive data"
    )
    process_times: ProcessTimes | None = Field(
        default=None, description="Process timing configuration"
    )
    routes: list[RouteInputDTO] | None = Field(default=None, description="Route data")
    topology: Any = Field(default=None, description="Topology model")
    trains: Any | None = Field(default=None, description="Train models")
    tracks: Sequence[Any] | None = Field(default=None, description="Track models")
    workshops: list[WorkshopInputDTO] | None = Field(
        default=None, description="Workshop data"
    )

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def ensure_utc_timezone_validator(cls, v: datetime | str) -> datetime:
        """Ensure datetime has UTC timezone."""
        return ensure_utc(v)

    @model_validator(mode="after")
    def validate_dates(self) -> "Scenario":
        """Ensure end_date is after start_date and duration is reasonable."""
        validate_timezone_aware(self.start_date, "start_date")
        validate_timezone_aware(self.end_date, "end_date")

        if self.end_date <= self.start_date:
            raise ValueError(
                f"Invalid date range: end_date ({self.end_date}) must be after start_date ({self.start_date})."
            )
        duration: int = (self.end_date - self.start_date).days

        if duration > 365:
            logger.warning(
                "Simulation duration of %d days for scenario '%s' may impact performance.",
                duration,
                self.id,
            )
        elif duration < 1:
            raise ValueError(
                f"Simulation duration must be at least 1 day. Current duration: {duration} days."
            )
        return self

    @property
    def duration(self) -> timedelta:
        """Get simulation duration as timedelta."""
        return self.end_date - self.start_date

    @property
    def duration_hours(self) -> float:
        """Get simulation duration in hours."""
        return self.duration.total_seconds() / 3600.0

    @property
    def duration_minutes(self) -> float:
        """Get simulation duration in minutes (for SimPy)."""
        return self.duration.total_seconds() / 60.0

    def validate_simulation_requirements(self) -> "Scenario":
        """Validate scenario has required resources for simulation.

        This should be called after all referenced files are loaded.
        Basic validation only - detailed track validation happens in workshop_operations context.
        """
        if not self.locomotives:
            raise ValueError("Scenario must have at least one locomotive")
        if not self.trains:
            raise ValueError("Scenario must have at least one train")
        if not self.tracks or not self.topology:
            raise ValueError("Scenario must have tracks and topology")

        return self

    model_config = {"arbitrary_types_allowed": True}
