"""Metrics snapshot value objects for analytics context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainArrivalMetrics:
    """Metrics for external train arrivals."""

    total_arrivals: int
    total_wagons: int
    arrivals_by_time: dict[float, int]  # timestamp -> wagon count


@dataclass(frozen=True)
class WagonMetrics:
    """Metrics for wagon states across contexts."""

    retrofitted_count: int
    rejected_count: int
    in_parking_count: int
    retrofitting_count: int
    on_retrofit_track_count: int
    on_retrofitted_track_count: int


@dataclass(frozen=True)
class LocomotiveUtilization:
    """Locomotive utilization breakdown."""

    parking_time: float
    moving_time: float
    coupling_time: float
    decoupling_time: float
    total_time: float

    @property
    def parking_percentage(self) -> float:
        """Return the percentage of parking time."""
        return (self.parking_time / self.total_time * 100) if self.total_time > 0 else 0.0

    @property
    def moving_percentage(self) -> float:
        """Return the percentage of moving tiem."""
        return (self.moving_time / self.total_time * 100) if self.total_time > 0 else 0.0

    @property
    def coupling_percentage(self) -> float:
        """Return the percentage of coupling time."""
        return (self.coupling_time / self.total_time * 100) if self.total_time > 0 else 0.0

    @property
    def decoupling_percentage(self) -> float:
        """Return percentage of decoupling time."""
        return (self.decoupling_time / self.total_time * 100) if self.total_time > 0 else 0.0


@dataclass(frozen=True)
class WorkshopMetrics:
    """Metrics for workshop operations."""

    completed_retrofits: int
    total_working_time: float
    total_waiting_time: float
    wagons_per_hour: float

    @property
    def working_percentage(self) -> float:
        """Return the percentage of working time."""
        total = self.total_working_time + self.total_waiting_time
        return (self.total_working_time / total * 100) if total > 0 else 0.0

    @property
    def waiting_percentage(self) -> float:
        """Return the percentage of waiting time."""
        total = self.total_working_time + self.total_waiting_time
        return (self.total_waiting_time / total * 100) if total > 0 else 0.0


@dataclass(frozen=True)
class TrackCapacitySnapshot:
    """Track capacity at a point in time."""

    track_id: str
    used_capacity: int
    total_capacity: int
    timestamp: float

    @property
    def utilization_percentage(self) -> float:
        """Return utilization in percentage of the track."""
        return (self.used_capacity / self.total_capacity * 100) if self.total_capacity > 0 else 0.0

    @property
    def status(self) -> str:
        """Track status: green (empty), yellow (nearly full), red (full)."""
        if self.utilization_percentage >= 95:
            return 'red'
        if self.utilization_percentage >= 70:
            return 'yellow'
        return 'green'


@dataclass(frozen=True)
class BottleneckDetection:
    """Bottleneck detection result."""

    resource_type: str  # workshop, track, locomotive
    resource_id: str
    utilization_percentage: float
    threshold_exceeded: bool
    severity: str  # overutilization, underutilization, normal

    # pylint: disable=too-many-positional-arguments, too-many-arguments
    @classmethod
    def detect(
        cls,
        resource_type: str,
        resource_id: str,
        utilization: float,
        over_threshold: float = 90.0,
        under_threshold: float = 20.0,
    ) -> 'BottleneckDetection':
        """Detect bottleneck based on utilization thresholds."""
        if utilization > over_threshold:
            return cls(resource_type, resource_id, utilization, True, 'overutilization')
        if utilization < under_threshold:
            return cls(resource_type, resource_id, utilization, True, 'underutilization')
        return cls(resource_type, resource_id, utilization, False, 'normal')
