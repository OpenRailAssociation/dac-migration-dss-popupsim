"""Retrofit bay entity for individual DAC installation work positions."""

from enum import Enum

from pydantic import BaseModel, Field


class BayStatus(Enum):
    """Status of a retrofit bay."""

    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class RetrofitBay(BaseModel):
    """Individual work position for DAC installation."""

    bay_id: str = Field(description="Unique identifier for the retrofit bay")
    status: BayStatus = Field(
        default=BayStatus.AVAILABLE, description="Current status of the bay"
    )
    current_wagon_id: str | None = Field(
        default=None, description="ID of wagon currently in bay"
    )

    def occupy(self, wagon_id: str) -> None:
        """Occupy bay with a wagon."""
        if self.status != BayStatus.AVAILABLE:
            raise ValueError(f"Bay {self.bay_id} is not available")
        self.status = BayStatus.OCCUPIED
        self.current_wagon_id = wagon_id

    def release(self) -> None:
        """Release bay after work completion."""
        self.status = BayStatus.AVAILABLE
        self.current_wagon_id = None
