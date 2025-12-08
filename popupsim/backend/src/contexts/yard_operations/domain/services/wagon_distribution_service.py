"""Wagon distribution service for yard operations."""

from shared.domain.entities.wagon import Wagon


class WagonDistributionService:
    """Service for distributing wagons to workshops."""

    def distribute_wagons(
        self, available_wagons: list[Wagon], workshop_capacities: dict[str, int]
    ) -> dict[str, list[Wagon]]:
        """Distribute wagons to workshops based on capacity."""
        distribution: dict[str, list[Wagon]] = {
            ws_id: [] for ws_id in workshop_capacities
        }

        for wagon in available_wagons:
            # Find workshop with most available capacity
            best_workshop = max(
                workshop_capacities.keys(),
                key=lambda ws_id: workshop_capacities[ws_id] - len(distribution[ws_id]),
            )

            if workshop_capacities[best_workshop] > len(distribution[best_workshop]):
                distribution[best_workshop].append(wagon)

        return distribution
