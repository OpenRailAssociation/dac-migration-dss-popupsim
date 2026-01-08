"""Repository for managing track occupancy aggregates."""

from uuid import UUID

from contexts.railway_infrastructure.domain.aggregates.track_occupancy import TrackOccupancy
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.value_objects.occupancy_snapshot import OccupancySnapshot


class TrackOccupancyRepository:
    """Repository managing all track occupancy aggregates."""

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._occupancies: dict[UUID | str, TrackOccupancy] = {}

    def get_or_create(self, track: Track) -> TrackOccupancy:
        """Get existing occupancy or create new one for track."""
        if track.id not in self._occupancies:
            self._occupancies[track.id] = TrackOccupancy(track_id=track.id, track_specification=track)
        return self._occupancies[track.id]

    def get(self, track_id: UUID | str) -> TrackOccupancy | None:
        """Get occupancy by track ID."""
        return self._occupancies.get(track_id)

    def get_occupancy_history(self, track_id: UUID | str, from_time: float, to_time: float) -> list[OccupancySnapshot]:
        """Get occupancy history for time range."""
        occupancy = self._occupancies.get(track_id)
        if not occupancy:
            return []

        return [snapshot for snapshot in occupancy._occupancy_history if from_time <= snapshot.timestamp <= to_time]

    def reset(self, track_id: UUID | str | None = None) -> None:
        """Reset occupancy for specific track or all tracks."""
        if track_id is None:
            self._occupancies.clear()
        else:
            self._occupancies.pop(track_id, None)

    def get_all_occupancies(self) -> dict[UUID | str, TrackOccupancy]:
        """Get all track occupancies (for analytics)."""
        return self._occupancies.copy()
