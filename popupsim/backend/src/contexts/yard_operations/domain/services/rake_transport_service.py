"""Domain service for rake transport operations in yard context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from shared.domain.entities.rake import Rake


class TransportPriority(Enum):
    """Priority levels for rake transport."""

    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'


@dataclass
class TransportJob:
    """Transport job for moving a rake."""

    rake: Rake
    from_track: str
    to_track: str
    priority: TransportPriority
    estimated_duration: float
    requires_locomotive: bool = True


@dataclass
class TransportSchedule:
    """Schedule for executing transport jobs."""

    jobs: list[TransportJob]
    total_duration: float
    locomotive_requirements: int
    execution_sequence: list[str]  # Job IDs in execution order


class RakeTransportService:
    """Domain service for rake transport operations - pure business logic."""

    def create_transport_schedule(
        self,
        rakes: list[Rake],
        available_locomotives: int,
        priority_rules: dict[str, TransportPriority] | None = None,
    ) -> TransportSchedule:
        """Create optimal transport schedule for rakes."""
        if not rakes:
            return TransportSchedule(
                jobs=[],
                total_duration=0.0,
                locomotive_requirements=0,
                execution_sequence=[],
            )

        # Create transport jobs
        jobs = []
        for rake in rakes:
            priority = self._determine_priority(rake, priority_rules)
            duration = self._estimate_transport_duration(rake)

            job = TransportJob(
                rake=rake,
                from_track=rake.formation_track,
                to_track=rake.target_track,
                priority=priority,
                estimated_duration=duration,
                requires_locomotive=True,
            )
            jobs.append(job)

        # Optimize execution sequence
        execution_sequence = self._optimize_execution_sequence(jobs)

        # Calculate total duration considering parallel execution
        total_duration = self._calculate_total_duration(jobs, available_locomotives)

        return TransportSchedule(
            jobs=jobs,
            total_duration=total_duration,
            locomotive_requirements=min(len(jobs), available_locomotives),
            execution_sequence=execution_sequence,
        )

    def _determine_priority(self, rake: Rake, priority_rules: dict[str, TransportPriority] | None) -> TransportPriority:
        """Determine transport priority for rake."""
        if not priority_rules:
            return TransportPriority.NORMAL

        # Check workshop-specific priorities
        if rake.target_track in priority_rules:
            return priority_rules[rake.target_track]

        # Check rake type priorities
        rake_type_key = f'rake_type_{rake.rake_type.value}'
        if rake_type_key in priority_rules:
            return priority_rules[rake_type_key]

        return TransportPriority.NORMAL

    def _estimate_transport_duration(self, rake: Rake) -> float:
        """Estimate duration for transporting rake."""
        # Base transport time + time per wagon
        base_time = 3.0  # minutes for locomotive allocation and movement
        coupling_time = 1.0  # minutes for coupling/decoupling
        transport_time = 2.0  # minutes for actual movement
        wagon_factor = rake.wagon_count * 0.2  # additional time per wagon

        return base_time + coupling_time + transport_time + wagon_factor

    def _optimize_execution_sequence(self, jobs: list[TransportJob]) -> list[str]:
        """Optimize execution sequence for transport jobs."""
        # Sort by priority first, then by estimated duration
        priority_order = {
            TransportPriority.URGENT: 0,
            TransportPriority.HIGH: 1,
            TransportPriority.NORMAL: 2,
            TransportPriority.LOW: 3,
        }

        sorted_jobs = sorted(
            jobs,
            key=lambda job: (
                priority_order[job.priority],
                job.estimated_duration,  # Shorter jobs first within same priority
            ),
        )

        return [job.rake.rake_id for job in sorted_jobs]

    def _calculate_total_duration(self, jobs: list[TransportJob], available_locomotives: int) -> float:
        """Calculate total duration considering parallel execution."""
        if not jobs:
            return 0.0

        if available_locomotives >= len(jobs):
            # All jobs can run in parallel
            return max(job.estimated_duration for job in jobs)

        # Sequential execution with limited locomotives
        total_duration = sum(job.estimated_duration for job in jobs)

        # Apply parallelization factor
        parallelization_factor = min(available_locomotives, len(jobs)) / len(jobs)
        return total_duration * (1.0 - parallelization_factor + parallelization_factor / available_locomotives)

    def validate_transport_feasibility(
        self,
        schedule: TransportSchedule,
        track_constraints: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate if transport schedule is feasible."""
        issues = []

        # Check track capacity constraints
        if track_constraints:
            track_usage: dict[str, float] = {}
            for job in schedule.jobs:
                # Check source track
                if job.from_track in track_constraints:
                    constraints = track_constraints[job.from_track]
                    if 'max_concurrent_operations' in constraints:
                        track_usage[job.from_track] = track_usage.get(job.from_track, 0) + 1
                        if track_usage[job.from_track] > constraints['max_concurrent_operations']:
                            issues.append(f'Track {job.from_track} exceeds concurrent operation limit')

                # Check destination track
                if job.to_track in track_constraints:
                    constraints = track_constraints[job.to_track]
                    if 'max_concurrent_arrivals' in constraints:
                        track_usage[job.to_track] = track_usage.get(job.to_track, 0) + 1
                        if track_usage[job.to_track] > constraints['max_concurrent_arrivals']:
                            issues.append(f'Track {job.to_track} exceeds concurrent arrival limit')

        # Check locomotive requirements
        if schedule.locomotive_requirements == 0 and schedule.jobs:
            issues.append('No locomotives available for transport operations')

        return len(issues) == 0, issues

    def calculate_workshop_delivery_times(self, schedule: TransportSchedule) -> dict[str, float]:
        """Calculate expected delivery times for each workshop."""
        delivery_times = {}
        current_time = 0.0

        for job_id in schedule.execution_sequence:
            job = next(job for job in schedule.jobs if job.rake.rake_id == job_id)
            current_time += job.estimated_duration

            if job.to_track not in delivery_times:
                delivery_times[job.to_track] = current_time
            else:
                # Update with latest delivery time for this workshop
                delivery_times[job.to_track] = max(delivery_times[job.to_track], current_time)

        return delivery_times
