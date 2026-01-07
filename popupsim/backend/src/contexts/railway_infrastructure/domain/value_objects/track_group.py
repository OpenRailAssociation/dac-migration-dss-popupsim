"""TrackGroup value object for logical track grouping."""

from dataclasses import dataclass

from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy


@dataclass(frozen=True)
class TrackGroup:
    """Value object representing a logical grouping of tracks."""

    track_type: TrackType
    track_ids: list[str]
    selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED