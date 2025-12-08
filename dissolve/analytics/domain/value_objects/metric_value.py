"""Metric value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricValue:
    """Strongly typed metric value with unit."""

    value: float | int | str
    unit: str

    def __init__(self, value: float | int | str, unit: str) -> None:
        if not unit or not unit.strip():
            raise ValueError("Unit cannot be empty")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "unit", unit)

    @classmethod
    def percentage(cls, value: float) -> "MetricValue":
        """Create percentage metric."""
        if not 0 <= value <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return cls(round(value, 2), "%")

    @classmethod
    def count(cls, value: int) -> "MetricValue":
        """Create count metric."""
        if value < 0:
            raise ValueError("Count cannot be negative")
        return cls(value, "count")

    @classmethod
    def duration_minutes(cls, value: float) -> "MetricValue":
        """Create duration metric in minutes."""
        if value < 0:
            raise ValueError("Duration cannot be negative")
        return cls(round(value, 2), "minutes")

    def is_numeric(self) -> bool:
        """Check if value is numeric."""
        return isinstance(self.value, (int, float))
