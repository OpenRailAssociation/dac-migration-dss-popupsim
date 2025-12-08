"""Example usage of track capacity management."""

from contexts.railway_infrastructure.domain.aggregates.track_group import (
    TrackGroup,
)
from contexts.railway_infrastructure.domain.entities.track import (
    Track,
    TrackType,
)
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import (
    TrackSelectionStrategy,
)


def example_basic_track_usage() -> None:
    """Demonstrate basic track capacity management."""

    track = Track(
        track_id="track_1",
        track_type=TrackType.COLLECTION,
        total_length=100.0,
        fill_factor=0.75,
    )

    track.add_wagon(15.0)

    track.add_wagon(20.0)


def example_track_group_usage() -> None:
    """Demonstrate track group with selection strategies."""

    group = TrackGroup(group_id="collection_group", track_type=TrackType.COLLECTION)

    for i in range(1, 4):
        track = Track(
            track_id=f"collection_{i}",
            track_type=TrackType.COLLECTION,
            total_length=100.0,
            fill_factor=0.75,
        )
        group.add_track(track)

    group.set_selection_strategy(TrackSelectionStrategy.LEAST_OCCUPIED)

    for wagon_length in [15.0, 20.0, 25.0, 30.0]:
        selected = group.select_track_for_wagon(wagon_length)
        if selected:
            selected.add_wagon(wagon_length)


if __name__ == "__main__":
    example_basic_track_usage()
    example_track_group_usage()
