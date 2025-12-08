"""Domain service for planning multi-track transport operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon
    from shared.domain.services.retrofit_track_allocation_service import (
        RetrofitAllocation,
    )


@dataclass
class TransportJob:
    """Single transport job to one retrofit track."""

    wagons: list[Wagon]
    from_track: str
    to_track: str
    estimated_duration: float


@dataclass
class TransportPlan:
    """Plan for transporting wagons to multiple retrofit tracks."""

    transport_jobs: list[TransportJob]
    total_duration: float
    locomotive_utilization: float
    route_efficiency: float


class MultiTrackTransportService:
    """Domain service for planning multi-track transport."""

    def create_transport_plan(
        self, allocation: RetrofitAllocation, from_track: str = "collection"
    ) -> TransportPlan:
        """Create optimal transport plan for retrofit allocation."""
        jobs = []

        for track_id, wagons in allocation.track_assignments.items():
            job = TransportJob(
                wagons=wagons,
                from_track=from_track,
                to_track=track_id,
                estimated_duration=self._estimate_job_duration(wagons),
            )
            jobs.append(job)

        # Optimize job sequence
        optimized_jobs = self._optimize_job_sequence(jobs)

        total_duration = sum(job.estimated_duration for job in optimized_jobs)

        return TransportPlan(
            transport_jobs=optimized_jobs,
            total_duration=total_duration,
            locomotive_utilization=self._calculate_utilization(optimized_jobs),
            route_efficiency=self._calculate_route_efficiency(optimized_jobs),
        )

    def _estimate_job_duration(self, wagons: list[Wagon]) -> float:
        """Estimate duration for single transport job."""
        # Base time + coupling time + movement time + decoupling time
        base_time = 2.0  # minutes
        coupling_time = len(wagons) * 0.5  # 0.5 min per wagon
        movement_time = 3.0  # minutes (track to track)
        decoupling_time = len(wagons) * 0.5  # 0.5 min per wagon

        return base_time + coupling_time + movement_time + decoupling_time

    def _optimize_job_sequence(self, jobs: list[TransportJob]) -> list[TransportJob]:
        """Optimize job sequence for minimal travel time."""
        # Simple optimization: sort by track name for consistent routing
        return sorted(jobs, key=lambda j: j.to_track)

    def _calculate_utilization(self, jobs: list[TransportJob]) -> float:
        """Calculate locomotive utilization efficiency."""
        if not jobs:
            return 0.0

        total_transport_time = sum(job.estimated_duration for job in jobs)
        total_wagon_time = sum(len(job.wagons) * job.estimated_duration for job in jobs)

        return (
            total_wagon_time
            / (total_transport_time * max(len(job.wagons) for job in jobs))
            if total_transport_time > 0
            else 0.0
        )

    def _calculate_route_efficiency(self, jobs: list[TransportJob]) -> float:
        """Calculate route efficiency (fewer jobs = higher efficiency)."""
        if not jobs:
            return 1.0

        # Efficiency decreases with more jobs (more complex routing)
        return 1.0 / len(jobs)

    def validate_transport_plan(
        self,
        plan: TransportPlan,
        max_duration: float | None = None,
        min_utilization: float = 0.5,
    ) -> tuple[bool, list[str]]:
        """Validate transport plan meets requirements."""
        issues = []

        if max_duration and plan.total_duration > max_duration:
            issues.append(
                f"Total duration {plan.total_duration:.1f} exceeds limit {max_duration:.1f}"
            )

        if plan.locomotive_utilization < min_utilization:
            issues.append(
                f"Locomotive utilization {plan.locomotive_utilization:.2f} below minimum {min_utilization:.2f}"
            )

        return len(issues) == 0, issues
