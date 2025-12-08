"""Metric ID value object for Analytics Context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricId:
    """Unique identifier for metrics."""

    id: str

    @property
    def value(self) -> str:
        """Get ID value for backward compatibility."""
        return self.id
