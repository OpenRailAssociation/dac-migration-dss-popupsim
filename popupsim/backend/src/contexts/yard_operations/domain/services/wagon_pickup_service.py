"""Domain service for wagon pickup operations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shared.domain.entities.rake import Rake
from shared.domain.value_objects.rake_type import RakeType

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


@dataclass
class PickupPlan:
    """Plan for picking up wagons from collection tracks."""

    rakes_to_pickup: list[Rake]
    total_wagon_count: int
    estimated_duration: float
    pickup_sequence: list[str]  # Track sequence for pickup


@dataclass
class WorkshopAllocation:
    """Allocation of wagons to workshops."""

    workshop_id: str
    allocated_wagons: list[Wagon]
    capacity_used: int
    remaining_capacity: int


class WagonPickupService:
    """Domain service for wagon pickup operations - pure business logic."""

    def create_pickup_plan(
        self,
        available_wagons: list[Wagon],
        workshop_capacities: dict[str, int],
    ) -> PickupPlan:
        """Create optimal pickup plan for available wagons."""
        if not available_wagons:
            return PickupPlan(
                rakes_to_pickup=[],
                total_wagon_count=0,
                estimated_duration=0.0,
                pickup_sequence=[],
            )

        # Keep wagons in original sequence - assign workshops round-robin
        workshop_ids = list(workshop_capacities.keys())
        for i, wagon in enumerate(available_wagons):
            wagon.workshop_id = workshop_ids[i % len(workshop_ids)]

        # Create single rake with all wagons in sequence
        rake = Rake(
            rake_id=f"pickup_rake_{int(time.time() * 1000)}",
            wagons=available_wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track="collection",
            target_track="retrofit",
        )
        rake.assign_to_wagons()
        rakes = [rake]

        # Determine pickup sequence (optimize for efficiency)
        pickup_sequence = self._optimize_pickup_sequence(rakes)

        # Estimate duration based on rake count and complexity
        estimated_duration = self._estimate_pickup_duration(rakes)

        return PickupPlan(
            rakes_to_pickup=rakes,
            total_wagon_count=len(available_wagons),
            estimated_duration=estimated_duration,
            pickup_sequence=pickup_sequence,
        )

    def _allocate_wagons_to_workshops(
        self, wagons: list[Wagon], workshop_capacities: dict[str, int]
    ) -> list[WorkshopAllocation]:
        """Allocate wagons to workshops based on capacity."""
        allocations = []
        remaining_wagons = list(wagons)

        for workshop_id, capacity in workshop_capacities.items():
            if not remaining_wagons:
                break

            # Take up to capacity wagons for this workshop
            allocated_count = min(capacity, len(remaining_wagons))
            allocated_wagons = remaining_wagons[:allocated_count]
            remaining_wagons = remaining_wagons[allocated_count:]

            allocation = WorkshopAllocation(
                workshop_id=workshop_id,
                allocated_wagons=allocated_wagons,
                capacity_used=allocated_count,
                remaining_capacity=capacity - allocated_count,
            )
            allocations.append(allocation)

        # Handle overflow wagons (assign to workshop with most remaining capacity)
        if remaining_wagons and allocations:
            best_allocation = max(allocations, key=lambda a: a.remaining_capacity)
            best_allocation.allocated_wagons.extend(remaining_wagons)
            best_allocation.capacity_used += len(remaining_wagons)
            best_allocation.remaining_capacity = max(
                0, best_allocation.remaining_capacity - len(remaining_wagons)
            )

        return allocations

    def _create_workshop_rake(self, allocation: WorkshopAllocation) -> Rake:
        """Create rake for workshop allocation - goes to retrofit staging first."""
        rake = Rake(
            rake_id=f"pickup_rake_{allocation.workshop_id}_{int(time.time() * 1000)}",
            wagons=allocation.allocated_wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track="collection",
            target_track="retrofit",  # Go to retrofit staging track first
        )
        # Store workshop_id for later transport to workshop
        for wagon in allocation.allocated_wagons:
            wagon.workshop_id = allocation.workshop_id

        rake.assign_to_wagons()
        return rake

    def create_single_retrofit_rake(
        self, wagons: list[Wagon], workshop_allocations: dict[str, list[Wagon]]
    ) -> Rake:
        """Create single rake to retrofit track, with workshop assignments stored on wagons."""
        rake = Rake(
            rake_id=f"retrofit_rake_{int(time.time() * 1000)}",
            wagons=wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track="collection",
            target_track="retrofit",
        )
        # Store workshop assignments on wagons
        for workshop_id, workshop_wagons in workshop_allocations.items():
            for wagon in workshop_wagons:
                wagon.workshop_id = workshop_id

        rake.assign_to_wagons()
        return rake

    def _optimize_pickup_sequence(self, rakes: list[Rake]) -> list[str]:
        """Optimize pickup sequence for efficiency."""
        # Simple optimization: process by target workshop order
        return sorted({rake.target_track for rake in rakes})

    def _estimate_pickup_duration(self, rakes: list[Rake]) -> float:
        """Estimate total duration for pickup operations."""
        if not rakes:
            return 0.0

        # Base time per rake + time per wagon
        base_time_per_rake = 5.0  # minutes
        time_per_wagon = 0.5  # minutes

        total_duration = 0.0
        for rake in rakes:
            total_duration += base_time_per_rake + (rake.wagon_count * time_per_wagon)

        return total_duration

    def validate_pickup_feasibility(
        self,
        pickup_plan: PickupPlan,
        available_locomotives: int,
        time_constraints: dict[str, float] | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate if pickup plan is feasible given constraints."""
        issues = []

        # Check locomotive availability
        if len(pickup_plan.rakes_to_pickup) > available_locomotives:
            issues.append(
                f"Insufficient locomotives: need {len(pickup_plan.rakes_to_pickup)}, have {available_locomotives}"
            )

        # Check time constraints
        if time_constraints and "max_pickup_time" in time_constraints:
            max_time = time_constraints["max_pickup_time"]
            if pickup_plan.estimated_duration > max_time:
                issues.append(
                    f"Pickup duration {pickup_plan.estimated_duration:.1f} exceeds limit {max_time:.1f}"
                )

        return len(issues) == 0, issues
