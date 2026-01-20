"""Tests for TrackGroup aggregate with service pattern."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.aggregates.track_group import TrackGroup
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.services.track_group_service import TrackGroupService
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


@pytest.fixture
def repository() -> TrackOccupancyRepository:
    """Create track occupancy repository."""
    return TrackOccupancyRepository()


@pytest.fixture
def service(repository: TrackOccupancyRepository) -> TrackGroupService:
    """Create track group service."""
    return TrackGroupService(repository)


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
    assert track_group.selection_strategy == TrackSelectionStrategy.RANDOM


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


@pytest.mark.usefixtures('collection_tracks')
def test_get_total_occupancy(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test total occupancy calculation."""
    service.try_add_wagon(track_group, 'W1', 20.0, 1.0)
    service.try_add_wagon(track_group, 'W2', 30.0, 2.0)
    assert service.get_group_occupancy(track_group) == 50.0


@pytest.mark.usefixtures('collection_tracks')
def test_get_average_utilization(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test average utilization calculation."""
    service.try_add_wagon(track_group, 'W1', 56.25, 1.0)
    utilization = service.get_group_utilization(track_group)
    assert utilization == pytest.approx(16.67, rel=0.01)


def test_get_average_utilization_empty_group(service: TrackGroupService) -> None:
    """Test average utilization for empty group."""
    group = TrackGroup('empty_group', TrackType.COLLECTION)
    assert service.get_group_utilization(group) == 0.0


def test_get_available_tracks(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test getting available tracks."""
    # Fill first track completely
    occupancy = service._repository.get_or_create(collection_tracks[0])
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant

    occupancy.add_occupant(TrackOccupant('W1', OccupantType.WAGON, 112.5, 0.0), 1.0)

    # Get available tracks manually since service doesn't have this method
    available = [t for t in track_group.get_all_tracks() if not service._repository.get_or_create(t).is_full(20.0)]
    assert len(available) == 2
    assert collection_tracks[0] not in available


def test_select_track_for_wagon(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test track selection for wagon."""
    track = service.select_track_for_wagon(track_group, 20.0)
    assert track is not None
    assert track in track_group.tracks.values()


def test_select_track_for_wagon_no_capacity(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test track selection when no capacity available."""
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant

    for t in collection_tracks:
        occupancy = service._repository.get_or_create(t)
        occupancy.add_occupant(TrackOccupant(f'W{t.name}', OccupantType.WAGON, t.capacity, 0.0), 1.0)

    track = service.select_track_for_wagon(track_group, 20.0)
    assert track is None


def test_try_add_wagon_to_group_success(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test successfully adding wagon to group."""
    track, success = service.try_add_wagon(track_group, 'W1', 20.0, 1.0)
    assert success is True
    assert track is not None
    assert service.get_group_occupancy(track_group) == 20.0


def test_try_add_wagon_to_group_no_capacity(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test adding wagon when group is full."""
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant

    for t in collection_tracks:
        occupancy = service._repository.get_or_create(t)
        occupancy.add_occupant(TrackOccupant(f'W{t.name}', OccupantType.WAGON, t.capacity, 0.0), 1.0)

    track, success = service.try_add_wagon(track_group, 'W999', 20.0, 1.0)
    assert success is False
    assert track is None


def test_remove_wagon_from_group_success(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test successfully removing wagon from group."""
    track = collection_tracks[0]
    service.try_add_wagon(track_group, 'W1', 20.0, 1.0)

    result = service.remove_wagon(track_group, str(track.id), 'W1', 2.0)
    assert result is True
    assert service.get_group_occupancy(track_group) == 0.0


def test_remove_wagon_from_group_track_not_found(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test removing wagon from non-existent track."""
    result = service.remove_wagon(track_group, str(uuid4()), 'W1', 1.0)
    assert result is False


@pytest.mark.usefixtures('collection_tracks')
def test_get_total_available_capacity(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test total available capacity calculation."""
    service.try_add_wagon(track_group, 'W1', 50.0, 1.0)
    total_capacity = track_group.get_total_capacity()
    occupied = service.get_group_occupancy(track_group)
    available = total_capacity - occupied
    assert available == total_capacity - 50.0


def test_is_group_full_false(track_group: TrackGroup, service: TrackGroupService) -> None:
    """Test group not full."""
    assert service.is_group_full(track_group, 15.0) is False


def test_is_group_full_true(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test group is full."""
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant

    for t in collection_tracks:
        occupancy = service._repository.get_or_create(t)
        occupancy.add_occupant(TrackOccupant(f'W{t.name}', OccupantType.WAGON, t.capacity, 0.0), 1.0)

    assert service.is_group_full(track_group, 15.0) is True


def test_workshop_track_wagon_count_limit(workshop_tracks: list[Track], service: TrackGroupService) -> None:
    """Test workshop tracks enforce wagon count limits."""
    # Test with single track to ensure limit is enforced
    group = TrackGroup('workshop_group', TrackType.WORKSHOP)
    workshop_a = workshop_tracks[0]  # max_wagons=5
    group.add_track(workshop_a)

    # Add wagons up to limit
    for i in range(5):
        _track, success = service.try_add_wagon(group, f'W{i}', 10.0, float(i))
        assert success

    # Try to exceed limit
    _track, success = service.try_add_wagon(group, 'W6', 10.0, 6.0)
    assert not success


def test_least_occupied_strategy(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test least occupied selection strategy."""
    track_group.set_selection_strategy(TrackSelectionStrategy.LEAST_OCCUPIED)

    # Add different amounts to tracks
    service.try_add_wagon(track_group, 'W1', 50.0, 1.0)
    service.try_add_wagon(track_group, 'W2', 30.0, 2.0)

    selected = service.select_track_for_wagon(track_group, 20.0)
    assert selected == collection_tracks[2]  # Empty track


def test_first_available_strategy(
    track_group: TrackGroup, collection_tracks: list[Track], service: TrackGroupService
) -> None:
    """Test first available selection strategy."""
    track_group.set_selection_strategy(TrackSelectionStrategy.FIRST_AVAILABLE)
    selected = service.select_track_for_wagon(track_group, 20.0)
    assert selected == collection_tracks[0]
