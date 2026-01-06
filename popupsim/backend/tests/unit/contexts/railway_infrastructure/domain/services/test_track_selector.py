"""Tests for TrackSelector domain service."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.services.track_occupancy_manager import TrackOccupancyManager
from contexts.railway_infrastructure.domain.services.track_selector import TrackSelector
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy
import pytest


@pytest.fixture
def manager() -> TrackOccupancyManager:
    """Create occupancy manager."""
    return TrackOccupancyManager()


@pytest.fixture
def tracks() -> list[Track]:
    """Create test tracks with sufficient capacity."""
    return [
        Track(uuid4(), 'C1', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0),
        Track(uuid4(), 'C2', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0),
        Track(uuid4(), 'C3', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0),
    ]


def test_first_available_strategy(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test FIRST_AVAILABLE strategy returns first track with capacity."""
    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, manager)
    selected = selector.select_track(tracks, required_length=20.0)
    assert selected == tracks[0]


def test_least_occupied_strategy(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test LEAST_OCCUPIED strategy returns track with lowest utilization."""
    manager.add_wagon(tracks[0], wagon_length=50.0)
    manager.add_wagon(tracks[1], wagon_length=25.0)

    selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, manager)
    selected = selector.select_track(tracks, required_length=10.0)
    assert selected == tracks[2]  # Empty track


def test_round_robin_strategy(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test ROUND_ROBIN strategy cycles through tracks."""
    selector = TrackSelector(TrackSelectionStrategy.ROUND_ROBIN, manager)

    assert selector.select_track(tracks, required_length=10.0) == tracks[0]
    assert selector.select_track(tracks, required_length=10.0) == tracks[1]
    assert selector.select_track(tracks, required_length=10.0) == tracks[2]
    assert selector.select_track(tracks, required_length=10.0) == tracks[0]  # Wraps


def test_random_strategy(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test RANDOM strategy returns valid track."""
    selector = TrackSelector(TrackSelectionStrategy.RANDOM, manager)
    selected = selector.select_track(tracks, required_length=10.0)
    assert selected in tracks


def test_no_available_tracks(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test returns None when no tracks can accommodate."""
    for track in tracks:
        manager.add_wagon(track, wagon_length=100.0)  # Fill to capacity

    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, manager)
    assert selector.select_track(tracks, required_length=10.0) is None


def test_get_available_tracks(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test get_available_tracks returns only tracks with capacity."""
    manager.add_wagon(tracks[0], wagon_length=100.0)  # Fill to capacity

    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, manager)
    available = selector.get_available_tracks(tracks, required_length=10.0)

    assert len(available) == 2
    assert tracks[0] not in available
    assert tracks[1] in available
    assert tracks[2] in available


def test_reset_round_robin(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test reset_round_robin resets index to start."""
    selector = TrackSelector(TrackSelectionStrategy.ROUND_ROBIN, manager)

    selector.select_track(tracks, required_length=10.0)
    selector.select_track(tracks, required_length=10.0)

    selector.reset_round_robin()
    assert selector.select_track(tracks, required_length=10.0) == tracks[0]


def test_strategy_property(manager: TrackOccupancyManager) -> None:
    """Test strategy property returns configured strategy."""
    selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, manager)
    assert selector.strategy == TrackSelectionStrategy.LEAST_OCCUPIED


def test_empty_track_list(manager: TrackOccupancyManager) -> None:
    """Test selection with empty track list."""
    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, manager)
    assert selector.select_track([], required_length=10.0) is None


def test_least_occupied_with_equal_utilization(manager: TrackOccupancyManager, tracks: list[Track]) -> None:
    """Test LEAST_OCCUPIED returns first when utilization is equal."""
    manager.add_wagon(tracks[0], wagon_length=25.0)
    manager.add_wagon(tracks[1], wagon_length=25.0)
    manager.add_wagon(tracks[2], wagon_length=25.0)

    selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, manager)
    selected = selector.select_track(tracks, required_length=10.0)
    assert selected == tracks[0]


def test_selection_with_fill_factor(manager: TrackOccupancyManager) -> None:
    """Test track selection respects 75% fill factor."""
    tracks_75 = [
        Track(uuid4(), 'T1', TrackType.COLLECTION, total_length=100.0, fill_factor=0.75),
        Track(uuid4(), 'T2', TrackType.COLLECTION, total_length=100.0, fill_factor=0.75),
    ]

    # Capacity is 75m per track
    manager.add_wagon(tracks_75[0], wagon_length=70.0)

    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, manager)

    # 10m wagon fits in T1 (70 + 10 = 80 > 75, should fail)
    selected = selector.select_track(tracks_75, required_length=10.0)
    assert selected == tracks_75[1]  # Should select T2

    # 5m wagon fits in T1 (70 + 5 = 75, exactly at capacity)
    selected = selector.select_track(tracks_75, required_length=5.0)
    assert selected == tracks_75[0]
