"""Track selection facade for railway infrastructure resource allocation.

This module provides a domain-specific facade over the generic ResourceSelectionService,
offering track-type grouping, per-type strategies, and convenience methods for track
selection in the DAC migration workflow.
"""

from contexts.retrofit_workflow.domain.services.resource_selection_service import ResourceSelectionService
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackCapacityManager
from shared.domain.value_objects.selection_strategy import SelectionStrategy


class TrackSelectionFacade:
    """Facade for selecting tracks from grouped collections by track type.

    This facade provides a domain-specific API over ResourceSelectionService,
    handling track-type grouping, per-type selection strategies, and convenience
    methods. It simplifies track selection for coordinators while maintaining
    flexibility through the underlying generic resource selector.

    Track Types Supported
    ---------------------
    - Collection tracks: For incoming train arrival and wagon classification
    - Retrofit tracks: For staging wagons before workshop processing
    - Retrofitted tracks: For staging completed wagons before parking
    - Parking tracks: For long-term storage of processed wagons

    Attributes
    ----------
    tracks_by_type : dict[str, list[TrackCapacityManager]]
        Dictionary mapping track types to lists of track managers
    strategy : SelectionStrategy
        Selection strategy for choosing between multiple tracks
    selector : ResourceSelectionService
        Generic resource selector for consistent allocation logic

    Notes
    -----
    Uses LEAST_BUSY strategy by default for optimal load balancing across
    multiple tracks of the same type.

    Examples
    --------
    >>> tracks = {'collection': [track1, track2], 'retrofit': [track3, track4]}
    >>> facade = TrackSelectionFacade(tracks)
    >>> selected_track = facade.select_track_with_capacity('collection')
    """

    def __init__(
        self,
        tracks_by_type: dict[str, list[TrackCapacityManager]],
        strategies_by_type: dict[str, SelectionStrategy] | None = None,
        default_strategy: SelectionStrategy = SelectionStrategy.BEST_FIT,
    ) -> None:
        """Initialize the track selection service.

        Parameters
        ----------
        tracks_by_type : dict[str, list[TrackCapacityManager]]
            Dictionary mapping track type names to lists of track managers
        strategies_by_type : dict[str, SelectionStrategy] | None
            Dictionary mapping track types to their selection strategies
        default_strategy : SelectionStrategy, default=SelectionStrategy.BEST_FIT
            Default strategy for track types not in strategies_by_type

        Notes
        -----
        Each track type can have its own selection strategy for optimal
        resource allocation based on operational requirements.
        """
        self.tracks_by_type = tracks_by_type
        self.strategies_by_type = strategies_by_type or {}
        self.default_strategy = default_strategy
        # Create separate selector for each track type to maintain round-robin state
        self.selectors: dict[str, ResourceSelectionService[TrackCapacityManager]] = {}
        for track_type, track_list in tracks_by_type.items():
            track_dict = {t.track_id: t for t in track_list}
            strategy = self.strategies_by_type.get(track_type, default_strategy)
            self.selectors[track_type] = ResourceSelectionService(track_dict, strategy)

    def select_track_with_capacity(self, track_type: str) -> TrackCapacityManager | None:
        """Select a track of the specified type with available capacity."""
        tracks = self.tracks_by_type.get(track_type, [])
        if not tracks:
            return None

        # Single track - return it if it has capacity
        if len(tracks) == 1:
            return tracks[0] if tracks[0].get_available_capacity() > 0 else None

        # Multiple tracks - use selector with capacity filter
        selector = self.selectors.get(track_type)
        if not selector:
            # Fallback: return first track with capacity
            for track in tracks:
                if track.get_available_capacity() > 0:
                    return track
            return None

        # Use selector with capacity filter
        selected_id = selector.select(lambda _tid, t: t.get_available_capacity() > 0)

        if selected_id:
            # Get track directly from selector's resources dict
            return selector.resources.get(selected_id)

        return None

    def get_total_available_capacity(self, track_type: str) -> float:
        """Calculate total available capacity across all tracks of specified type.

        Aggregates the available capacity from all tracks of the given type
        to provide system-wide capacity visibility.

        Parameters
        ----------
        track_type : str
            Track type identifier to calculate capacity for

        Returns
        -------
        float
            Total available capacity across all tracks in meters

        Notes
        -----
        This method is useful for:
        - System capacity planning
        - Batch size optimization
        - Resource utilization monitoring
        - Bottleneck identification

        Examples
        --------
        >>> facade = TrackSelectionFacade(tracks_by_type)
        >>> total_capacity = facade.get_total_available_capacity('parking')
        >>> print(f'Total parking capacity: {total_capacity}m')
        """
        tracks = self.tracks_by_type.get(track_type, [])
        total: float = sum(track.get_available_capacity() for track in tracks)
        return total

    def get_tracks_of_type(self, track_type: str) -> list[TrackCapacityManager]:
        """Retrieve all track managers of the specified type.

        Provides access to the complete collection of tracks for a given type,
        useful for detailed analysis and direct track management operations.

        Parameters
        ----------
        track_type : str
            Track type identifier to retrieve

        Returns
        -------
        list[TrackCapacityManager]
            List of all track managers for the specified type (may be empty)

        Notes
        -----
        This method returns the raw track list without any filtering or
        selection logic applied. It's primarily used for:
        - System monitoring and reporting
        - Direct track access for specialized operations
        - Configuration validation

        Examples
        --------
        >>> facade = TrackSelectionFacade(tracks_by_type)
        >>> collection_tracks = facade.get_tracks_of_type('collection')
        >>> for track in collection_tracks:
        ...     print(f'Track {track.track_id}: {track.get_available_capacity()}m')
        """
        return self.tracks_by_type.get(track_type, [])
