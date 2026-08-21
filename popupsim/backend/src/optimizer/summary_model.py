from pydantic import BaseModel, Field


class WorkshopStats(BaseModel):
    """Per-workshop breakdown."""

    wagons_processed: int = Field(default=0)
    retrofits_started: int = Field(default=0)


class WorkshopStatistics(BaseModel):
    """Aggregated workshop statistics."""

    total_workshops: int = Field(default=0)
    workshops: dict[str, WorkshopStats] = Field(default_factory=dict)
    total_wagons_processed: int = Field(default=0)


class LocomotiveStatistics(BaseModel):
    """Locomotive operation counts."""

    allocations: int = Field(default=0)
    releases: int = Field(default=0)
    movements: int = Field(default=0)
    total_operations: int = Field(default=0)


class LocomotiveTimeBreakdown(BaseModel):
    """Per-locomotive time breakdown."""

    moving_time: float = Field(default=0.0)
    idle_time: float = Field(default=0.0)
    coupling_time: float = Field(default=0.0)
    decoupling_time: float = Field(default=0.0)


class SummaryMetrics(BaseModel):
    """Typed representation of summary_metrics.json produced by the simulation."""

    # Event totals
    total_events: int = Field(default=0)
    event_counts: dict[str, int] = Field(default_factory=dict)

    # Wagon counts
    trains_arrived: int = Field(default=0)
    total_wagons: int = Field(default=0)
    wagons_eligible: int = Field(default=0)
    wagons_processable: int = Field(default=0)
    wagons_arrived: int = Field(default=0)
    wagons_parked: int = Field(default=0)
    retrofits_completed: int = Field(default=0)
    wagons_rejected: int = Field(default=0)
    rejected_no_retrofit: int = Field(default=0)
    rejected_loaded: int = Field(default=0)
    rejected_track_full: int = Field(default=0)
    rejected_other: int = Field(default=0)
    wagons_distributed: int = Field(default=0)
    wagons_in_process: int = Field(default=0)

    # Rates
    completion_rate: float = Field(default=0.0)
    throughput_rate_per_hour: float = Field(default=0.0)

    # Workshop
    workshop_statistics: WorkshopStatistics = Field(default_factory=WorkshopStatistics)
    workshop_utilization: float = Field(default=0.0)

    # Locomotive
    locomotive_statistics: LocomotiveStatistics = Field(default_factory=LocomotiveStatistics)
    locomotive_time_breakdown: dict[str, LocomotiveTimeBreakdown] = Field(default_factory=dict)

    # Simulation duration
    simulation_duration_minutes: float = Field(default=0.0)

    @property
    def completion_rate_pct(self) -> float:
        """Percentage of processable wagons that were fully retrofitted and parked (0–100)."""
        return self.completion_rate * 100.0

    @property
    def loco_utilization_pct(self) -> float:
        """Average locomotive utilisation as a percentage of total available time (0–100).

        Active time per loco = moving_time + coupling_time + decoupling_time (excludes idle).
        Each locomotive is weighted equally.
        """
        n_locos = len(self.locomotive_time_breakdown)
        if n_locos == 0 or self.simulation_duration_minutes == 0:
            return 0.0
        total_active = sum(
            locomotive.moving_time
            for locomotive in self.locomotive_time_breakdown.values()
        )
        return (total_active / n_locos) / self.simulation_duration_minutes * 100.0
