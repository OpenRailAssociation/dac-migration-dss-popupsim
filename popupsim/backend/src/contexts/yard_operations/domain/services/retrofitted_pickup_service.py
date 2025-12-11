"""Domain service for retrofitted wagon pickup operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

from shared.domain.services.rake_formation_service import RakeFormationService

if TYPE_CHECKING:
    from shared.domain.entities.rake import Rake
    from shared.domain.entities.wagon import Wagon


@dataclass
class RetrofittedPickupPlan:
    """Plan for picking up retrofitted wagons using rakes."""

    pickup_rakes: list[Rake]
    total_wagon_count: int
    estimated_duration: float
    required_locomotives: int


class RetrofittedPickupService:
    """Domain service for retrofitted wagon pickup operations - pure business logic."""

    def __init__(self) -> None:
        self._rake_formation_service = RakeFormationService()

    def create_pickup_plan(
        self,
        completed_wagons_by_workshop: dict[str, list[Wagon]],
        workshop_capacities: dict[str, int] | None = None,
    ) -> RetrofittedPickupPlan:
        """Create optimized pickup plan for completed wagons."""
        if not completed_wagons_by_workshop:
            return RetrofittedPickupPlan(
                pickup_rakes=[],
                total_wagon_count=0,
                estimated_duration=0.0,
                required_locomotives=0,
            )

        # Form retrofitted rakes using existing rake formation
        pickup_rakes = []
        for workshop_id, wagons in completed_wagons_by_workshop.items():
            if wagons:
                rake = self._rake_formation_service.form_retrofitted_rake(wagons, workshop_id)
                pickup_rakes.append(rake)

        # Optimize pickup sequence
        optimized_rakes = self._optimize_pickup_sequence(pickup_rakes, workshop_capacities)

        total_wagon_count = sum(rake.wagon_count for rake in optimized_rakes)
        estimated_duration = self._estimate_pickup_duration(optimized_rakes)
        required_locomotives = self._calculate_locomotive_requirements(optimized_rakes)

        return RetrofittedPickupPlan(
            pickup_rakes=optimized_rakes,
            total_wagon_count=total_wagon_count,
            estimated_duration=estimated_duration,
            required_locomotives=required_locomotives,
        )

    def _optimize_pickup_sequence(
        self, pickup_rakes: list[Rake], workshop_capacities: dict[str, int] | None
    ) -> list[Rake]:
        """Optimize pickup sequence based on workshop capacity and efficiency."""
        if not workshop_capacities:
            return pickup_rakes

        # Sort by workshop capacity (smaller workshops first for faster turnaround)
        return sorted(
            pickup_rakes,
            key=lambda rake: workshop_capacities.get(rake.formation_track, 1),
        )

    def _calculate_locomotive_requirements(self, pickup_rakes: list[Rake]) -> int:
        """Calculate locomotive requirements based on MVP pattern."""
        if not pickup_rakes:
            return 0

        # MVP processes one workshop at a time sequentially
        return 1  # One locomotive per pickup operation

    def _estimate_pickup_duration(self, pickup_rakes: list[Rake], process_times: Any = None) -> float:
        """Estimate duration using actual process times from scenario."""
        if not pickup_rakes:
            return 0.0

        # Use process times from scenario if available
        if process_times:
            coupling_time = getattr(process_times, 'get_coupling_ticks', lambda _: 1.0)('DAC')
            move_time = getattr(process_times, 'wagon_move_to_next_station', 0.5)
            base_time = coupling_time + move_time
        else:
            base_time = 1.5  # Default fallback

        # MVP uses workshop.retrofit_stations as batch size
        return len(pickup_rakes) * base_time

    def validate_pickup_feasibility(
        self,
        pickup_plan: RetrofittedPickupPlan,
        available_locomotives: int,
        track_capacity: float | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate pickup plan feasibility with business constraints."""
        issues = []

        if pickup_plan.required_locomotives > available_locomotives:
            issues.append(
                f'Insufficient locomotives: need {pickup_plan.required_locomotives}, have {available_locomotives}'
            )

        if track_capacity and pickup_plan.total_wagon_count > track_capacity:
            issues.append(f'Track capacity exceeded: {pickup_plan.total_wagon_count} > {track_capacity}')

        if not pickup_plan.pickup_rakes:
            issues.append('No rakes to pickup')

        return len(issues) == 0, issues

    def determine_pickup_priority(self, wagon_count: int, workshop_capacity: int) -> float:
        """Calculate pickup priority based on MVP logic."""
        # MVP uses workshop.retrofit_stations as batch size
        # Priority = how close to full batch capacity
        return wagon_count / workshop_capacity if workshop_capacity > 0 else 0
