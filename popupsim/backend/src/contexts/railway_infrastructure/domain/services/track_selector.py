"""Track selection domain service.

This module provides the TrackSelector domain service for selecting tracks
from a group based on configurable strategies and current occupancy state.
"""

from collections.abc import Sequence
import random

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.services.track_occupancy_manager import TrackOccupancyManager
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy


class TrackSelector:
    """Domain service for selecting tracks based on strategy.

    Selects the most appropriate track from a group based on the configured
    strategy and current occupancy state managed by TrackOccupancyManager.

    Parameters
    ----------
    strategy : TrackSelectionStrategy
        Selection strategy (LEAST_OCCUPIED, FIRST_AVAILABLE, ROUND_ROBIN, RANDOM)
    occupancy_manager : TrackOccupancyManager
        Manager tracking current occupancy state of tracks

    Attributes
    ----------
    _strategy : TrackSelectionStrategy
        Configured selection strategy
    _occupancy_manager : TrackOccupancyManager
        Reference to occupancy manager
    _round_robin_index : int
        Current index for round-robin selection

    Examples
    --------
    >>> manager = TrackOccupancyManager()
    >>> selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, manager)
    >>> tracks = [track1, track2, track3]
    >>> selected = selector.select_track(tracks, required_length=20.0)
    """

    def __init__(self, strategy: TrackSelectionStrategy, occupancy_manager: TrackOccupancyManager) -> None:
        """Initialize track selector.

        Parameters
        ----------
        strategy : TrackSelectionStrategy
            Selection strategy to use
        occupancy_manager : TrackOccupancyManager
            Manager for checking track occupancy
        """
        self._strategy = strategy
        self._occupancy_manager = occupancy_manager
        self._round_robin_index = 0

    def select_track(self, tracks: Sequence[Track], required_length: float) -> Track | None:
        """Select track from available tracks based on strategy.

        Filters tracks that can accommodate the required length, then applies
        the configured selection strategy.

        Parameters
        ----------
        tracks : Sequence[Track]
            Candidate tracks to select from
        required_length : float
            Required length in meters

        Returns
        -------
        Track | None
            Selected track, or None if no track can accommodate the length

        Notes
        -----
        Selection strategies:
        - LEAST_OCCUPIED: Track with lowest utilization percentage
        - FIRST_AVAILABLE: First track with sufficient capacity
        - ROUND_ROBIN: Cycles through available tracks sequentially
        - RANDOM: Random selection from available tracks
        """
        available = self.get_available_tracks(tracks, required_length)

        if not available:
            return None

        if self._strategy == TrackSelectionStrategy.LEAST_OCCUPIED:
            return min(available, key=self._occupancy_manager.get_utilization_percentage)

        if self._strategy == TrackSelectionStrategy.FIRST_AVAILABLE:
            return available[0]

        if self._strategy == TrackSelectionStrategy.ROUND_ROBIN:
            track = available[self._round_robin_index % len(available)]
            self._round_robin_index += 1
            return track

        if self._strategy == TrackSelectionStrategy.RANDOM:
            return random.choice(available)  # noqa: S311

        return None

    def get_available_tracks(self, tracks: Sequence[Track], required_length: float) -> list[Track]:
        """Get all tracks that can accommodate the required length.

        Parameters
        ----------
        tracks : Sequence[Track]
            Candidate tracks to check
        required_length : float
            Required length in meters

        Returns
        -------
        list[Track]
            List of tracks with sufficient capacity
        """
        return [t for t in tracks if self._occupancy_manager.can_accommodate(t, required_length)]

    def reset_round_robin(self) -> None:
        """Reset round-robin index to start from beginning.

        Notes
        -----
        Useful when simulation restarts or track group changes.
        """
        self._round_robin_index = 0

    @property
    def strategy(self) -> TrackSelectionStrategy:
        """Get current selection strategy.

        Returns
        -------
        TrackSelectionStrategy
            Configured selection strategy
        """
        return self._strategy
