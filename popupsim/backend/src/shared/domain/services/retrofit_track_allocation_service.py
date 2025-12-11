"""Domain service for allocating wagons to retrofit tracks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


@dataclass
class RetrofitAllocation:
    """Result of retrofit track allocation."""

    track_assignments: dict[str, list[Wagon]]  # {track_id: wagons}
    overflow_wagons: list[Wagon]
    total_capacity_used: float
    allocation_efficiency: float


class RetrofitTrackAllocationService:
    """Domain service for allocating wagons to retrofit tracks."""

    def allocate_wagons(
        self,
        wagons: list[Wagon],
        available_tracks: dict[str, float],  # {track_id: available_capacity}
    ) -> RetrofitAllocation:
        """Allocate wagons to retrofit tracks optimally."""
        if not wagons or not available_tracks:
            return RetrofitAllocation(
                track_assignments={},
                overflow_wagons=wagons,
                total_capacity_used=0.0,
                allocation_efficiency=0.0,
            )

        assignments = {}
        remaining_wagons = list(wagons)

        # Sort tracks by available capacity (largest first)
        sorted_tracks = sorted(available_tracks.items(), key=lambda x: x[1], reverse=True)

        for track_id, capacity in sorted_tracks:
            if not remaining_wagons:
                break

            # Calculate how many wagons fit
            track_wagons = []
            used_capacity = 0.0

            for wagon in remaining_wagons[:]:
                wagon_length = getattr(wagon, 'length', 10.0)
                if used_capacity + wagon_length <= capacity:
                    track_wagons.append(wagon)
                    used_capacity += wagon_length
                    remaining_wagons.remove(wagon)

            if track_wagons:
                assignments[track_id] = track_wagons

        total_wagons = len(wagons)
        allocated_wagons = total_wagons - len(remaining_wagons)

        return RetrofitAllocation(
            track_assignments=assignments,
            overflow_wagons=remaining_wagons,
            total_capacity_used=float(allocated_wagons),
            allocation_efficiency=allocated_wagons / total_wagons if total_wagons > 0 else 0.0,
        )

    def validate_allocation(
        self, allocation: RetrofitAllocation, min_efficiency: float = 0.8
    ) -> tuple[bool, list[str]]:
        """Validate allocation meets requirements."""
        issues = []

        if allocation.allocation_efficiency < min_efficiency:
            issues.append(
                f'Allocation efficiency {allocation.allocation_efficiency:.2f} below minimum {min_efficiency:.2f}'
            )

        if allocation.overflow_wagons:
            issues.append(f'{len(allocation.overflow_wagons)} wagons could not be allocated')

        return len(issues) == 0, issues
