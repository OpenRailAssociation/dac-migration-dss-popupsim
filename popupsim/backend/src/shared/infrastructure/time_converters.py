"""Streamlined time conversion functions."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from .time_config import SIMULATION_TIME_UNIT_SECONDS


def to_ticks(duration: timedelta) -> float:
    """Convert timedelta to simulation ticks."""
    return duration.total_seconds() / SIMULATION_TIME_UNIT_SECONDS


def from_ticks(ticks: float) -> timedelta:
    """Convert simulation ticks to timedelta."""
    return timedelta(seconds=ticks * SIMULATION_TIME_UNIT_SECONDS)


def datetime_to_ticks(target_time: datetime, current_time: datetime) -> float:
    """Calculate simulation ticks between two timezone-aware datetimes."""
    if target_time.tzinfo is None or current_time.tzinfo is None:
        msg = 'Both datetimes must be timezone-aware'
        raise ValueError(msg)

    # Convert to UTC for consistent calculation
    target_utc = target_time.astimezone(UTC)
    current_utc = current_time.astimezone(UTC)

    delay = target_utc - current_utc
    return to_ticks(delay)
