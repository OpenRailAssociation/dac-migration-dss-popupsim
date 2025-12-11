"""Domain service for workshop processing operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


class ProcessingStrategy(Enum):
    """Processing strategies for workshop operations."""

    INDIVIDUAL = 'individual'
    BATCH = 'batch'
    RAKE = 'rake'


@dataclass
class ProcessingPlan:
    """Plan for processing wagons at workshop."""

    workshop_id: str
    processing_strategy: ProcessingStrategy
    wagon_groups: list[list[Wagon]]
    estimated_duration: float
    required_stations: int


class WorkshopProcessingService:
    """Domain service for workshop processing operations - pure business logic."""

    def create_processing_plan(
        self,
        wagons: list[Wagon],
        workshop_id: str,
        workshop_capacity: int,
        processing_strategy: ProcessingStrategy = ProcessingStrategy.BATCH,
    ) -> ProcessingPlan:
        """Create optimal processing plan for wagons."""
        if not wagons:
            return ProcessingPlan(
                workshop_id=workshop_id,
                processing_strategy=processing_strategy,
                wagon_groups=[],
                estimated_duration=0.0,
                required_stations=0,
            )

        wagon_groups = self._group_wagons_by_strategy(wagons, processing_strategy, workshop_capacity)
        required_stations = self._calculate_required_stations(wagon_groups, processing_strategy)
        estimated_duration = self._estimate_processing_duration(wagon_groups)

        return ProcessingPlan(
            workshop_id=workshop_id,
            processing_strategy=processing_strategy,
            wagon_groups=wagon_groups,
            estimated_duration=estimated_duration,
            required_stations=required_stations,
        )

    def _group_wagons_by_strategy(
        self, wagons: list[Wagon], strategy: ProcessingStrategy, workshop_capacity: int
    ) -> list[list[Wagon]]:
        """Group wagons according to processing strategy."""
        if strategy == ProcessingStrategy.INDIVIDUAL:
            return [[wagon] for wagon in wagons]

        if strategy == ProcessingStrategy.BATCH:
            groups = []
            current_group = []

            for wagon in wagons:
                if len(current_group) < workshop_capacity:
                    current_group.append(wagon)
                else:
                    groups.append(current_group)
                    current_group = [wagon]

            if current_group:
                groups.append(current_group)

            return groups

        if strategy == ProcessingStrategy.RAKE:
            rake_groups = {}
            for wagon in wagons:
                rake_id = getattr(wagon, 'rake_id', f'single_{wagon.id}')
                if rake_id not in rake_groups:
                    rake_groups[rake_id] = []
                rake_groups[rake_id].append(wagon)

            return list(rake_groups.values())

        return [wagons]

    def _calculate_required_stations(self, wagon_groups: list[list[Wagon]], strategy: ProcessingStrategy) -> int:
        """Calculate required workshop stations."""
        if not wagon_groups:
            return 0

        if strategy == ProcessingStrategy.INDIVIDUAL:
            return 1

        return max(len(group) for group in wagon_groups)

    def _estimate_processing_duration(self, wagon_groups: list[list[Wagon]]) -> float:
        """Estimate total processing duration."""
        if not wagon_groups:
            return 0.0

        base_time = 10.0  # minutes per wagon
        setup_time = 2.0  # minutes per group

        total_duration = 0.0
        for _group in wagon_groups:
            group_duration = base_time + setup_time
            total_duration += group_duration

        return total_duration

    def validate_processing_feasibility(
        self, processing_plan: ProcessingPlan, available_capacity: int
    ) -> tuple[bool, list[str]]:
        """Validate if processing plan is feasible."""
        issues = []

        if processing_plan.required_stations > available_capacity:
            issues.append(f'Insufficient capacity: need {processing_plan.required_stations}, have {available_capacity}')

        if not processing_plan.wagon_groups:
            issues.append('No wagon groups to process')

        return len(issues) == 0, issues
