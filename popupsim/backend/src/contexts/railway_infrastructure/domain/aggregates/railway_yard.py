"""RailwayYard aggregate root for managing tracks and their occupancy."""

from typing import Any

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.exceptions import InsufficientCapacityError
from contexts.railway_infrastructure.domain.exceptions import TrackNotFoundError
from contexts.railway_infrastructure.domain.value_objects.track_group import TrackGroup
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy


class RailwayYard:
    """Aggregate root managing all tracks and their occupancy in a railway yard."""

    def __init__(self, yard_id: str) -> None:
        """Initialize railway yard."""
        self._yard_id = yard_id
        self._tracks: dict[str, Track] = {}
        self._occupancy: dict[str, float] = {}  # track_id -> occupied_length_meters
        self._track_groups: dict[TrackType, TrackGroup] = {}
        self._selection_strategies: dict[TrackType, TrackSelectionStrategy] = {}

    @property
    def yard_id(self) -> str:
        """Get yard ID."""
        return self._yard_id

    def add_track(self, track: Track) -> None:
        """Add track to yard."""
        self._tracks[track.name] = track
        self._occupancy[track.name] = 0.0

    def create_track_group(
        self,
        track_type: TrackType,
        track_ids: list[str],
        strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED,
    ) -> None:
        """Create logical grouping of tracks by type."""
        # Validate all track IDs exist
        for track_id in track_ids:
            if track_id not in self._tracks:
                raise TrackNotFoundError(f'Track {track_id} not found in yard')

        self._track_groups[track_type] = TrackGroup(track_type, track_ids, strategy)
        self._selection_strategies[track_type] = strategy

    def set_selection_strategy(self, track_type: TrackType, strategy: TrackSelectionStrategy) -> None:
        """Set selection strategy for track type."""
        if track_type in self._track_groups:
            group = self._track_groups[track_type]
            self._track_groups[track_type] = TrackGroup(group.track_type, group.track_ids, strategy)
            self._selection_strategies[track_type] = strategy

    def can_track_accommodate(self, track_id: str, wagon_length: float) -> bool:
        """Check if specific track can accommodate wagon."""
        track = self._tracks.get(track_id)
        if not track:
            return False

        current_occupancy = self._occupancy.get(track_id, 0.0)
        available_capacity = track.capacity - current_occupancy

        # For workshop tracks, also check wagon count limit
        if track.type == TrackType.WORKSHOP and track.max_wagons is not None:
            current_wagon_count = self._get_wagon_count_on_track(track_id)
            if current_wagon_count >= track.max_wagons:
                return False

        return available_capacity >= wagon_length

    def add_wagon_to_track(self, track_id: str, wagon_length: float) -> None:
        """Add wagon to specific track."""
        if not self.can_track_accommodate(track_id, wagon_length):
            raise InsufficientCapacityError(f'Track {track_id} cannot accommodate wagon of length {wagon_length}m')

        self._occupancy[track_id] = self._occupancy.get(track_id, 0.0) + wagon_length

    def remove_wagon_from_track(self, track_id: str, wagon_length: float) -> None:
        """Remove wagon from specific track."""
        if track_id not in self._tracks:
            raise TrackNotFoundError(f'Track {track_id} not found')

        current_occupancy = self._occupancy.get(track_id, 0.0)
        new_occupancy = max(0.0, current_occupancy - wagon_length)
        self._occupancy[track_id] = new_occupancy

    def select_track_for_type(self, track_type: TrackType, wagon_length: float) -> str | None:
        """Select track from type group that can accommodate wagon."""
        group = self._track_groups.get(track_type)
        if not group:
            return None

        # Get available tracks that can accommodate the wagon
        available_tracks = [
            track_id for track_id in group.track_ids if self.can_track_accommodate(track_id, wagon_length)
        ]

        if not available_tracks:
            return None

        # Apply selection strategy
        return self._apply_selection_strategy(available_tracks, group.selection_strategy)

    def add_wagon_to_group(self, track_type: TrackType, wagon_length: float) -> tuple[str | None, bool]:
        """Add wagon to group using selection strategy."""
        selected_track_id = self.select_track_for_type(track_type, wagon_length)
        if not selected_track_id:
            return (None, False)

        try:
            self.add_wagon_to_track(selected_track_id, wagon_length)
            return (selected_track_id, True)
        except (TrackNotFoundError, InsufficientCapacityError):
            return (None, False)

    def remove_wagon_from_group(self, track_type: TrackType, wagon_length: float) -> bool:
        """Remove wagon from group (removes from most occupied track)."""
        group = self._track_groups.get(track_type)
        if not group:
            return False

        # Find tracks with wagons
        tracks_with_wagons = [track_id for track_id in group.track_ids if self._occupancy.get(track_id, 0.0) > 0]

        if not tracks_with_wagons:
            return False

        # Remove from most occupied track
        most_occupied = max(tracks_with_wagons, key=lambda t: self._occupancy.get(t, 0.0))
        self.remove_wagon_from_track(most_occupied, wagon_length)
        return True

    def get_track_capacity(self, track_id: str) -> float:
        """Get total capacity of track in meters."""
        track = self._tracks.get(track_id)
        return track.capacity if track else 0.0

    def get_available_capacity(self, track_id: str) -> float:
        """Get available capacity on track in meters."""
        track = self._tracks.get(track_id)
        if not track:
            return 0.0

        current_occupancy = self._occupancy.get(track_id, 0.0)
        return max(0.0, track.capacity - current_occupancy)

    def get_track_occupancy(self, track_id: str) -> float:
        """Get current occupancy of track in meters."""
        return self._occupancy.get(track_id, 0.0)

    def get_track_utilization(self, track_id: str) -> float:
        """Get utilization percentage of track."""
        track = self._tracks.get(track_id)
        if not track or track.capacity == 0:
            return 0.0

        occupancy = self._occupancy.get(track_id, 0.0)
        return (occupancy / track.capacity) * 100.0

    def get_tracks_by_type(self, track_type: TrackType) -> list[Track]:
        """Get all tracks of specific type."""
        return [track for track in self._tracks.values() if track.type == track_type]

    def get_group_metrics(self, track_type: TrackType) -> dict[str, Any]:
        """Get metrics for track group."""
        group = self._track_groups.get(track_type)
        if not group:
            return {}

        total_capacity = sum(self.get_track_capacity(track_id) for track_id in group.track_ids)
        total_occupancy = sum(self.get_track_occupancy(track_id) for track_id in group.track_ids)

        utilization = (total_occupancy / total_capacity * 100.0) if total_capacity > 0 else 0.0

        return {
            'track_count': len(group.track_ids),
            'total_capacity': total_capacity,
            'total_occupancy': total_occupancy,
            'utilization_percent': utilization,
            'selection_strategy': group.selection_strategy.value,
        }

    def get_yard_metrics(self) -> dict[str, Any]:
        """Get overall yard metrics."""
        total_tracks = len(self._tracks)
        total_capacity = sum(track.capacity for track in self._tracks.values())
        total_occupancy = sum(self._occupancy.values())

        utilization = (total_occupancy / total_capacity * 100.0) if total_capacity > 0 else 0.0

        group_metrics = {
            f'{track_type.value}_group': self.get_group_metrics(track_type) for track_type in self._track_groups
        }

        return {
            'yard_id': self._yard_id,
            'total_tracks': total_tracks,
            'total_capacity': total_capacity,
            'total_occupancy': total_occupancy,
            'utilization_percent': utilization,
            'track_groups': group_metrics,
        }

    def _apply_selection_strategy(self, available_tracks: list[str], strategy: TrackSelectionStrategy) -> str:
        """Apply selection strategy to choose track."""
        if not available_tracks:
            raise ValueError('No available tracks')

        match strategy:
            case TrackSelectionStrategy.LEAST_OCCUPIED:
                return min(available_tracks, key=lambda t: self._occupancy.get(t, 0.0))
            case TrackSelectionStrategy.FIRST_AVAILABLE:
                return available_tracks[0]
            case TrackSelectionStrategy.ROUND_ROBIN:
                # Simple round-robin based on track name hash
                return sorted(available_tracks)[hash(self._yard_id) % len(available_tracks)]
            case TrackSelectionStrategy.RANDOM:
                import random

                return random.choice(available_tracks)  # noqa: S311
            case _:
                return available_tracks[0]

    def _get_wagon_count_on_track(self, track_id: str) -> int:
        """Estimate wagon count on track (assuming 20m average wagon length)."""
        occupancy = self._occupancy.get(track_id, 0.0)
        return int(occupancy / 20.0)  # Rough estimate for workshop capacity checks
