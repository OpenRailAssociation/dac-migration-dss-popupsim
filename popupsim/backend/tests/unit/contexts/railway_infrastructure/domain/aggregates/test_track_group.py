"""Tests for TrackGroup aggregate."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.aggregates.track_group import TrackGroup
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy
import pytest


@pytest.fixture
def collection_tracks() -> list[Track]:
    """Create collection tracks for testing."""
    return [
        Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=150.0, fill_factor=0.75),
        Track(uuid4(), 'Collection 2', TrackType.COLLECTION, total_length=200.0, fill_factor=0.75),
        Track(uuid4(), 'Collection 3', TrackType.COLLECTION, total_length=100.0, fill_factor=0.75),
    ]


@pytest.fixture
def workshop_tracks() -> list[Track]:
    """Create workshop tracks for testing."""
    return [
        Track(uuid4(), 'Workshop A', TrackType.WORKSHOP, total_length=100.0, fill_factor=0.75, max_wagons=5),
        Track(uuid4(), 'Workshop B', TrackType.WORKSHOP, total_length=120.0, fill_factor=0.75, max_wagons=6),
    ]


@pytest.fixture
def track_group(collection_tracks: list[Track]) -> TrackGroup:
    """Create track group with collection tracks."""
    group = TrackGroup('collection_group', TrackType.COLLECTION)
    for track in collection_tracks:
        group.add_track(track)
    return group


def test_track_group_initialization() -> None:
    """Test track group initialization."""
    group = TrackGroup('test_group', TrackType.COLLECTION)
    assert group.group_id == 'test_group'
    assert group.track_type == TrackType.COLLECTION
    assert len(group.tracks) == 0


def test_add_track(collection_tracks: list[Track]) -> None:
    """Test adding tracks to group."""
    group = TrackGroup('test_group', TrackType.COLLECTION)
    track = collection_tracks[0]
    group.add_track(track)
    assert track.id in group.tracks
    assert group.tracks[track.id] == track


def test_add_track_type_mismatch(collection_tracks: list[Track]) -> None:
    """Test adding track with wrong type raises error."""
    group = TrackGroup('test_group', TrackType.RETROFIT)
    with pytest.raises(ValueError, match='Track type mismatch'):
        group.add_track(collection_tracks[0])


def test_set_selection_strategy(track_group: TrackGroup) -> None:
    """Test changing selection strategy."""
    track_group.set_selection_strategy(TrackSelectionStrategy.RANDOM)
    assert track_group._selector.strategy == TrackSelectionStrategy.RANDOM


def test_get_track(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test getting track by ID."""
    track = collection_tracks[0]
    result = track_group.get_track(track.id)
    assert result == track


def test_get_track_not_found(track_group: TrackGroup) -> None:
    """Test getting non-existent track returns None."""
    result = track_group.get_track(uuid4())
    assert result is None


def test_get_total_capacity(track_group: TrackGroup) -> None:
    """Test total capacity calculation."""
    expected = 150.0 * 0.75 + 200.0 * 0.75 + 100.0 * 0.75
    assert track_group.get_total_capacity() == expected


def test_get_total_occupancy(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test total occupancy calculation."""
    track_group._occupancy_manager.add_wagon(collection_tracks[0], 20.0)
    track_group._occupancy_manager.add_wagon(collection_tracks[1], 30.0)
    assert track_group.get_total_occupancy() == 50.0


def test_get_average_utilization(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test average utilization calculation."""
    track_group._occupancy_manager.add_wagon(collection_tracks[0], 56.25)
    utilization = track_group.get_average_utilization()
    assert utilization == pytest.approx(16.67, rel=0.01)


def test_get_average_utilization_empty_group() -> None:
    """Test average utilization for empty group."""
    group = TrackGroup('empty_group', TrackType.COLLECTION)
    assert group.get_average_utilization() == 0.0


def test_get_available_tracks(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test getting available tracks."""
    track_group._occupancy_manager.add_wagon(collection_tracks[0], 100.0)
    available = track_group.get_available_tracks(20.0)
    assert len(available) == 2
    assert collection_tracks[0] not in available


def test_select_track_for_wagon(track_group: TrackGroup) -> None:
    """Test track selection for wagon."""
    track = track_group.select_track_for_wagon(20.0)
    assert track is not None
    assert track in track_group.tracks.values()


def test_select_track_for_wagon_no_capacity(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test track selection when no capacity available."""
    for t in collection_tracks:
        track_group._occupancy_manager.add_wagon(t, t.capacity)
    track = track_group.select_track_for_wagon(20.0)
    assert track is None


def test_try_add_wagon_to_group_success(track_group: TrackGroup) -> None:
    """Test successfully adding wagon to group."""
    track, success = track_group.try_add_wagon_to_group(20.0)
    assert success is True
    assert track is not None
    assert track_group.get_total_occupancy() == 20.0


def test_try_add_wagon_to_group_no_capacity(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test adding wagon when group is full."""
    for t in collection_tracks:
        track_group._occupancy_manager.add_wagon(t, t.capacity)
    track, success = track_group.try_add_wagon_to_group(20.0)
    assert success is False
    assert track is None


def test_remove_wagon_from_group_success(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test successfully removing wagon from group."""
    track = collection_tracks[0]
    track_group._occupancy_manager.add_wagon(track, 20.0)
    result = track_group.remove_wagon_from_group(track.id, 20.0)
    assert result is True
    assert track_group.get_total_occupancy() == 0.0


def test_remove_wagon_from_group_track_not_found(track_group: TrackGroup) -> None:
    """Test removing wagon from non-existent track."""
    result = track_group.remove_wagon_from_group(uuid4(), 20.0)
    assert result is False


def test_get_total_available_capacity(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test total available capacity calculation."""
    track_group._occupancy_manager.add_wagon(collection_tracks[0], 50.0)
    total_capacity = track_group.get_total_capacity()
    available = track_group.get_total_available_capacity()
    assert available == total_capacity - 50.0


def test_is_group_full_false(track_group: TrackGroup) -> None:
    """Test group not full."""
    assert track_group.is_group_full(15.0) is False


def test_is_group_full_true(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test group is full."""
    for t in collection_tracks:
        track_group._occupancy_manager.add_wagon(t, t.capacity)
    assert track_group.is_group_full(15.0) is True


def test_workshop_track_wagon_count_limit(workshop_tracks: list[Track]) -> None:
    """Test workshop tracks enforce wagon count limits."""
    group = TrackGroup('workshop_group', TrackType.WORKSHOP)
    for track in workshop_tracks:
        group.add_track(track)

    workshop_a = workshop_tracks[0]
    for _ in range(5):
        group._occupancy_manager.add_wagon(workshop_a, 10.0)

    with pytest.raises(ValueError, match='wagon count limit reached'):
        group._occupancy_manager.add_wagon(workshop_a, 10.0)


def test_least_occupied_strategy(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test least occupied selection strategy."""
    track_group.set_selection_strategy(TrackSelectionStrategy.LEAST_OCCUPIED)
    track_group._occupancy_manager.add_wagon(collection_tracks[0], 50.0)
    track_group._occupancy_manager.add_wagon(collection_tracks[1], 30.0)

    selected = track_group.select_track_for_wagon(20.0)
    assert selected == collection_tracks[2]


def test_first_available_strategy(track_group: TrackGroup, collection_tracks: list[Track]) -> None:
    """Test first available selection strategy."""
    track_group.set_selection_strategy(TrackSelectionStrategy.FIRST_AVAILABLE)
    selected = track_group.select_track_for_wagon(20.0)
    assert selected == collection_tracks[0]
