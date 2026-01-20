"""Tests for TrackOccupancyRepository."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
import pytest


@pytest.fixture
def repository() -> TrackOccupancyRepository:
    """Create repository."""
    return TrackOccupancyRepository()


@pytest.fixture
def track() -> Track:
    """Create test track."""
    return Track(uuid4(), 'Test Track', TrackType.COLLECTION, total_length=100.0)


def test_get_or_create_new_track(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test creating new occupancy for track."""
    occupancy = repository.get_or_create(track)

    assert occupancy.track_id == track.id
    assert occupancy.track_specification == track
    assert occupancy.is_empty()


def test_get_or_create_existing_track(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test getting existing occupancy."""
    occupancy1 = repository.get_or_create(track)
    occupancy2 = repository.get_or_create(track)

    assert occupancy1 is occupancy2  # Same instance


def test_get_nonexistent_track(repository: TrackOccupancyRepository) -> None:
    """Test getting non-existent track."""
    result = repository.get(uuid4())
    assert result is None


def test_get_existing_track(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test getting existing track."""
    occupancy = repository.get_or_create(track)
    result = repository.get(track.id)

    assert result is occupancy


def test_get_occupancy_history(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test getting occupancy history."""
    occupancy = repository.get_or_create(track)

    # Add some occupants to create history
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 15.0, 20.0)

    occupancy.add_occupant(occupant1, 1.0)
    occupancy.add_occupant(occupant2, 3.0)

    # Get history for time range
    history = repository.get_occupancy_history(track.id, 0.5, 2.5)

    assert len(history) == 1  # Only first snapshot in range
    assert history[0].timestamp == 1.0


def test_get_occupancy_history_empty_track(repository: TrackOccupancyRepository) -> None:
    """Test getting history for non-existent track."""
    history = repository.get_occupancy_history(uuid4(), 0.0, 10.0)
    assert history == []


def test_reset_specific_track(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test resetting specific track."""
    occupancy = repository.get_or_create(track)
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupancy.add_occupant(occupant, 1.0)

    repository.reset(track.id)

    # Track should be removed from repository
    result = repository.get(track.id)
    assert result is None


def test_reset_all_tracks(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test resetting all tracks."""
    track2 = Track(uuid4(), 'Track 2', TrackType.COLLECTION, 100.0)

    repository.get_or_create(track)
    repository.get_or_create(track2)

    repository.reset()

    assert repository.get(track.id) is None
    assert repository.get(track2.id) is None


def test_get_all_occupancies(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test getting all occupancies."""
    track2 = Track(uuid4(), 'Track 2', TrackType.COLLECTION, 100.0)

    occupancy1 = repository.get_or_create(track)
    occupancy2 = repository.get_or_create(track2)

    all_occupancies = repository.get_all_occupancies()

    assert len(all_occupancies) == 2
    assert all_occupancies[track.id] is occupancy1
    assert all_occupancies[track2.id] is occupancy2


def test_get_all_occupancies_copy(repository: TrackOccupancyRepository, track: Track) -> None:
    """Test get_all_occupancies returns copy."""
    repository.get_or_create(track)

    all_occupancies = repository.get_all_occupancies()
    all_occupancies.clear()  # Modify returned dict

    # Original should be unchanged
    assert len(repository.get_all_occupancies()) == 1
