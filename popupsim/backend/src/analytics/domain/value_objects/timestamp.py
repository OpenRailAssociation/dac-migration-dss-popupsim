"""Timestamp value object."""

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime


@dataclass(frozen=True)
class Timestamp:
    """Simulation timestamp with validation."""

    value: float  # Minutes from simulation start

    def __post_init__(self) -> None:
        """Validate timestamp is not negative."""
        if self.value < 0:
            raise ValueError('Timestamp cannot be negative')

    @classmethod
    def from_simulation_time(cls, time: float) -> 'Timestamp':
        """Create from simulation time in minutes."""
        return cls(time)

    @classmethod
    def now(cls) -> 'Timestamp':
        """Create from current datetime (for testing)."""
        return cls(datetime.now(UTC).timestamp() / 60.0)

    def to_minutes(self) -> float:
        """Get value in minutes."""
        return self.value

    def to_hours(self) -> float:
        """Get value in hours."""
        return self.value / 60.0
