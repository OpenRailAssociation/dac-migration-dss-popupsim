"""Track group aggregate for managing related tracks."""

from dataclasses import dataclass
from dataclasses import field
from uuid import UUID

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.services.track_occupancy_manager import TrackOccupancyManager
from contexts.railway_infrastructure.domain.services.track_selector import TrackSelector
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy


@dataclass
class TrackGroup:
    """Aggregate managing a group of tracks of the same type."""

    group_id: str
    track_type: TrackType
    tracks: dict[UUID, Track] = field(default_factory=lambda: {})
    _occupancy_manager: TrackOccupancyManager = field(default_factory=TrackOccupancyManager, init=False, repr=False)
    _selector: TrackSelector = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize track selector with default strategy."""
        self._selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, self._occupancy_manager)

    def set_selection_strategy(self, strategy: TrackSelectionStrategy) -> None:
        """Set track selection strategy.

        Parameters
        ----------
        strategy : TrackSelectionStrategy
            New selection strategy to use
        """
        self._selector = TrackSelector(strategy, self._occupancy_manager)

    def add_track(self, track: Track) -> None:
        """Add track to group.

        Parameters
        ----------
        track : Track
            Track to add to group

        Raises
        ------
        ValueError
            If track type doesn't match group type
        """
        if track.type != self.track_type:
            msg = f'Track type mismatch: expected {self.track_type}, got {track.type}'
            raise ValueError(msg)
        self.tracks[track.id] = track

    def select_track_for_wagon(self, wagon_length: float) -> Track | None:
        """Select appropriate track for wagon based on strategy.

        Parameters
        ----------
        wagon_length : float
            Length of wagon in meters

        Returns
        -------
        Track | None
            Selected track, or None if no track can accommodate wagon
        """
        return self._selector.select_track(list(self.tracks.values()), wagon_length)

    def get_track(self, track_id: UUID) -> Track | None:
        """Get specific track by ID.

        Parameters
        ----------
        track_id : UUID
            Track identifier

        Returns
        -------
        Track | None
            Track if found, None otherwise
        """
        return self.tracks.get(track_id)

    def get_total_capacity(self) -> float:
        """Get total capacity of all tracks in group.

        Returns
        -------
        float
            Sum of all track capacities in meters
        """
        return sum(track.capacity for track in self.tracks.values())

    def get_total_occupancy(self) -> float:
        """Get total occupancy of all tracks in group.

        Returns
        -------
        float
            Sum of current occupancy across all tracks in meters
        """
        return sum(self._occupancy_manager.get_current_occupancy(track) for track in self.tracks.values())

    def get_average_utilization(self) -> float:
        """Get average utilization percentage across all tracks.

        Returns
        -------
        float
            Average utilization percentage (0.0 to 100.0), or 0.0 if no tracks
        """
        if not self.tracks:
            return 0.0
        return sum(self._occupancy_manager.get_utilization_percentage(track) for track in self.tracks.values()) / len(
            self.tracks
        )

    def get_available_tracks(self, min_length: float) -> list[Track]:
        """Get all tracks that can accommodate minimum length.

        Parameters
        ----------
        min_length : float
            Minimum required length in meters

        Returns
        -------
        list[Track]
            List of tracks with sufficient available capacity
        """
        return [track for track in self.tracks.values() if self._occupancy_manager.can_accommodate(track, min_length)]

    def try_add_wagon_to_group(self, wagon_length: float) -> tuple[Track | None, bool]:
        """Try to add wagon to group using selection strategy.

        Parameters
        ----------
        wagon_length : float
            Length of wagon in meters

        Returns
        -------
        tuple[Track | None, bool]
            (selected_track, success) - track is None if no capacity available
        """
        track = self._selector.select_track(list(self.tracks.values()), wagon_length)
        if track is None:
            return (None, False)

        try:
            self._occupancy_manager.add_wagon(track, wagon_length)
            return (track, True)
        except ValueError:
            return (track, False)

    def remove_wagon_from_group(self, track_id: UUID, wagon_length: float) -> bool:
        """Remove wagon from specific track in group.

        Parameters
        ----------
        track_id : UUID
            ID of track to remove wagon from
        wagon_length : float
            Length of wagon in meters

        Returns
        -------
        bool
            True if wagon removed successfully, False if track not found
        """
        track = self.tracks.get(track_id)
        if track is None:
            return False

        self._occupancy_manager.remove_wagon(track, wagon_length)
        return True

    def get_total_available_capacity(self) -> float:
        """Get sum of available capacity across all tracks.

        Returns
        -------
        float
            Total available capacity in meters
        """
        return sum(self._occupancy_manager.get_available_capacity(track) for track in self.tracks.values())

    def is_group_full(self, min_wagon_length: float = 15.0) -> bool:
        """Check if no track in group can accommodate minimum wagon length.

        Parameters
        ----------
        min_wagon_length : float, optional
            Minimum wagon length to check, by default 15.0 meters

        Returns
        -------
        bool
            True if all tracks are full (cannot accommodate min_wagon_length)
        """
        return all(
            not self._occupancy_manager.can_accommodate(track, min_wagon_length) for track in self.tracks.values()
        )
