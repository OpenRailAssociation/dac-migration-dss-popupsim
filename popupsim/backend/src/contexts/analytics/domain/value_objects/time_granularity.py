"""Time granularity configuration for analytics."""

from enum import Enum


class TimeGranularity(Enum):
    """Predefined time granularities for time-series data."""

    MINUTE = 60.0  # 1 minute
    FIVE_MINUTES = 300.0  # 5 minutes
    FIFTEEN_MINUTES = 900.0  # 15 minutes
    THIRTY_MINUTES = 1800.0  # 30 minutes
    HOUR = 3600.0  # 1 hour
    TWO_HOURS = 7200.0  # 2 hours
    FOUR_HOURS = 14400.0  # 4 hours
    DAY = 86400.0  # 24 hours


class TimeGranularityConfig:
    """Configuration for time granularity with custom intervals."""

    def __init__(self, granularity: TimeGranularity | float = TimeGranularity.HOUR) -> None:
        if isinstance(granularity, TimeGranularity):
            self.interval_seconds = granularity.value
        else:
            self.interval_seconds = float(granularity)

    @classmethod
    def custom(cls, seconds: float) -> 'TimeGranularityConfig':
        """Create custom time granularity."""
        return cls(seconds)

    @classmethod
    def minutes(cls, minutes: int) -> 'TimeGranularityConfig':
        """Create granularity in minutes."""
        return cls(minutes * 60.0)

    @classmethod
    def hours(cls, hours: int) -> 'TimeGranularityConfig':
        """Create granularity in hours."""
        return cls(hours * 3600.0)
