"""Track capacity management for simulation."""

import random

from configuration.domain.models.scenario import TrackSelectionStrategy
from configuration.domain.models.topology import Topology

from workshop_operations.domain.entities.track import Track, TrackType


class TrackCapacityManager:  # pylint: disable=too-many-instance-attributes
    """Manages track capacity based on length and fill factor."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        tracks: list[Track],
        topology: Topology,
        fill_factor: float = 0.75,
        collection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED,
        retrofit_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED,
    ) -> None:
        """Initialize track capacity manager.

        Parameters
        ----------
        tracks : list[Track]
            List of tracks to manage.
        topology : Topology
            Topology containing track edge lengths.
        fill_factor : float, optional
            Maximum fill ratio for tracks (default 0.75).
        collection_strategy : TrackSelectionStrategy, optional
            Strategy for selecting collection tracks.
        retrofit_strategy : TrackSelectionStrategy, optional
            Strategy for selecting retrofit tracks.
        """
        self.managed_track_types = {
            TrackType.COLLECTION,
            TrackType.RETROFIT,
            TrackType.RETROFITTED,
            TrackType.PARKING,
        }
        self.fill_factor = fill_factor
        self.collection_strategy = collection_strategy
        self.retrofit_strategy = retrofit_strategy
        self.track_capacities: dict[str, float] = {}
        self.current_occupancy: dict[str, float] = {}
        self.collection_tracks: list[str] = []
        self.retrofit_tracks: list[str] = []
        self.round_robin_indices: dict[str, int] = {"collection": 0, "retrofit": 0}

        self._calculate_capacities(tracks, topology)

    def _calculate_capacities(self, tracks: list[Track], topology: Topology) -> None:
        """Calculate capacity for managed tracks.

        Parameters
        ----------
        tracks : list[Track]
            List of tracks to calculate capacities for.
        topology : Topology
            Topology containing edge length information.
        """
        for track in tracks:
            if track.type in self.managed_track_types:
                # Use cached length if available, otherwise calculate and cache
                total_length = track.get_total_length()
                if total_length is None:
                    total_length = sum(
                        topology.get_edge_length(edge_id) for edge_id in track.edges
                    )
                    track.set_total_length(total_length)

                self.track_capacities[track.id] = total_length * self.fill_factor
                self.current_occupancy[track.id] = 0.0
                if track.type == TrackType.COLLECTION:
                    self.collection_tracks.append(track.id)
                elif track.type == TrackType.RETROFIT:
                    self.retrofit_tracks.append(track.id)

    def can_add_wagon(self, track_id: str, wagon_length: float) -> bool:
        """Check if wagon can be added to track.

        Parameters
        ----------
        track_id : str
            ID of the track to check.
        wagon_length : float
            Length of the wagon to add.

        Returns
        -------
        bool
            True if wagon fits, False otherwise.
        """
        if track_id not in self.track_capacities:
            return False
        return (
            self.current_occupancy[track_id] + wagon_length
            <= self.track_capacities[track_id]
        )

    def add_wagon(self, track_id: str, wagon_length: float) -> bool:
        """Add wagon to track if space available.

        Parameters
        ----------
        track_id : str
            ID of the track to add wagon to.
        wagon_length : float
            Length of the wagon to add.

        Returns
        -------
        bool
            True if wagon was added, False if no space.
        """
        if self.can_add_wagon(track_id, wagon_length):
            self.current_occupancy[track_id] += wagon_length
            return True
        return False

    def remove_wagon(self, track_id: str, wagon_length: float) -> None:
        """Remove wagon from track.

        Parameters
        ----------
        track_id : str
            ID of the track to remove wagon from.
        wagon_length : float
            Length of the wagon to remove.
        """
        if track_id in self.current_occupancy:
            self.current_occupancy[track_id] = max(
                0.0, self.current_occupancy[track_id] - wagon_length
            )

    def select_collection_track(self, wagon_length: float) -> str | None:
        """Select collection track based on configured strategy.

        Parameters
        ----------
        wagon_length : float
            Length of wagon needing a collection track.

        Returns
        -------
        str | None
            Selected track ID or None if no capacity available.
        """
        return self._select_track(
            self.collection_tracks, wagon_length, self.collection_strategy, "collection"
        )

    def select_retrofit_track(self, wagon_length: float) -> str | None:
        """Select retrofit track based on configured strategy.

        Parameters
        ----------
        wagon_length : float
            Length of wagon needing a retrofit track.

        Returns
        -------
        str | None
            Selected track ID or None if no capacity available.
        """
        return self._select_track(
            self.retrofit_tracks, wagon_length, self.retrofit_strategy, "retrofit"
        )

    def _select_track(  # pylint: disable=too-many-return-statements  # noqa: PLR0911
        self,
        track_list: list[str],
        wagon_length: float,
        strategy: TrackSelectionStrategy,
        track_type: str,
    ) -> str | None:
        """Select track based on strategy.

        Parameters
        ----------
        track_list : list[str]
            List of track IDs to choose from.
        wagon_length : float
            Length of wagon needing track space.
        strategy : TrackSelectionStrategy
            Selection strategy to use.
        track_type : str
            Type of track ('collection' or 'retrofit') for round-robin indexing.

        Returns
        -------
        str | None
            Selected track ID or None if no tracks available.
        """
        if strategy == TrackSelectionStrategy.LEAST_OCCUPIED:
            available_with_ratio = [
                (t, self.current_occupancy[t] / self.track_capacities[t])
                for t in track_list
                if self.can_add_wagon(t, wagon_length)
            ]
            if not available_with_ratio:
                return None
            return min(available_with_ratio, key=lambda x: x[1])[0]

        available_tracks = [
            track_id
            for track_id in track_list
            if self.can_add_wagon(track_id, wagon_length)
        ]

        if not available_tracks:
            return None

        if strategy == TrackSelectionStrategy.ROUND_ROBIN:
            index = self.round_robin_indices[track_type] % len(available_tracks)
            self.round_robin_indices[track_type] += 1
            return available_tracks[index]

        if strategy == TrackSelectionStrategy.FIRST_AVAILABLE:
            return available_tracks[0]

        if strategy == TrackSelectionStrategy.RANDOM:
            return random.choice(available_tracks)  # noqa: S311

        return None

    def get_available_capacity(self, track_id: str) -> float:
        """Get available capacity on track.

        Parameters
        ----------
        track_id : str
            ID of the track to check.

        Returns
        -------
        float
            Available capacity in length units, 0.0 if track not found.
        """
        if track_id not in self.track_capacities:
            return 0.0
        return self.track_capacities[track_id] - self.current_occupancy[track_id]

    def get_total_capacity(self, track_id: str) -> float:
        """Get total capacity of track.

        Parameters
        ----------
        track_id : str
            ID of the track to check.

        Returns
        -------
        float
            Total capacity in length units, 0.0 if track not found.
        """
        return self.track_capacities.get(track_id, 0.0)
