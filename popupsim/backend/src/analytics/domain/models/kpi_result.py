"""KPI result models for analytics."""

from dataclasses import dataclass
from dataclasses import field


@dataclass
class ThroughputKPI:
    """Throughput metrics."""

    total_wagons_processed: int
    total_wagons_retrofitted: int
    total_wagons_rejected: int
    simulation_duration_hours: float
    wagons_per_hour: float
    wagons_per_day: float


@dataclass
class UtilizationKPI:
    """Workshop utilization metrics."""

    workshop_id: str
    total_capacity: int
    average_utilization_percent: float
    peak_utilization_percent: float
    idle_time_percent: float


@dataclass
class BottleneckInfo:
    """Bottleneck identification."""

    location: str
    type: str  # 'track', 'workshop', 'resource'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    impact_wagons_per_hour: float


@dataclass
class KPIResult:
    """Complete KPI analysis result."""

    scenario_id: str
    throughput: ThroughputKPI
    utilization: list[UtilizationKPI] = field(default_factory=list)
    bottlenecks: list[BottleneckInfo] = field(default_factory=list)
    avg_flow_time_minutes: float = 0.0
    avg_waiting_time_minutes: float = 0.0
