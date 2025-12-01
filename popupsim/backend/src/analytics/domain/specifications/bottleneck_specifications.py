"""Bottleneck detection specifications."""

from ..models.bottleneck_config import BottleneckConfig
from ..models.kpi_result import BottleneckInfo
from ..models.kpi_result import ThroughputKPI
from ..models.kpi_result import UtilizationKPI
from .base_specification import Specification


class HighUtilizationSpec(Specification[UtilizationKPI]):
    """Specification for high workshop utilization."""

    def __init__(self, config: BottleneckConfig) -> None:
        self.threshold = config.workshop.high_utilization_percent

    def is_satisfied_by(self, candidate: UtilizationKPI) -> bool:
        """Check if utilization exceeds high threshold."""
        return candidate.average_utilization_percent > self.threshold


class CriticalUtilizationSpec(Specification[UtilizationKPI]):
    """Specification for critical workshop utilization."""

    def __init__(self, config: BottleneckConfig) -> None:
        self.threshold = config.workshop.critical_utilization_percent

    def is_satisfied_by(self, candidate: UtilizationKPI) -> bool:
        """Check if utilization exceeds critical threshold."""
        return candidate.average_utilization_percent > self.threshold


class HighRejectionRateSpec(Specification[ThroughputKPI]):
    """Specification for high wagon rejection rate."""

    def __init__(self, config: BottleneckConfig) -> None:
        self.threshold = config.global_rejection_rate_percent / 100.0  # Convert to decimal

    def is_satisfied_by(self, candidate: ThroughputKPI) -> bool:
        """Check if rejection rate exceeds threshold."""
        if candidate.total_wagons_processed == 0:
            return False
        rejection_rate = candidate.total_wagons_rejected / candidate.total_wagons_processed
        return rejection_rate > self.threshold


class LowThroughputSpec(Specification[ThroughputKPI]):
    """Specification for low throughput performance."""

    def __init__(self, config: BottleneckConfig) -> None:
        self.min_wagons_per_hour = config.workshop.min_throughput_wagons_per_hour

    def is_satisfied_by(self, candidate: ThroughputKPI) -> bool:
        """Check if throughput is below minimum threshold."""
        return candidate.wagons_per_hour < self.min_wagons_per_hour


class CriticalBottleneckSpec(Specification[BottleneckInfo]):
    """Specification for critical bottlenecks."""

    def is_satisfied_by(self, candidate: BottleneckInfo) -> bool:
        """Check if bottleneck has critical severity."""
        return candidate.severity == 'critical'
