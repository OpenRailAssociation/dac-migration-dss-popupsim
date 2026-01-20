"""Track selection service for railway infrastructure context."""

from enum import Enum
from typing import TYPE_CHECKING

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType

if TYPE_CHECKING:
    from contexts.railway_infrastructure.application.railway_context import RailwayInfrastructureContext


class SelectionStrategy(Enum):
    """Track selection strategies."""

    ROUND_ROBIN = 'round_robin'
    LEAST_OCCUPIED = 'least_occupied'
    MOST_AVAILABLE = 'most_available'


class TrackSelectionService:
    """Service for selecting tracks with various strategies."""

    def __init__(self, railway_context: 'RailwayInfrastructureContext') -> None:
        """Initialize with railway context."""
        self._railway_context = railway_context
        self._round_robin_indices: dict[str, int] = {}

    def select_track(
        self, track_type: str, strategy: SelectionStrategy = SelectionStrategy.ROUND_ROBIN
    ) -> Track | None:
        """Select a track of given type using specified strategy."""
        tracks = self.get_tracks_by_type(track_type)
        if not tracks:
            return None

        if strategy == SelectionStrategy.ROUND_ROBIN:
            return self._select_round_robin(tracks, track_type)
        elif strategy == SelectionStrategy.LEAST_OCCUPIED:
            return self._select_least_occupied(tracks)
        elif strategy == SelectionStrategy.MOST_AVAILABLE:
            return self._select_most_available(tracks)

        return tracks[0]  # Fallback

    def get_tracks_by_type(self, track_type: str) -> list[Track]:
        """Get all tracks of specified type."""
        track_type_enum = self._map_track_type(track_type)
        tracks = []

        for track in self._railway_context._tracks.values():
            if track.type == track_type_enum:
                tracks.append(track)

        return tracks

    def get_track_ids_by_type(self, track_type: str) -> list[str]:
        """Get track IDs of specified type."""
        tracks = self.get_tracks_by_type(track_type)
        return [str(track.id) for track in tracks]

    def _select_round_robin(self, tracks: list[Track], track_type: str) -> Track:
        """Select track using round-robin strategy."""
        if track_type not in self._round_robin_indices:
            self._round_robin_indices[track_type] = 0

        index = self._round_robin_indices[track_type]
        selected_track = tracks[index % len(tracks)]
        self._round_robin_indices[track_type] = (index + 1) % len(tracks)

        return selected_track

    def _select_least_occupied(self, tracks: list[Track]) -> Track:
        """Select track with least occupancy."""
        min_occupancy = float('inf')
        selected_track = tracks[0]

        for track in tracks:
            occupancy_repo = self._railway_context.get_occupancy_repository()
            track_occupancy = occupancy_repo.get(track.id)

            current_occupancy = track_occupancy.get_current_occupancy_meters() if track_occupancy else 0.0

            if current_occupancy < min_occupancy:
                min_occupancy = current_occupancy
                selected_track = track

        return selected_track

    def _select_most_available(self, tracks: list[Track]) -> Track:
        """Select track with most available capacity."""
        max_available = -1.0
        selected_track = tracks[0]

        for track in tracks:
            available = self._railway_context.get_available_capacity(str(track.id))
            if available > max_available:
                max_available = available
                selected_track = track

        return selected_track

    def _map_track_type(self, track_type: str) -> TrackType:
        """Map string to TrackType enum."""
        type_mapping = {
            'locoparking': TrackType.LOCOPARKING,
            'parking': TrackType.PARKING,
            'collection': TrackType.COLLECTION,
            'retrofit': TrackType.RETROFIT,
            'workshop': TrackType.WORKSHOP,
            'retrofitted': TrackType.RETROFITTED,
        }
        return type_mapping.get(track_type.lower(), TrackType.COLLECTION)
