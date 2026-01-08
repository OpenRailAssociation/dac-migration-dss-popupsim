"""Tests for TrackSelector domain service."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackAccess
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.services.track_selector import TrackSelector
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy
import pytest


@pytest.fixture
def repository() -> TrackOccupancyRepository:
    """Create occupancy repository."""
    return TrackOccupancyRepository()


@pytest.fixture
def tracks() -> list[Track]:
    """Create test tracks with sufficient capacity."""
    return [
        Track(uuid4(), 'C1', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0),
        Track(uuid4(), 'C2', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0),
        Track(uuid4(), 'C3', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0),
    ]


def test_first_available_strategy(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test FIRST_AVAILABLE strategy returns first track with capacity."""
    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, repository)
    selected = selector.select_track(tracks, required_length=20.0)
    assert selected == tracks[0]


def test_least_occupied_strategy(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test LEAST_OCCUPIED strategy returns track with lowest utilization."""
    # Add occupants to tracks
    occupancy0 = repository.get_or_create(tracks[0])
    occupancy1 = repository.get_or_create(tracks[1])

    occupancy0.add_occupant(TrackOccupant('W1', OccupantType.WAGON, 50.0, 0.0), 0.0)
    occupancy1.add_occupant(TrackOccupant('W2', OccupantType.WAGON, 25.0, 0.0), 0.0)

    selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, repository)
    selected = selector.select_track(tracks, required_length=10.0)
    assert selected == tracks[2]  # Empty track


def test_round_robin_strategy(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test ROUND_ROBIN strategy cycles through tracks."""
    selector = TrackSelector(TrackSelectionStrategy.ROUND_ROBIN, repository)

    assert selector.select_track(tracks, required_length=10.0) == tracks[0]
    assert selector.select_track(tracks, required_length=10.0) == tracks[1]
    assert selector.select_track(tracks, required_length=10.0) == tracks[2]
    assert selector.select_track(tracks, required_length=10.0) == tracks[0]  # Wraps


def test_random_strategy(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test RANDOM strategy returns valid track."""
    selector = TrackSelector(TrackSelectionStrategy.RANDOM, repository)
    selected = selector.select_track(tracks, required_length=10.0)
    assert selected in tracks


def test_no_available_tracks(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test returns None when no tracks can accommodate."""
    for track in tracks:
        occupancy = repository.get_or_create(track)
        occupancy.add_occupant(TrackOccupant(f'W{track.name}', OccupantType.WAGON, 100.0, 0.0), 0.0)

    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, repository)
    assert selector.select_track(tracks, required_length=10.0) is None


def test_get_available_tracks(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test get_available_tracks returns only tracks with capacity."""
    occupancy = repository.get_or_create(tracks[0])
    occupancy.add_occupant(TrackOccupant('W1', OccupantType.WAGON, 100.0, 0.0), 0.0)

    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, repository)
    available = selector.get_available_tracks(tracks, required_length=10.0)

    assert len(available) == 2
    assert tracks[0] not in available
    assert tracks[1] in available
    assert tracks[2] in available


def test_reset_round_robin(repository: TrackOccupancyRepository, tracks: list[Track]) -> None:
    """Test reset_round_robin resets index to start."""
    selector = TrackSelector(TrackSelectionStrategy.ROUND_ROBIN, repository)

    selector.select_track(tracks, required_length=10.0)
    selector.select_track(tracks, required_length=10.0)

    selector.reset_round_robin()
    assert selector.select_track(tracks, required_length=10.0) == tracks[0]


def test_strategy_property(repository: TrackOccupancyRepository) -> None:
    """Test strategy property returns configured strategy."""
    selector = TrackSelector(TrackSelectionStrategy.LEAST_OCCUPIED, repository)
    assert selector.strategy == TrackSelectionStrategy.LEAST_OCCUPIED


def test_empty_track_list(repository: TrackOccupancyRepository) -> None:
    """Test selection with empty track list."""
    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, repository)
    assert selector.select_track([], required_length=10.0) is None


def test_track_access_constraints(repository: TrackOccupancyRepository) -> None:
    """Test track access direction constraints."""
    front_only_track = Track(uuid4(), 'F1', TrackType.COLLECTION, 100.0, access=TrackAccess.FRONT_ONLY)
    rear_only_track = Track(uuid4(), 'R1', TrackType.COLLECTION, 100.0, access=TrackAccess.REAR_ONLY)

    # Fill front of front-only track
    occupancy = repository.get_or_create(front_only_track)
    occupancy.add_occupant(TrackOccupant('W1', OccupantType.WAGON, 50.0, 0.0), 0.0)

    selector = TrackSelector(TrackSelectionStrategy.FIRST_AVAILABLE, repository)

    # Should not select front-only track (can't add at rear)
    selected = selector.select_track([front_only_track, rear_only_track], required_length=20.0)
    assert selected == rear_only_track
