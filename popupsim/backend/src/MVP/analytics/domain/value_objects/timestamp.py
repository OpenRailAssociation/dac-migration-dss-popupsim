"""Timestamp value object."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from shared.infrastructure.time_converters import (
    from_ticks,
    to_ticks,
)
from shared.value_objects.timezone_utils import (
    ensure_utc,
    validate_timezone_aware,
)


@dataclass(frozen=True)
class Timestamp:
    """Simulation timestamp."""

    duration: timedelta

    def __post_init__(self) -> None:
        """Validate timestamp is non-negative."""
        if self.duration.total_seconds() < 0:
            msg = f"Timestamp cannot be negative: {self.duration}"
            raise ValueError(msg)

    @classmethod
    def from_ticks(cls, ticks: float) -> "Timestamp":
        """Create from simulation ticks."""
        return cls(from_ticks(ticks))

    @classmethod
    def from_simulation_time(cls, ticks: float) -> "Timestamp":
        """Create from simulation time for backward compatibility."""
        return cls.from_ticks(ticks)

    @classmethod
    def from_datetime(cls, dt: datetime | str, start_time: datetime) -> "Timestamp":
        """Create from absolute datetime with timezone handling."""
        dt = ensure_utc(dt) if isinstance(dt, str) else dt
        validate_timezone_aware(dt, "datetime")
        validate_timezone_aware(start_time, "start_time")

        # Ensure both are in UTC for consistent calculation
        dt_utc = dt.astimezone(UTC)
        start_utc = start_time.astimezone(UTC)

        duration = dt_utc - start_utc
        if duration.total_seconds() < 0:
            msg = f"Datetime {dt} is before start time {start_time}"
            raise ValueError(msg)

        return cls(duration)

    def to_ticks(self) -> float:
        """Convert to simulation ticks."""
        return to_ticks(self.duration)

    def to_minutes(self) -> float:
        """Get value in minutes for backward compatibility."""
        return self.duration.total_seconds() / 60.0

    def to_hours(self) -> float:
        """Get value in hours for backward compatibility."""
        return self.duration.total_seconds() / 3600.0

    def to_seconds(self) -> float:
        """Get value in seconds for backward compatibility."""
        return self.duration.total_seconds()

    def to_absolute_time(self, start_datetime: datetime) -> datetime:
        """Convert to absolute datetime with timezone handling."""
        validate_timezone_aware(start_datetime, "start_datetime")
        return start_datetime.astimezone(UTC) + self.duration

    def __str__(self) -> str:
        """Human-readable format."""
        total_minutes = self.duration.total_seconds() / 60
        hours, minutes = divmod(int(total_minutes), 60)
        return f"{hours}h{minutes:02d}m"
