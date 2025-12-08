"""Track group aggregate for managing related tracks."""

from dataclasses import dataclass, field

from ..entities.track import Track, TrackType
from ..services.track_selector import TrackSelector
from ..value_objects.track_selection_strategy import TrackSelectionStrategy


@dataclass
class TrackGroup:
    """Aggregate managing a group of tracks of the same type."""

    group_id: str
    track_type: TrackType
    tracks: dict[str, Track] = field(default_factory=dict)
    _selector: TrackSelector = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize track selector with default strategy."""
        self._selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED)

    def set_selection_strategy(self, strategy: TrackSelectionStrategy) -> None:
        """Set track selection strategy."""
        self._selector = TrackSelector(strategy)

    def add_track(self, track: Track) -> None:
        """Add track to group."""
        if track.track_type != self.track_type:
            msg = f"Track type mismatch: expected {self.track_type}, got {track.track_type}"
            raise ValueError(msg)
        self.tracks[track.track_id] = track

    def select_track_for_wagon(self, wagon_length: float) -> Track | None:
        """Select appropriate track for wagon based on strategy."""
        return self._selector.select_track(list(self.tracks.values()), wagon_length)

    def get_track(self, track_id: str) -> Track | None:
        """Get specific track by ID."""
        return self.tracks.get(track_id)

    def get_total_capacity(self) -> float:
        """Get total capacity of all tracks in group."""
        return sum(t.capacity for t in self.tracks.values())

    def get_total_occupancy(self) -> float:
        """Get total occupancy of all tracks in group."""
        return sum(t.current_occupancy for t in self.tracks.values())

    def get_average_utilization(self) -> float:
        """Get average utilization percentage across all tracks."""
        if not self.tracks:
            return 0.0
        return sum(t.utilization_percentage for t in self.tracks.values()) / len(
            self.tracks
        )

    def get_available_tracks(self, min_length: float) -> list[Track]:
        """Get all tracks that can accommodate minimum length."""
        return [t for t in self.tracks.values() if t.can_accommodate(min_length)]
