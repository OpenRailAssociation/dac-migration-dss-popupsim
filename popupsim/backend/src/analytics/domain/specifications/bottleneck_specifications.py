"""Bottleneck detection specifications."""

from ..models.kpi_result import BottleneckInfo
from ..models.kpi_result import ThroughputKPI
from ..models.kpi_result import UtilizationKPI
from .base_specification import Specification


class HighUtilizationSpec(Specification[UtilizationKPI]):
    """Specification for high workshop utilization."""

    def __init__(self, threshold: float = 90.0) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, candidate: UtilizationKPI) -> bool:
        """Check if utilization exceeds high threshold."""
        return candidate.average_utilization_percent > self.threshold


class CriticalUtilizationSpec(Specification[UtilizationKPI]):
    """Specification for critical workshop utilization."""

    def __init__(self, threshold: float = 95.0) -> None:
        self.threshold = threshold

    def is_satisfied_by(self, candidate: UtilizationKPI) -> bool:
        """Check if utilization exceeds critical threshold."""
        return candidate.average_utilization_percent > self.threshold


class HighRejectionRateSpec(Specification[ThroughputKPI]):
    """Specification for high wagon rejection rate."""

    def __init__(self, threshold: float = 0.1) -> None:  # 10%
        self.threshold = threshold

    def is_satisfied_by(self, candidate: ThroughputKPI) -> bool:
        """Check if rejection rate exceeds threshold."""
        if candidate.total_wagons_processed == 0:
            return False
        rejection_rate = candidate.total_wagons_rejected / candidate.total_wagons_processed
        return rejection_rate > self.threshold


class LowThroughputSpec(Specification[ThroughputKPI]):
    """Specification for low throughput performance."""

    def __init__(self, min_wagons_per_hour: float = 10.0) -> None:
        self.min_wagons_per_hour = min_wagons_per_hour

    def is_satisfied_by(self, candidate: ThroughputKPI) -> bool:
        """Check if throughput is below minimum threshold."""
        return candidate.wagons_per_hour < self.min_wagons_per_hour


class CriticalBottleneckSpec(Specification[BottleneckInfo]):
    """Specification for critical bottlenecks."""

    def is_satisfied_by(self, candidate: BottleneckInfo) -> bool:
        """Check if bottleneck has critical severity."""
        return candidate.severity == 'critical'
