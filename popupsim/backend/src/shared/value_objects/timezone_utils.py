"""Timezone utilities for consistent datetime handling."""

from datetime import UTC
from datetime import datetime
from datetime import timezone


def ensure_utc(dt: datetime | str) -> datetime:
    """Ensure datetime is timezone-aware UTC.

    Parameters
    ----------
    dt : datetime | str
        Datetime object or ISO format string

    Returns
    -------
    datetime
        Timezone-aware datetime in UTC
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)

    return dt.astimezone(UTC)


def now_utc() -> datetime:
    """Get current time in UTC."""
    return datetime.now(UTC)


def from_timestamp(timestamp: float, tz: timezone = UTC) -> datetime:
    """Create datetime from Unix timestamp."""
    return datetime.fromtimestamp(timestamp, tz=tz)


def validate_timezone_aware(dt: datetime, field_name: str = 'datetime') -> None:
    """Validate that datetime is timezone-aware."""
    if dt.tzinfo is None:
        msg = f'{field_name} must be timezone-aware (UTC)'
        raise ValueError(msg)
