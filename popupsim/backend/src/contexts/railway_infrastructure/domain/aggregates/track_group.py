"""Simplified track group aggregate."""

from dataclasses import dataclass
from dataclasses import field
from uuid import UUID

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from shared.domain.value_objects.selection_strategy import SelectionStrategy


@dataclass
class TrackGroup:
    """Simple aggregate managing a collection of tracks."""

    group_id: str
    track_type: TrackType
    tracks: dict[UUID | str, Track] = field(default_factory=dict)
    selection_strategy: SelectionStrategy = SelectionStrategy.LEAST_OCCUPIED

    def add_track(self, track: Track) -> None:
        """Add track to group."""
        if track.type != self.track_type:
            raise ValueError(f'Track type mismatch: expected {self.track_type}, got {track.type}')
        self.tracks[track.id] = track

    def get_track(self, track_id: UUID | str) -> Track | None:
        """Get track by ID."""
        return self.tracks.get(track_id)

    def get_all_tracks(self) -> list[Track]:
        """Get all tracks in group."""
        return list(self.tracks.values())

    def get_total_capacity(self) -> float:
        """Get total capacity of all tracks."""
        return sum(track.capacity for track in self.tracks.values())

    def set_selection_strategy(self, strategy: SelectionStrategy) -> None:
        """Set track selection strategy."""
        self.selection_strategy = strategy

    def is_empty(self) -> bool:
        """Check if group has no tracks."""
        return len(self.tracks) == 0
