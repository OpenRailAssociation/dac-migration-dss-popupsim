"""Hybrid rake formation service combining strategic and tactical approaches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shared.domain.services.rake_formation_service import RakeFormationService
from shared.domain.value_objects.rake_type import RakeType

if TYPE_CHECKING:
    from shared.domain.entities.rake import Rake
    from shared.domain.entities.wagon import Wagon


@dataclass
class FormationContext:
    """Context for rake formation decisions."""

    available_wagons: list[Wagon]
    planned_wagons: list[Wagon] | None
    workshop_capacities: dict[str, int]
    completion_tolerance: float = 0.1  # 10% tolerance


class HybridRakeFormationService:
    """Hybrid service combining strategic planning with tactical adaptation."""

    def __init__(self) -> None:
        self._strategic_planner = RakeFormationService()

    def form_rakes(
        self, context: FormationContext, rake_type: RakeType = RakeType.WORKSHOP_RAKE
    ) -> list[Rake]:
        """Form rakes using hybrid approach."""
        if self._should_use_strategic_plan(context):
            return self._execute_strategic_plan(context, rake_type)
        return self._execute_tactical_fallback(context, rake_type)

    def _should_use_strategic_plan(self, context: FormationContext) -> bool:
        """Decide whether to use strategic plan or tactical fallback."""
        if not context.planned_wagons:
            return False  # No plan available

        # Check if planned wagons are actually available
        planned_count = len(context.planned_wagons)
        available_count = len(context.available_wagons)

        # Use strategic plan if available wagons match plan within tolerance
        tolerance_threshold = planned_count * context.completion_tolerance
        return abs(available_count - planned_count) <= tolerance_threshold

    def _execute_strategic_plan(
        self, context: FormationContext, rake_type: RakeType
    ) -> list[Rake]:
        """Execute strategic pre-planned rake formation."""
        constraints = {
            "workshop_capacities": context.workshop_capacities,
            "group_by_cargo": False,
        }

        rakes = self._strategic_planner.form_rakes(
            context.available_wagons, "workshop_capacity", constraints
        )

        # Update rake types
        for rake in rakes:
            rake.rake_type = rake_type

        return rakes

    def _execute_tactical_fallback(
        self, context: FormationContext, rake_type: RakeType
    ) -> list[Rake]:
        """Execute tactical immediate rake formation (MVP pattern)."""
        rakes = []
        remaining_wagons = list(context.available_wagons)

        # Group wagons by workshop using immediate break pattern
        for workshop_id, capacity in context.workshop_capacities.items():
            if not remaining_wagons:
                break

            # Collect up to capacity wagons (immediate break if not enough)
            workshop_wagons = []
            for _ in range(capacity):
                if remaining_wagons:
                    wagon = remaining_wagons.pop(0)
                    workshop_wagons.append(wagon)
                else:
                    break  # Immediate break - MVP pattern

            if workshop_wagons:
                rake = self._strategic_planner.form_transport_rake(
                    workshop_wagons, "collection", workshop_id
                )
                rake.rake_type = rake_type
                rakes.append(rake)

        # Handle remaining wagons (overflow)
        if remaining_wagons:
            # Assign to workshop with most remaining capacity
            best_workshop = max(
                context.workshop_capacities.keys(),
                key=lambda w: context.workshop_capacities[w],
            )

            overflow_rake = self._strategic_planner.form_transport_rake(
                remaining_wagons, "collection", best_workshop
            )
            overflow_rake.rake_type = rake_type
            rakes.append(overflow_rake)

        return rakes

    def get_formation_strategy(self, context: FormationContext) -> str:
        """Get the formation strategy that would be used."""
        return "strategic" if self._should_use_strategic_plan(context) else "tactical"
