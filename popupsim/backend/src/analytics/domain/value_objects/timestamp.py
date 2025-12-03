"""Timestamp value object."""

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from shared.infrastructure.simpy_time_converters import sim_ticks_to_timedelta
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


@dataclass(frozen=True)
class Timestamp:
    """Simulation timestamp representing elapsed time from start."""

    value: timedelta  # Duration from simulation start

    def __post_init__(self) -> None:
        """Validate timestamp is not negative."""
        if self.value.total_seconds() < 0:
            raise ValueError(f'Timestamp cannot be negative: {self.value}')

    @classmethod
    def from_simulation_time(cls, ticks: float) -> 'Timestamp':
        """Create from SimPy simulation time (ticks)."""
        return cls(sim_ticks_to_timedelta(ticks))

    @classmethod
    def from_minutes(cls, minutes: float) -> 'Timestamp':
        """Create from minutes."""
        return cls(timedelta(minutes=minutes))

    @classmethod
    def from_seconds(cls, seconds: float) -> 'Timestamp':
        """Create from seconds."""
        return cls(timedelta(seconds=seconds))

    @classmethod
    def from_hours(cls, hours: float) -> 'Timestamp':
        """Create from hours."""
        return cls(timedelta(hours=hours))

    @classmethod
    def now(cls) -> 'Timestamp':
        """Create from current datetime (for testing)."""
        return cls(timedelta(seconds=datetime.now(UTC).timestamp()))

    def to_simulation_time(self) -> float:
        """Get value in SimPy ticks."""
        return timedelta_to_sim_ticks(self.value)

    def to_minutes(self) -> float:
        """Get value in minutes (for display)."""
        return self.value.total_seconds() / 60.0

    def to_hours(self) -> float:
        """Get value in hours."""
        return self.value.total_seconds() / 3600.0

    def to_seconds(self) -> float:
        """Get value in seconds."""
        return self.value.total_seconds()

    def to_absolute_time(self, start_datetime: datetime) -> datetime:
        """Convert to absolute datetime given simulation start time."""
        if start_datetime.tzinfo is None:
            raise ValueError('start_datetime must be timezone-aware (UTC)')
        return start_datetime + self.value

    def __str__(self) -> str:
        """Human-readable representation."""
        hours = int(self.to_hours())
        minutes = int(self.to_minutes() % 60)
        return f'{hours}h {minutes}m'
