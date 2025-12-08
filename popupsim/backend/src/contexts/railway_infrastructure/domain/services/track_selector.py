"""Domain service for track selection."""

from collections.abc import Sequence
import random

from ..entities.track import Track
from ..value_objects.track_selection_strategy import TrackSelectionStrategy


class TrackSelector:
    """Domain service for selecting tracks based on strategy."""

    def __init__(self, strategy: TrackSelectionStrategy) -> None:
        self._strategy = strategy
        self._round_robin_index = 0

    def select_track(self, tracks: Sequence[Track], required_length: float) -> Track | None:
        """Select track from available tracks based on strategy."""
        available = [t for t in tracks if t.can_accommodate(required_length)]

        if not available:
            return None

        if self._strategy == TrackSelectionStrategy.LEAST_OCCUPIED:
            return min(available, key=lambda t: t.utilization_percentage)

        if self._strategy == TrackSelectionStrategy.FIRST_AVAILABLE:
            return available[0]

        if self._strategy == TrackSelectionStrategy.ROUND_ROBIN:
            track = available[self._round_robin_index % len(available)]
            self._round_robin_index += 1
            return track

        if self._strategy == TrackSelectionStrategy.RANDOM:
            return random.choice(available)  # noqa: S311

        return None
