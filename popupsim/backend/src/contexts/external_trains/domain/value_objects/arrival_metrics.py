"""Arrival metrics value object for External Trains Context."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArrivalMetrics:
    """Metrics for train arrivals."""

    scheduled_time: float
    actual_time: float
    wagon_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'scheduled_time': self.scheduled_time,
            'actual_time': self.actual_time,
            'wagon_count': self.wagon_count,
            'delay': self.actual_time - self.scheduled_time,
        }
