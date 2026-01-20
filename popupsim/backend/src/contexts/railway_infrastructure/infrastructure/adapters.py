"""Adapters implementing domain ports for specific technologies."""

from typing import Any

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.ports import MetricsPort
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository


class StandardMetricsAdapter(MetricsPort):
    """Adapter implementing standard metrics collection.

    Provides standard dictionary-based metrics collection suitable for
    monitoring, logging, and analysis without external dependencies.
    """

    def collect_track_metrics(self, tracks: dict[str, Track]) -> dict[str, Any]:
        """Collect track-related metrics.

        Parameters
        ----------
        tracks : dict[str, Track]
            Dictionary of track ID to Track entity

        Returns
        -------
        dict[str, Any]
            Track metrics containing:
            - tracks_count: Total number of tracks
            - total_capacity_meters: Sum of all track capacities
            - tracks_by_type: Count of tracks grouped by type
        """
        total_capacity = sum(track.capacity for track in tracks.values())
        track_types = {}

        for track in tracks.values():
            track_type = track.type.value
            if track_type not in track_types:
                track_types[track_type] = 0
            track_types[track_type] += 1

        return {
            'tracks_count': len(tracks),
            'total_capacity_meters': total_capacity,
            'tracks_by_type': track_types,
        }

    def collect_occupancy_metrics(self, repository: TrackOccupancyRepository) -> dict[str, Any]:
        """Collect occupancy-related metrics.

        Parameters
        ----------
        repository : TrackOccupancyRepository
            Repository containing track occupancy data

        Returns
        -------
        dict[str, Any]
            Occupancy metrics containing:
            - total_occupancy_meters: Sum of occupied space across all tracks
            - overall_utilization_percent: Overall utilization percentage
            - occupancy_by_track: Per-track occupancy details
        """
        all_occupancies = repository.get_all_occupancies()

        total_occupancy = 0.0
        total_capacity = 0.0
        occupancy_by_track = {}

        for track_id, occupancy in all_occupancies.items():
            current_occ = occupancy.get_current_occupancy_meters()
            track_capacity = occupancy.track_specification.capacity

            total_occupancy += current_occ
            total_capacity += track_capacity
            occupancy_by_track[str(track_id)] = {
                'occupancy_meters': current_occ,
                'utilization_percent': occupancy.get_utilization_percentage(),
                'wagon_count': occupancy.get_wagon_count(),
            }

        overall_utilization = (total_occupancy / total_capacity * 100) if total_capacity > 0 else 0.0

        return {
            'total_occupancy_meters': total_occupancy,
            'overall_utilization_percent': overall_utilization,
            'occupancy_by_track': occupancy_by_track,
        }
