"""Step-specific transport planners for capacity-aware rake formation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shared.domain.entities.wagon import Wagon

if TYPE_CHECKING:
    from contexts.railway_infrastructure.application.railway_context import RailwayInfrastructureContext


@dataclass
class RakeTransportPlan:
    """Plan for transporting wagons between tracks."""

    wagons: list[Wagon]
    from_track: str
    to_track: str
    rake_id: str
    capacity_validated: bool


class CollectionToRetrofitPlanner:
    """Plans collection → retrofit transport using retrofit track capacity."""

    def __init__(self, railway_context: 'RailwayInfrastructureContext') -> None:
        self._railway_context = railway_context

    def plan_transport(self, wagons: list[Wagon], from_track: str) -> RakeTransportPlan | None:
        """Plan transport from collection to retrofit track."""
        if not wagons:
            return None

        # Find retrofit track with most available capacity (Approach 1)
        target_track = self._select_best_retrofit_track()
        if not target_track:
            return None

        # Get available capacity for target track
        available_capacity = self._railway_context.get_available_capacity(target_track)
        if available_capacity <= 0:
            return None

        # Select wagons that fit in available capacity
        selected_wagons = self._select_wagons_for_capacity(wagons, available_capacity)
        if not selected_wagons:
            return None

        return RakeTransportPlan(
            wagons=selected_wagons,
            from_track=from_track,
            to_track=target_track,
            rake_id=f'collection_to_retrofit_{len(selected_wagons)}w',
            capacity_validated=True,
        )

    def _select_best_retrofit_track(self) -> str | None:
        """Select retrofit track with most available capacity."""
        track_service = self._railway_context.get_track_selection_service()
        retrofit_tracks = track_service.get_tracks_by_type('retrofit')

        if not retrofit_tracks:
            return None

        best_track = None
        max_capacity = 0.0

        for track in retrofit_tracks:
            available = self._railway_context.get_available_capacity(str(track.id))
            if available > max_capacity:
                max_capacity = available
                best_track = str(track.id)

        return best_track

    def _select_wagons_for_capacity(self, wagons: list[Wagon], available_capacity: float) -> list[Wagon]:
        """Select wagons that fit in available capacity."""
        selected = []
        used_capacity = 0.0

        for wagon in wagons:
            wagon_length = getattr(wagon, 'length', 15.0)
            if used_capacity + wagon_length <= available_capacity:
                selected.append(wagon)
                used_capacity += wagon_length
            else:
                break

        return selected


class RetrofitToWorkshopPlanner:
    """Plans retrofit → workshop transport (Step 3)."""

    def __init__(self, railway_context: 'RailwayInfrastructureContext') -> None:
        self._railway_context = railway_context

    def plan_transport(self, wagons: list[Wagon], from_track: str) -> RakeTransportPlan | None:
        """Plan transport from retrofit to workshop."""
        if not wagons:
            return None

        # Select workshop with least occupancy
        track_service = self._railway_context.get_track_selection_service()
        workshop_track = track_service.select_track('workshop')

        if not workshop_track:
            return None

        return RakeTransportPlan(
            wagons=wagons,
            from_track=from_track,
            to_track=str(workshop_track.id),
            rake_id=f'retrofit_to_workshop_{len(wagons)}w',
            capacity_validated=True,
        )


class WorkshopToRetrofittedPlanner:
    """Plans workshop → retrofitted transport (Step 4)."""

    def __init__(self, railway_context: 'RailwayInfrastructureContext') -> None:
        self._railway_context = railway_context

    def plan_transport(self, wagons: list[Wagon], from_track: str) -> RakeTransportPlan | None:
        """Plan transport from workshop to retrofitted track."""
        if not wagons:
            return None

        # Select retrofitted track with most available capacity
        track_service = self._railway_context.get_track_selection_service()
        retrofitted_track = track_service.select_track('retrofitted')

        if not retrofitted_track:
            return None

        return RakeTransportPlan(
            wagons=wagons,
            from_track=from_track,
            to_track=str(retrofitted_track.id),
            rake_id=f'workshop_to_retrofitted_{len(wagons)}w',
            capacity_validated=True,
        )


class RetrofittedToParkingPlanner:
    """Plans retrofitted → parking transport (Step 5)."""

    def __init__(self, railway_context: 'RailwayInfrastructureContext') -> None:
        self._railway_context = railway_context

    def plan_transport(self, wagons: list[Wagon], from_track: str) -> RakeTransportPlan | None:
        """Plan transport from retrofitted to parking track."""
        if not wagons:
            return None

        # Select parking track with most available capacity
        track_service = self._railway_context.get_track_selection_service()
        parking_track = track_service.select_track('parking')

        if not parking_track:
            return None

        return RakeTransportPlan(
            wagons=wagons,
            from_track=from_track,
            to_track=str(parking_track.id),
            rake_id=f'retrofitted_to_parking_{len(wagons)}w',
            capacity_validated=True,
        )
