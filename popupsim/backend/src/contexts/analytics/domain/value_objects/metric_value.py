"""Metric value value object."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricValue:
    """Value with timestamp for time-series metrics."""

    value: Any
    timestamp: float

    def __post_init__(self) -> None:
        if self.timestamp < 0:
            msg = 'Timestamp cannot be negative'
            raise ValueError(msg)
        if not isinstance(self.value, (int, float, str, bool)):
            msg = f'Invalid metric value type: {type(self.value)}'
            raise ValueError(msg)

    def is_numeric(self) -> bool:
        """Check if value is numeric."""
        return isinstance(self.value, (int, float))

    def as_float(self) -> float:
        """Convert to float if numeric."""
        if not self.is_numeric():
            msg = f'Cannot convert {type(self.value)} to float'
            raise ValueError(msg)
        return float(self.value)
