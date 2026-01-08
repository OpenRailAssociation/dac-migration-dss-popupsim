"""Domain service for Railway Yard operations."""

from typing import Any

from contexts.railway_infrastructure.domain.aggregates.railway_yard import RailwayYard
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.railway_yard_repository import RailwayYardRepository
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant


class RailwayYardService:
    """Domain service for high-level yard operations."""

    def __init__(self, yard_repository: RailwayYardRepository) -> None:
        """Initialize with yard repository."""
        self._yard_repository = yard_repository

    def create_yard(self, yard_id: str, name: str, tracks: list[Track]) -> RailwayYard:
        """Create new railway yard with tracks."""
        yard = RailwayYard(yard_id, name)

        for track in tracks:
            yard.add_track(track)

        self._yard_repository.save(yard)
        return yard

    def find_best_track_for_occupant(
        self, yard_id: str, occupant: TrackOccupant, preferred_track_type: TrackType | None = None
    ) -> str | None:
        """Find best available track for occupant."""
        yard = self._yard_repository.get(yard_id)
        if not yard:
            return None

        # Filter tracks by type if specified
        candidate_tracks = []
        for track_name, track in yard.tracks.items():
            if preferred_track_type and track.type != preferred_track_type:
                continue

            occupancy = yard.get_track_occupancy(track_name)
            if occupancy and occupancy.can_accommodate_length(occupant.effective_length):
                candidate_tracks.append((track_name, occupancy))

        if not candidate_tracks:
            return None

        # Select track with least utilization
        best_track = min(candidate_tracks, key=lambda x: x[1].get_utilization_percentage())

        return best_track[0]

    def get_yard_status(self, yard_id: str) -> dict[str, Any] | None:
        """Get comprehensive yard status."""
        yard = self._yard_repository.get(yard_id)
        if not yard:
            return None

        return yard.get_yard_metrics()

    def can_accommodate_rake(self, yard_id: str, total_length: float) -> bool:
        """Check if yard can accommodate a rake of given length."""
        yard = self._yard_repository.get(yard_id)
        if not yard or yard.is_yard_at_capacity():
            return False

        # Check if any track can accommodate the rake
        for track_name in yard.tracks:
            occupancy = yard.get_track_occupancy(track_name)
            if occupancy and occupancy.can_accommodate_length(total_length):
                return True

        return False

    def get_available_capacity_by_type(self, yard_id: str, track_type: TrackType) -> float:
        """Get total available capacity for specific track type."""
        yard = self._yard_repository.get(yard_id)
        if not yard:
            return 0.0

        total_available = 0.0
        for track in yard.tracks.values():
            if track.type == track_type:
                occupancy = yard.get_track_occupancy(track.name)
                if occupancy:
                    total_available += occupancy.get_available_capacity()

        return total_available

    def optimize_yard_layout(self, yard_id: str) -> dict[str, Any]:
        """Analyze yard layout and suggest optimizations."""
        yard = self._yard_repository.get(yard_id)
        if not yard:
            return {}

        metrics = yard.get_yard_metrics()
        suggestions = []

        # Check for underutilized tracks
        for track_name, track_metrics in metrics['track_metrics'].items():
            if track_metrics['utilization_percentage'] < 20:
                suggestions.append(
                    f'Track {track_name} is underutilized ({track_metrics["utilization_percentage"]:.1f}%)'
                )

        # Check for capacity bottlenecks
        if metrics['utilization_percentage'] > 90:
            suggestions.append('Yard is near capacity - consider expanding or optimizing operations')

        return {
            'current_metrics': metrics,
            'optimization_suggestions': suggestions,
            'efficiency_score': min(
                100, (100 - metrics['utilization_percentage']) + (metrics['active_shunting_operations'] * 10)
            ),
        }
