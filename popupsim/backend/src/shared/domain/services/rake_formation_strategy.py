"""Rake formation strategies for different scenarios."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import time
from typing import TYPE_CHECKING

from shared.domain.entities.rake import Rake
from shared.domain.value_objects.rake_type import RakeType

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


class RakeFormationStrategy(ABC):  # pylint: disable=too-few-public-methods
    """Abstract base class for rake formation strategies."""

    @abstractmethod
    def form_rakes(self, wagons: list[Wagon], constraints: dict[str, any]) -> list[Rake]:
        """Form rakes based on strategy-specific logic."""


class WorkshopCapacityStrategy(RakeFormationStrategy):  # pylint: disable=too-few-public-methods
    """Form rakes based on workshop bay capacity (MVP algorithm)."""

    def form_rakes(self, wagons: list[Wagon], constraints: dict[str, any]) -> list[Rake]:
        """Form rakes optimized for workshop bay capacity."""
        workshop_capacities = constraints.get('workshop_capacities', {})
        group_by_cargo = constraints.get('group_by_cargo', False)

        if not workshop_capacities:
            msg = "WorkshopCapacityStrategy requires 'workshop_capacities' constraint"
            raise ValueError(msg)

        rakes = []

        # Group by cargo type if requested
        if group_by_cargo:
            cargo_groups = self._group_by_cargo(wagons)
            for cargo_wagons in cargo_groups.values():
                cargo_rakes = self._form_workshop_rakes(cargo_wagons, workshop_capacities, len(rakes))
                rakes.extend(cargo_rakes)
        else:
            rakes = self._form_workshop_rakes(wagons, workshop_capacities, 0)

        return rakes

    def _group_by_cargo(self, wagons: list[Wagon]) -> dict[str, list[Wagon]]:
        """Group wagons by cargo type."""
        cargo_groups = {}
        for wagon in wagons:
            cargo_type = getattr(wagon, 'cargo_type', 'general')
            if cargo_type not in cargo_groups:
                cargo_groups[cargo_type] = []
            cargo_groups[cargo_type].append(wagon)
        return cargo_groups

    def _form_workshop_rakes(
        self, wagons: list[Wagon], workshop_capacities: dict[str, int], rake_offset: int
    ) -> list[Rake]:
        """Form rakes using MVP's capacity-based algorithm."""
        rakes = []
        remaining_wagons = list(wagons)

        while remaining_wagons:
            # Find best workshop (capacity-based algorithm from MVP)
            best_workshop = self._find_optimal_workshop(workshop_capacities, rakes)

            # Calculate available capacity
            current_allocation = sum(rake.wagon_count for rake in rakes if rake.target_track == best_workshop)
            available_capacity = workshop_capacities[best_workshop] - current_allocation

            # Handle overflow - all remaining wagons go to best workshop
            if available_capacity <= 0:
                rake_size = len(remaining_wagons)
            else:
                rake_size = min(available_capacity, len(remaining_wagons))

            rake_wagons = remaining_wagons[:rake_size]

            rake = Rake(
                rake_id=f'workshop_rake_{best_workshop}_{len(rakes) + rake_offset}',
                wagons=rake_wagons,
                rake_type=RakeType.WORKSHOP_RAKE,
                formation_time=time.time(),
                formation_track='classification',
                target_track=best_workshop,
            )

            rake.assign_to_wagons()
            rakes.append(rake)
            remaining_wagons = remaining_wagons[rake_size:]

        return rakes

    def _find_optimal_workshop(self, workshop_capacities: dict[str, int], existing_rakes: list[Rake]) -> str:
        """Find optimal workshop using MVP's capacity-based algorithm."""
        capacity_claims = dict.fromkeys(workshop_capacities.keys(), 0)

        for rake in existing_rakes:
            if rake.target_track and rake.target_track in capacity_claims:
                capacity_claims[rake.target_track] += rake.wagon_count

        # Find workshop with most available capacity
        return max(
            workshop_capacities.keys(),
            key=lambda ws_id: workshop_capacities[ws_id] - capacity_claims[ws_id],
        )


class TrackCapacityStrategy(RakeFormationStrategy):  # pylint: disable=too-few-public-methods
    """Form rakes based on track length/capacity constraints."""

    def form_rakes(self, wagons: list[Wagon], constraints: dict[str, any]) -> list[Rake]:
        """Form rakes optimized for track capacity."""
        track_capacity = constraints.get('track_capacity', 100.0)  # Default 100m
        formation_track = constraints.get('formation_track', 'collection')
        rake_type = constraints.get('rake_type', RakeType.COLLECTION_RAKE)

        rakes = []
        current_length = 0.0
        current_wagons = []

        for wagon in wagons:
            wagon_length = getattr(wagon, 'length', 10.0)

            if current_length + wagon_length <= track_capacity:
                current_wagons.append(wagon)
                current_length += wagon_length
            else:
                # Complete current rake
                if current_wagons:
                    rake = self._create_rake(current_wagons, formation_track, rake_type, len(rakes))
                    rakes.append(rake)

                # Start new rake
                current_wagons = [wagon]
                current_length = wagon_length

        # Complete final rake
        if current_wagons:
            rake = self._create_rake(current_wagons, formation_track, rake_type, len(rakes))
            rakes.append(rake)

        return rakes

    def _create_rake(
        self,
        wagons: list[Wagon],
        formation_track: str,
        rake_type: RakeType,
        rake_number: int,
    ) -> Rake:
        """Create a rake with specified parameters."""
        rake = Rake(
            rake_id=f'{rake_type.value}_rake_{rake_number}',
            wagons=wagons,
            rake_type=rake_type,
            formation_time=time.time(),
            formation_track=formation_track,
        )

        rake.assign_to_wagons()
        return rake


class FixedSizeStrategy(RakeFormationStrategy):  # pylint: disable=too-few-public-methods
    """Form rakes with fixed number of wagons."""

    def form_rakes(self, wagons: list[Wagon], constraints: dict[str, any]) -> list[Rake]:
        """Form rakes with fixed size."""
        rake_size = constraints.get('rake_size', 5)
        formation_track = constraints.get('formation_track', 'yard')
        rake_type = constraints.get('rake_type', RakeType.TRANSPORT_RAKE)

        rakes = []
        remaining_wagons = list(wagons)

        while remaining_wagons:
            batch_size = min(rake_size, len(remaining_wagons))
            batch_wagons = remaining_wagons[:batch_size]

            rake = Rake(
                rake_id=f'fixed_rake_{len(rakes)}',
                wagons=batch_wagons,
                rake_type=rake_type,
                formation_time=time.time(),
                formation_track=formation_track,
            )

            rake.assign_to_wagons()
            rakes.append(rake)
            remaining_wagons = remaining_wagons[batch_size:]

        return rakes
