"""Retrofit track strategy for rake formation."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from shared.domain.entities.rake import Rake
from shared.domain.services.multi_track_transport_service import MultiTrackTransportService
from shared.domain.services.rake_formation_strategy import RakeFormationStrategy
from shared.domain.services.retrofit_track_allocation_service import RetrofitTrackAllocationService
from shared.domain.value_objects.rake_type import RakeType

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


class RetrofitTrackStrategy(RakeFormationStrategy):  # pylint: disable=too-few-public-methods
    """Form rakes optimized for retrofit track capacity."""

    def __init__(self) -> None:
        self.allocation_service = RetrofitTrackAllocationService()
        self.transport_service = MultiTrackTransportService()

    def form_rakes(self, wagons: list[Wagon], constraints: dict[str, any]) -> list[Rake]:
        """Form rakes based on retrofit track capacities."""
        retrofit_tracks = constraints.get('retrofit_tracks', {})
        from_track = constraints.get('from_track', 'collection')

        if not retrofit_tracks:
            # Fallback to single rake if no retrofit tracks specified
            return self._create_single_rake(wagons, from_track)

        # Allocate wagons to tracks
        allocation = self.allocation_service.allocate_wagons(wagons, retrofit_tracks)

        # Validate allocation
        is_valid, _issues = self.allocation_service.validate_allocation(allocation)
        if not is_valid:
            pass

        # Create transport plan
        transport_plan = self.transport_service.create_transport_plan(allocation, from_track)

        # Validate transport plan
        is_valid, _issues = self.transport_service.validate_transport_plan(transport_plan)
        if not is_valid:
            pass

        # Convert transport jobs to rakes
        rakes = []
        for job in transport_plan.transport_jobs:
            rake = self._create_transport_rake(job)
            rakes.append(rake)

        # Handle overflow wagons
        if allocation.overflow_wagons:
            overflow_rake = self._create_overflow_rake(allocation.overflow_wagons, from_track, retrofit_tracks)
            rakes.append(overflow_rake)

        return rakes

    def _create_transport_rake(self, job) -> Rake:
        """Create rake from transport job."""
        rake = Rake(
            rake_id=f'retrofit_rake_{job.to_track}_{int(time.time())}',
            wagons=job.wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track=job.from_track,
            target_track=job.to_track,
        )
        rake.assign_to_wagons()
        return rake

    def _create_single_rake(self, wagons: list[Wagon], from_track: str) -> list[Rake]:
        """Create single rake when no retrofit tracks specified."""
        if not wagons:
            return []

        rake = Rake(
            rake_id=f'single_retrofit_rake_{int(time.time())}',
            wagons=wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track=from_track,
            target_track='retrofit',  # Default retrofit track
        )
        rake.assign_to_wagons()
        return [rake]

    def _create_overflow_rake(self, wagons: list[Wagon], from_track: str, retrofit_tracks: dict[str, float]) -> Rake:
        """Create rake for overflow wagons (assign to track with most capacity)."""
        best_track = max(retrofit_tracks.keys(), key=lambda t: retrofit_tracks[t])

        rake = Rake(
            rake_id=f'overflow_rake_{best_track}_{int(time.time())}',
            wagons=wagons,
            rake_type=RakeType.TRANSPORT_RAKE,
            formation_time=time.time(),
            formation_track=from_track,
            target_track=best_track,
        )
        rake.assign_to_wagons()
        return rake
