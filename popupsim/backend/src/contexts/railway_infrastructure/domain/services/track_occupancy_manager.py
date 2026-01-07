"""Track occupancy management service.

This module provides the TrackOccupancyManager domain service for managing
runtime occupancy state of tracks.
"""

from uuid import UUID

from contexts.railway_infrastructure.domain.entities.track import Track


class TrackOccupancyManager:
    """Domain service for managing runtime occupancy state of tracks.

    Separates mutable state (what's on tracks) from immutable specification
    (track properties).

    Attributes
    ----------
    _occupancy : dict[UUID, float]
        Current occupancy in meters for each track (id -> meters)
    _wagon_count : dict[UUID, int]
        Current wagon count for each track (id -> count)

    Examples
    --------
    >>> from uuid import uuid4
    >>> track = Track(uuid4(), TrackType.COLLECTION, total_length=150.0)
    >>> manager = TrackOccupancyManager()
    >>> manager.can_accommodate(track, 20.0)
    True
    >>> manager.add_wagon(track, 20.0)
    >>> manager.get_current_occupancy(track)
    20.0
    """

    def __init__(self) -> None:
        """Initialize occupancy manager with empty state."""
        self._occupancy: dict[UUID, float] = {}
        self._wagon_count: dict[UUID, int] = {}

    def can_accommodate(self, track: Track, wagon_length: float) -> bool:
        """Check if track can accommodate wagon given current occupancy.

        Parameters
        ----------
        track : Track
            Track specification to check
        wagon_length : float
            Length of wagon in meters

        Returns
        -------
        bool
            True if wagon fits (both length and count constraints), False otherwise

        Notes
        -----
        For workshop tracks (max_wagons is not None), checks both length capacity
        and wagon count limit. For other tracks, only checks length capacity.
        """
        current_occupancy = self._occupancy.get(track.id, 0.0)
        length_ok = current_occupancy + wagon_length <= track.capacity

        if track.max_wagons is not None:
            current_count = self._wagon_count.get(track.id, 0)
            count_ok = current_count < track.max_wagons
            return length_ok and count_ok

        return length_ok

    def add_wagon(self, track: Track, wagon_length: float) -> None:
        """Add wagon to track (updates occupancy state).

        Parameters
        ----------
        track : Track
            Track specification
        wagon_length : float
            Length of wagon in meters

        Raises
        ------
        ValueError
            If track cannot accommodate wagon (capacity or count limit exceeded)

        Notes
        -----
        Updates both occupancy (meters) and wagon count. For workshop tracks,
        enforces both length and count limits.
        """
        if not self.can_accommodate(track, wagon_length):
            current_count = self._wagon_count.get(track.id, 0)
            if track.max_wagons is not None and current_count >= track.max_wagons:
                msg = (
                    f'Track {track.id} cannot accommodate wagon: wagon count limit reached. '
                    f'Current: {current_count}/{track.max_wagons} wagons'
                )
            else:
                available = track.capacity - self._occupancy.get(track.id, 0.0)
                msg = (
                    f'Track {track.id} cannot accommodate wagon of length {wagon_length}m. '
                    f'Available: {available:.1f}m, Required: {wagon_length:.1f}m'
                )
            raise ValueError(msg)

        self._occupancy[track.id] = self._occupancy.get(track.id, 0.0) + wagon_length
        self._wagon_count[track.id] = self._wagon_count.get(track.id, 0) + 1

    def remove_wagon(self, track: Track, wagon_length: float) -> None:
        """Remove wagon from track (updates occupancy state).

        Parameters
        ----------
        track : Track
            Track specification
        wagon_length : float
            Length of wagon in meters

        Raises
        ------
        ValueError
            If wagon_length is negative

        Notes
        -----
        Updates both occupancy (meters) and wagon count. Prevents negative values.
        """
        if wagon_length < 0:
            msg = f'Cannot remove negative wagon length: {wagon_length}m'
            raise ValueError(msg)

        current = self._occupancy.get(track.id, 0.0)
        self._occupancy[track.id] = max(0.0, current - wagon_length)

        current_count = self._wagon_count.get(track.id, 0)
        self._wagon_count[track.id] = max(0, current_count - 1)

    def get_current_occupancy(self, track: Track) -> float:
        """Get current occupancy for track.

        Parameters
        ----------
        track : Track
            Track specification

        Returns
        -------
        float
            Current occupancy in meters (0.0 if track not found)
        """
        return self._occupancy.get(track.id, 0.0)

    def get_available_capacity(self, track: Track) -> float:
        """Get available capacity for track.

        Parameters
        ----------
        track : Track
            Track specification

        Returns
        -------
        float
            Available capacity in meters (capacity - current_occupancy)
        """
        return track.capacity - self._occupancy.get(track.id, 0.0)

    def get_wagon_count(self, track: Track) -> int:
        """Get current wagon count on track.

        Parameters
        ----------
        track : Track
            Track specification

        Returns
        -------
        int
            Current wagon count (0 if track not found)
        """
        return self._wagon_count.get(track.id, 0)

    def get_utilization_percentage(self, track: Track) -> float:
        """Get utilization percentage for track.

        Parameters
        ----------
        track : Track
            Track specification

        Returns
        -------
        float
            Utilization percentage (0.0 to 100.0)
        """
        current = self._occupancy.get(track.id, 0.0)
        return (current / track.capacity * 100) if track.capacity > 0 else 0.0

    def is_empty(self, track: Track) -> bool:
        """Check if track is empty.

        Parameters
        ----------
        track : Track
            Track specification

        Returns
        -------
        bool
            True if track has no occupancy, False otherwise
        """
        return self._occupancy.get(track.id, 0.0) == 0.0

    def is_full(self, track: Track) -> bool:
        """Check if track is at capacity.

        Parameters
        ----------
        track : Track
            Track specification

        Returns
        -------
        bool
            True if track is at length capacity or wagon count limit, False otherwise

        Notes
        -----
        For workshop tracks, returns True if either length capacity OR wagon count
        limit is reached. For other tracks, only checks length capacity.
        """
        current = self._occupancy.get(track.id, 0.0)
        length_full = current >= track.capacity

        if track.max_wagons is not None:
            current_count = self._wagon_count.get(track.id, 0)
            count_full = current_count >= track.max_wagons
            return length_full or count_full

        return length_full

    def reset(self, track: Track | None = None) -> None:
        """Reset occupancy state for specific track or all tracks.

        Parameters
        ----------
        track : Track | None, optional
            Track to reset, or None to reset all tracks

        Notes
        -----
        If track is None, clears all occupancy and wagon count data.
        If track is provided, only resets that specific track.
        """
        if track is None:
            self._occupancy.clear()
            self._wagon_count.clear()
        else:
            self._occupancy.pop(track.id, None)
            self._wagon_count.pop(track.id, None)
