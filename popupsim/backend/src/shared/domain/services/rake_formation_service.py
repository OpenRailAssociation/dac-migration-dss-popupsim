"""Service for forming rakes from wagons."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from typing import Any

from shared.domain.entities.rake import Rake
from shared.domain.services.rake_formation_strategy import FixedSizeStrategy
from shared.domain.services.rake_formation_strategy import RakeFormationStrategy
from shared.domain.services.rake_formation_strategy import TrackCapacityStrategy
from shared.domain.services.rake_formation_strategy import WorkshopCapacityStrategy
from shared.domain.services.retrofit_track_strategy import RetrofitTrackStrategy
from shared.domain.value_objects.rake_type import RakeType

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


class RakeFormationService:
    """Service for forming different types of rakes using various strategies."""

    def __init__(self) -> None:
        self._strategies = {
            'workshop_capacity': WorkshopCapacityStrategy(),
            'track_capacity': TrackCapacityStrategy(),
            'fixed_size': FixedSizeStrategy(),
            'retrofit_tracks': RetrofitTrackStrategy(),
        }

    def form_rakes(self, wagons: list[Wagon], strategy: str, constraints: dict[str, Any]) -> list[Any]:
        """Form rakes using specified strategy and constraints."""
        if strategy not in self._strategies:
            msg = f'Unknown strategy: {strategy}. Available: {list(self._strategies.keys())}'
            raise ValueError(msg)

        strategy_impl = self._strategies[strategy]
        return strategy_impl.form_rakes(wagons, constraints)

    def form_workshop_rakes(
        self,
        wagons: list[Wagon],
        workshop_capacities: dict[str, int],
        group_by_cargo: bool = False,
    ) -> list[Rake]:
        """Form rakes optimized for workshop processing (backward compatibility)."""
        constraints = {
            'workshop_capacities': workshop_capacities,
            'group_by_cargo': group_by_cargo,
        }
        return self.form_rakes(wagons, 'workshop_capacity', constraints)

    def form_collection_rakes(self, wagons: list[Wagon], track_capacity: float) -> list[Rake]:
        """Form rakes for collection tracks based on track capacity."""
        constraints = {
            'track_capacity': track_capacity,
            'formation_track': 'collection',
            'rake_type': RakeType.COLLECTION_RAKE,
        }
        return self.form_rakes(wagons, 'track_capacity', constraints)

    def form_retrofit_rakes(self, wagons: list[Wagon], retrofit_track_capacity: float) -> list[Rake]:
        """Form rakes sized for retrofit track capacity."""
        constraints = {
            'track_capacity': retrofit_track_capacity,
            'formation_track': 'collection',
            'rake_type': RakeType.TRANSPORT_RAKE,
        }
        return self.form_rakes(wagons, 'track_capacity', constraints)

    def add_strategy(self, name: str, strategy: RakeFormationStrategy) -> None:
        """Add custom rake formation strategy."""
        self._strategies[name] = strategy

    def form_transport_rake(self, wagons: list[Wagon], from_track: str, to_track: str) -> Rake:
        """Form a transport rake for moving wagons between tracks."""
        rake = Rake(
            rake_id=f'transport_rake_{from_track}_{to_track}_{int(time.time())}',
            wagons=wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track=from_track,
            target_track=to_track,
        )

        rake.assign_to_wagons()
        return rake

    def form_retrofitted_rake(self, wagons: list[Wagon], workshop_id: str) -> Rake:
        """Form a retrofitted rake from completed workshop wagons."""
        rake = Rake(
            rake_id=f'retrofitted_rake_{workshop_id}_{int(time.time())}',
            wagons=wagons,
            rake_type=RakeType.RETROFITTED_RAKE,
            formation_time=time.time(),
            formation_track=workshop_id,
            target_track='retrofitted',
        )

        rake.assign_to_wagons()
        return rake

    def form_retrofit_track_rakes(
        self,
        wagons: list[Wagon],
        retrofit_tracks: dict[str, float],
        from_track: str = 'collection',
    ) -> list[Rake]:
        """Form rakes optimized for retrofit track capacities (convenience method)."""
        constraints = {
            'retrofit_tracks': retrofit_tracks,
            'from_track': from_track,
        }
        return self.form_rakes(wagons, 'retrofit_tracks', constraints)
