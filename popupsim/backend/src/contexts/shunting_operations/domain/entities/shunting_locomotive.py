"""Shunting locomotive entity."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from contexts.shunting_operations.domain.value_objects.locomotive_id import (
    LocomotiveId,
)


class ShuntingStatus(Enum):
    """Shunting locomotive status."""

    IDLE = "idle"
    MOVING = "moving"
    COUPLING = "coupling"
    DECOUPLING = "decoupling"


class ShuntingLocomotive(BaseModel):
    """Locomotive for shunting operations."""

    id: LocomotiveId = Field(description="Locomotive identifier")
    current_track: str = Field(description="Current track location")
    home_track: str = Field(description="Home parking track")
    status: ShuntingStatus = Field(
        default=ShuntingStatus.IDLE, description="Current status"
    )
    max_capacity: int = Field(default=10, description="Maximum wagon capacity")
    current_load: int = Field(default=0, description="Current number of coupled wagons")
    track_request: Any | None = Field(default=None, description="Current track resource request")

    def is_available(self) -> bool:
        """Check if locomotive is available for operations."""
        return self.status == ShuntingStatus.IDLE

    def start_operation(self, operation_type: ShuntingStatus) -> None:
        """Start a shunting operation."""
        if not self.is_available():
            msg = f"Locomotive {self.id.value} is not available"
            raise ValueError(msg)
        self.status = operation_type

    def complete_operation(self) -> None:
        """Complete current operation."""
        self.status = ShuntingStatus.IDLE

    def move_to_track(self, track: str) -> None:
        """Move locomotive to specified track."""
        self.current_track = track

    def is_at_capacity(self) -> bool:
        """Check if locomotive is at maximum capacity."""
        return self.current_load >= self.max_capacity
