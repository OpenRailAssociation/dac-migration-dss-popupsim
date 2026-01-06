"""Tests for TrackOccupancyManager domain service."""

from uuid import uuid4

import pytest

from popupsim.backend.src.contexts.railway_infrastructure.domain.entities.track import Track
from popupsim.backend.src.contexts.railway_infrastructure.domain.entities.track import TrackType
from popupsim.backend.src.contexts.railway_infrastructure.domain.services.track_occupancy_manager import (
    TrackOccupancyManager,
)


@pytest.fixture
def manager() -> TrackOccupancyManager:
    """Create occupancy manager."""
    return TrackOccupancyManager()


@pytest.fixture
def track() -> Track:
    """Create test track."""
    return Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=100.0, fill_factor=0.75)


def test_initial_state(manager: TrackOccupancyManager, track: Track) -> None:
    """Test manager starts with empty state."""
    assert manager.get_current_occupancy(track) == 0.0
    assert manager.get_wagon_count(track) == 0
    assert manager.is_empty(track)
    assert not manager.is_full(track)


def test_can_accommodate(manager: TrackOccupancyManager, track: Track) -> None:
    """Test capacity check."""
    assert manager.can_accommodate(track, 50.0)
    assert manager.can_accommodate(track, 75.0)
    assert not manager.can_accommodate(track, 76.0)


def test_add_wagon(manager: TrackOccupancyManager, track: Track) -> None:
    """Test adding wagon updates state."""
    manager.add_wagon(track, 20.0)
    assert manager.get_current_occupancy(track) == 20.0
    assert manager.get_wagon_count(track) == 1


def test_add_multiple_wagons(manager: TrackOccupancyManager, track: Track) -> None:
    """Test adding multiple wagons."""
    manager.add_wagon(track, 20.0)
    manager.add_wagon(track, 30.0)
    assert manager.get_current_occupancy(track) == 50.0
    assert manager.get_wagon_count(track) == 2


def test_add_wagon_exceeds_capacity(manager: TrackOccupancyManager, track: Track) -> None:
    """Test adding wagon that exceeds capacity raises error."""
    manager.add_wagon(track, 70.0)
    with pytest.raises(ValueError, match='cannot accommodate'):
        manager.add_wagon(track, 10.0)


def test_remove_wagon(manager: TrackOccupancyManager, track: Track) -> None:
    """Test removing wagon updates state."""
    manager.add_wagon(track, 30.0)
    manager.remove_wagon(track, 30.0)
    assert manager.get_current_occupancy(track) == 0.0
    assert manager.get_wagon_count(track) == 0


def test_remove_wagon_negative_length(manager: TrackOccupancyManager, track: Track) -> None:
    """Test removing negative length raises error."""
    with pytest.raises(ValueError, match='negative'):
        manager.remove_wagon(track, -10.0)


def test_get_available_capacity(manager: TrackOccupancyManager, track: Track) -> None:
    """Test available capacity calculation."""
    assert manager.get_available_capacity(track) == 75.0
    manager.add_wagon(track, 25.0)
    assert manager.get_available_capacity(track) == 50.0


def test_get_utilization_percentage(manager: TrackOccupancyManager, track: Track) -> None:
    """Test utilization percentage calculation."""
    assert manager.get_utilization_percentage(track) == 0.0
    manager.add_wagon(track, 37.5)
    assert manager.get_utilization_percentage(track) == 50.0


def test_workshop_track_wagon_limit(manager: TrackOccupancyManager) -> None:
    """Test workshop track enforces wagon count limit."""
    workshop = Track(uuid4(), 'Workshop A', TrackType.WORKSHOP, total_length=100.0, fill_factor=0.75, max_wagons=3)

    manager.add_wagon(workshop, 10.0)
    manager.add_wagon(workshop, 10.0)
    manager.add_wagon(workshop, 10.0)

    assert manager.get_wagon_count(workshop) == 3
    with pytest.raises(ValueError, match='wagon count limit'):
        manager.add_wagon(workshop, 10.0)


def test_reset_specific_track(manager: TrackOccupancyManager) -> None:
    """Test resetting specific track."""
    track1 = Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    track2 = Track(uuid4(), 'Collection 2', TrackType.COLLECTION, total_length=100.0)

    manager.add_wagon(track1, 20.0)
    manager.add_wagon(track2, 30.0)

    manager.reset(track1)
    assert manager.get_current_occupancy(track1) == 0.0
    assert manager.get_current_occupancy(track2) == 30.0


def test_reset_all_tracks(manager: TrackOccupancyManager) -> None:
    """Test resetting all tracks."""
    track1 = Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    track2 = Track(uuid4(), 'Collection 2', TrackType.COLLECTION, total_length=100.0)

    manager.add_wagon(track1, 20.0)
    manager.add_wagon(track2, 30.0)

    manager.reset()
    assert manager.get_current_occupancy(track1) == 0.0
    assert manager.get_current_occupancy(track2) == 0.0
