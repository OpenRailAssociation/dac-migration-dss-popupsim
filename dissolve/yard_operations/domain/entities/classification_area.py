"""Classification area entity for hump yard operations."""

from workshop_operations.domain.entities.track import TrackType
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.infrastructure.resources.track_capacity_manager import (
    TrackCapacityManager,
)
from workshop_operations.infrastructure.resources.workshop_capacity_manager import (
    WorkshopCapacityManager,
)

from yard_operations.domain.value_objects.classification_decision import (
    ClassificationDecision,
)


class ClassificationArea:
    """Hump yard classification area for wagon sorting.

    Parameters
    ----------
    area_id : str
        Unique identifier for classification area
    track_capacity : TrackCapacityManager
        Track capacity manager for collection tracks
    workshop_capacity : WorkshopCapacityManager
        Workshop capacity manager for checking availability
    """

    def __init__(
        self,
        area_id: str,
        track_capacity: TrackCapacityManager,
        workshop_capacity: WorkshopCapacityManager,
    ) -> None:
        self.area_id = area_id
        self.track_capacity = track_capacity
        self.workshop_capacity = workshop_capacity

    def classify_wagon(self, wagon: Wagon) -> tuple[ClassificationDecision, str | None]:
        """Classify wagon and determine routing.

        Parameters
        ----------
        wagon : Wagon
            Wagon to classify

        Returns
        -------
        tuple[ClassificationDecision, str | None]
            Classification decision and collection track ID (if retrofit)
        """
        # Check if wagon needs retrofit
        if not wagon.needs_retrofit:
            return (ClassificationDecision.BYPASS, None)

        # Try to allocate collection track
        collection_track_id = self.track_capacity.select_collection_track(wagon.length)

        if collection_track_id:
            return (ClassificationDecision.RETROFIT, collection_track_id)

        # No capacity available
        return (ClassificationDecision.REJECT, None)

    def find_wagons_for_retrofit(
        self,
        collection_wagons: list[Wagon],
        tracks: list[object],  # type: ignore[type-arg]
    ) -> list[tuple[Wagon, str]]:
        """Find wagons that can be moved to retrofit tracks with available stations.

        Parameters
        ----------
        collection_wagons : list[Wagon]
            Wagons available on collection track
        tracks : list[object]
            All tracks in scenario

        Returns
        -------
        list[tuple[Wagon, str]]
            List of (wagon, retrofit_track_id) tuples for wagons that can be moved
        """
        wagons_to_pickup = []
        retrofit_tracks = [t for t in tracks if t.type == TrackType.RETROFIT]  # type: ignore[union-attr,attr-defined]

        for wagon in collection_wagons:
            for retrofit_track in retrofit_tracks:
                retrofit_track_id = retrofit_track.id  # type: ignore[attr-defined]

                # Check if any workshop has capacity
                has_workshop_capacity = any(
                    self.workshop_capacity.get_available_stations(w.track) > 0
                    for w in self.workshop_capacity.workshops_by_track.values()
                )

                if has_workshop_capacity and self.track_capacity.can_add_wagon(
                    retrofit_track_id, wagon.length
                ):
                    wagons_to_pickup.append((wagon, retrofit_track_id))
                    break

        return wagons_to_pickup

    def group_wagons_by_retrofit_track(
        self, wagons_to_pickup: list[tuple[Wagon, str]]
    ) -> dict[str, list[Wagon]]:
        """Group wagons by their destination retrofit track.

        Parameters
        ----------
        wagons_to_pickup : list[tuple[Wagon, str]]
            List of (wagon, retrofit_track_id) tuples

        Returns
        -------
        dict[str, list[Wagon]]
            Dictionary mapping retrofit track IDs to lists of wagons
        """
        result: dict[str, list[Wagon]] = {}
        for wagon, track_id in wagons_to_pickup:
            if track_id not in result:
                result[track_id] = []
            result[track_id].append(wagon)
        return result
