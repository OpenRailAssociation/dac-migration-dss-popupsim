"""Analytics metrics value object for Analytics Context."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnalyticsMetrics:
    """Metrics collected during simulation."""

    throughput: float
    utilization: float
    total_wagons: int
    processed_wagons: int

    def efficiency(self) -> float:
        """Calculate efficiency ratio."""
        return (
            self.processed_wagons / self.total_wagons if self.total_wagons > 0 else 0.0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "throughput": self.throughput,
            "utilization": self.utilization,
            "total_wagons": self.total_wagons,
            "processed_wagons": self.processed_wagons,
            "efficiency": self.efficiency(),
        }


@dataclass(frozen=True)
class TimeRange:
    """Time range for analytics queries."""

    start: float
    end: float

    def duration(self) -> float:
        return self.end - self.start

    def contains(self, timestamp: float) -> bool:
        return self.start <= timestamp <= self.end


@dataclass(frozen=True)
class Threshold:
    """Threshold for metric alerting."""

    metric_name: str
    warning_value: float
    critical_value: float

    def evaluate(self, value: float) -> str:
        """Evaluate value against thresholds."""
        if value <= self.critical_value:
            return "critical"
        if value <= self.warning_value:
            return "warning"
        return "normal"
