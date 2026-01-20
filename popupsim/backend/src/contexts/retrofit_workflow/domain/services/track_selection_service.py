"""Track selection service for railway infrastructure resource allocation.

This module provides specialized services for selecting tracks from grouped
collections based on track type and capacity requirements. It leverages the
generic resource selection service for consistent allocation strategies.
"""

from contexts.retrofit_workflow.domain.services.resource_selection_service import ResourceSelectionService
from contexts.retrofit_workflow.domain.services.resource_selection_service import SelectionStrategy
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackCapacityManager


class TrackSelectionService:
    """Service for selecting tracks from grouped collections by track type.

    This service handles scenarios with multiple tracks of the same operational
    type, providing intelligent selection based on capacity, utilization, and
    operational requirements. It supports various track types used in the
    DAC migration process.

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
    >>> service = TrackSelectionService(tracks)
    >>> selected_track = service.select_track_with_capacity('collection')
    """

    def __init__(
        self,
        tracks_by_type: dict[str, list[TrackCapacityManager]],
        strategy: SelectionStrategy = SelectionStrategy.LEAST_BUSY,
    ) -> None:
        """Initialize the track selection service.

        Parameters
        ----------
        tracks_by_type : dict[str, list[TrackCapacityManager]]
            Dictionary mapping track type names to lists of track managers
        strategy : SelectionStrategy, default=SelectionStrategy.LEAST_BUSY
            Selection strategy for load balancing across multiple tracks

        Notes
        -----
        LEAST_BUSY strategy is used by default to ensure optimal load
        distribution across tracks of the same type.
        """
        self.tracks_by_type = tracks_by_type
        self.strategy = strategy
        # Create resource dict for selector
        track_dict: dict[str, TrackCapacityManager] = {}
        for track_list in tracks_by_type.values():
            for track in track_list:
                track_dict[track.track_id] = track
        self.selector: ResourceSelectionService[TrackCapacityManager] = ResourceSelectionService(track_dict, strategy)

    def select_track_with_capacity(self, track_type: str) -> TrackCapacityManager | None:
        """Select a track of the specified type with available capacity.

        Finds and selects the most appropriate track from the specified type
        group that has available capacity for new wagon allocation.

        Parameters
        ----------
        track_type : str
            Track type identifier ('collection', 'retrofit', 'retrofitted', 'parking')

        Returns
        -------
        TrackCapacityManager | None
            Selected track manager with available capacity, or None if all tracks full

        Notes
        -----
        The selection process:
        1. Filters tracks of the specified type
        2. Identifies tracks with available capacity
        3. Applies the configured selection strategy
        4. Returns the optimal track or None if no capacity available

        Examples
        --------
        >>> service = TrackSelectionService(tracks_by_type)
        >>> track = service.select_track_with_capacity('retrofit')
        >>> if track:
        ...     print(f'Selected track: {track.track_id}')
        ... else:
        ...     print('No retrofit tracks available')
        """
        tracks = self.tracks_by_type.get(track_type, [])
        if not tracks:
            return None

        # Find tracks with available capacity
        available_tracks = [t for t in tracks if t.get_available_capacity() > 0]
        if not available_tracks:
            return None

        # Single track - return it
        if len(available_tracks) == 1:
            return available_tracks[0]

        # Multiple tracks - use selection strategy
        track_dict = {t.track_id: t for t in available_tracks}
        selector: ResourceSelectionService[TrackCapacityManager] = ResourceSelectionService(track_dict, self.strategy)
        selected_id = selector.select()
        return track_dict.get(selected_id) if selected_id else None

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
        >>> service = TrackSelectionService(tracks_by_type)
        >>> total_capacity = service.get_total_available_capacity('parking')
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
        >>> service = TrackSelectionService(tracks_by_type)
        >>> collection_tracks = service.get_tracks_of_type('collection')
        >>> for track in collection_tracks:
        ...     print(f'Track {track.track_id}: {track.get_available_capacity()}m')
        """
        return self.tracks_by_type.get(track_type, [])
