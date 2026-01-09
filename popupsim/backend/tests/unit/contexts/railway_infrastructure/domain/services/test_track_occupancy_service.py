"""Tests for TrackOccupancyService."""

from uuid import UUID
from uuid import uuid4

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.services.track_occupancy_service import TrackOccupancyService
import pytest


@pytest.fixture
def repository() -> TrackOccupancyRepository:
    """Create repository."""
    return TrackOccupancyRepository()


@pytest.fixture
def service(repository: TrackOccupancyRepository) -> TrackOccupancyService:
    """Create service."""
    return TrackOccupancyService(repository)


@pytest.fixture
def track() -> Track:
    """Create test track with no fill factor for precise calculations."""
    return Track(uuid4(), 'Test Track', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0)


@pytest.fixture
def workshop_track() -> Track:
    """Create workshop track with wagon limit and no fill factor."""
    return Track(uuid4(), 'Workshop', TrackType.WORKSHOP, total_length=100.0, fill_factor=1.0, max_wagons=2)


def test_allocate_wagon_success(service: TrackOccupancyService, track: Track) -> None:
    """Test successful wagon allocation."""
    success = service.allocate_wagon(track, 'W1', 20.0, 1.0)

    assert success
    assert service.get_current_occupancy(track) == 20.0
    assert service.get_wagon_count(track) == 1


def test_allocate_wagon_insufficient_space(service: TrackOccupancyService, track: Track) -> None:
    """Test wagon allocation with insufficient space."""
    # Fill track almost completely
    service.allocate_wagon(track, 'W1', 95.0, 1.0)

    # Try to add wagon that doesn't fit
    success = service.allocate_wagon(track, 'W2', 20.0, 2.0)

    assert not success
    assert service.get_wagon_count(track) == 1  # Only first wagon


def test_allocate_wagon_count_limit(service: TrackOccupancyService, workshop_track: Track) -> None:
    """Test wagon allocation with count limit."""
    # Add wagons up to limit
    service.allocate_wagon(workshop_track, 'W1', 20.0, 1.0)
    service.allocate_wagon(workshop_track, 'W2', 20.0, 2.0)

    # Try to exceed limit
    success = service.allocate_wagon(workshop_track, 'W3', 20.0, 3.0)

    assert not success
    assert service.get_wagon_count(workshop_track) == 2


def test_deallocate_wagon_success(service: TrackOccupancyService, track: Track) -> None:
    """Test successful wagon deallocation."""
    service.allocate_wagon(track, 'W1', 20.0, 1.0)

    success = service.deallocate_wagon(track, 'W1', 2.0)

    assert success
    assert service.get_current_occupancy(track) == 0.0
    assert service.is_empty(track)


def test_deallocate_wagon_not_found(service: TrackOccupancyService, track: Track) -> None:
    """Test deallocation of non-existent wagon."""
    success = service.deallocate_wagon(track, 'W999', 1.0)
    assert not success


def test_allocate_rake_success(service: TrackOccupancyService, track: Track) -> None:
    """Test successful rake allocation."""
    success = service.allocate_rake(track, 'R1', 50.0, 1.0)

    assert success
    assert service.get_current_occupancy(track) == 52.0  # 50 + 2 buffer


def test_allocate_rake_insufficient_space(service: TrackOccupancyService, track: Track) -> None:
    """Test rake allocation with insufficient space."""
    success = service.allocate_rake(track, 'R1', 120.0, 1.0)  # Too long
    assert not success


def test_can_accommodate_true(service: TrackOccupancyService, track: Track) -> None:
    """Test can_accommodate returns true for available space."""
    assert service.can_accommodate(track, 50.0)


def test_can_accommodate_false(service: TrackOccupancyService, track: Track) -> None:
    """Test can_accommodate returns false for insufficient space."""
    service.allocate_wagon(track, 'W1', 90.0, 1.0)
    assert not service.can_accommodate(track, 20.0)


def test_get_available_capacity(service: TrackOccupancyService, track: Track) -> None:
    """Test getting available capacity."""
    service.allocate_wagon(track, 'W1', 30.0, 1.0)

    available = service.get_available_capacity(track)
    assert available == 70.0


def test_get_utilization_percentage(service: TrackOccupancyService, track: Track) -> None:
    """Test getting utilization percentage."""
    service.allocate_wagon(track, 'W1', 25.0, 1.0)

    utilization = service.get_utilization_percentage(track)
    assert utilization == 25.0


def test_is_full_length_constraint(service: TrackOccupancyService, track: Track) -> None:
    """Test is_full with length constraint."""
    service.allocate_wagon(track, 'W1', 95.0, 1.0)

    assert service.is_full(track, 10.0)  # Can't fit 10m wagon
    assert not service.is_full(track, 5.0)  # Can fit 5m wagon


def test_is_full_count_constraint(service: TrackOccupancyService, workshop_track: Track) -> None:
    """Test is_full with wagon count constraint."""
    service.allocate_wagon(workshop_track, 'W1', 20.0, 1.0)
    service.allocate_wagon(workshop_track, 'W2', 20.0, 2.0)

    assert service.is_full(workshop_track)  # At wagon limit


def test_reset_track(service: TrackOccupancyService, track: Track) -> None:
    """Test resetting specific track."""
    service.allocate_wagon(track, 'W1', 20.0, 1.0)

    # Ensure track.id is UUID for the service call
    track_id = track.id if isinstance(track.id, UUID) else UUID(track.id)
    service.reset_track(track_id)

    # Should create new empty occupancy
    assert service.get_current_occupancy(track) == 0.0


def test_reset_all_tracks(service: TrackOccupancyService, track: Track) -> None:
    """Test resetting all tracks."""
    track2 = Track(uuid4(), 'Track 2', TrackType.COLLECTION, 100.0)

    service.allocate_wagon(track, 'W1', 20.0, 1.0)
    service.allocate_wagon(track2, 'W2', 30.0, 1.0)

    service.reset_all_tracks()

    assert service.get_current_occupancy(track) == 0.0
    assert service.get_current_occupancy(track2) == 0.0
