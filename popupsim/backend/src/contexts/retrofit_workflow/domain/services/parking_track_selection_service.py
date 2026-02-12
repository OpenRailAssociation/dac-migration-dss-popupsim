"""Track selection service for finding optimal tracks for wagon batches."""

from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class ParkingTrackSelectionService:
    """Domain service for selecting optimal parking tracks."""

    def select_best_fit_track(self, wagons: list[Wagon], available_tracks: list[Any]) -> Any | None:
        """Select parking track that best fits batch size (smallest available capacity).

        Args:
            wagons: List of wagons to place
            available_tracks: List of available tracks

        Returns
        -------
            Best fitting track or None if no suitable track found
        """
        batch_length = sum(w.length for w in wagons)

        # Filter tracks with sufficient capacity
        suitable_tracks = [track for track in available_tracks if track.get_available_capacity() >= batch_length]

        if not suitable_tracks:
            return None

        # Select track with smallest available capacity (best fit)
        return min(suitable_tracks, key=lambda t: t.get_available_capacity())
