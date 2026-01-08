"""Tests for TrackOccupancy aggregate."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.aggregates.track_occupancy import TrackOccupancy
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackAccess
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
import pytest


@pytest.fixture
def track() -> Track:
    """Create test track."""
    return Track(uuid4(), 'Test Track', TrackType.COLLECTION, total_length=100.0, fill_factor=1.0)


@pytest.fixture
def workshop_track() -> Track:
    """Create workshop track with wagon limit."""
    return Track(uuid4(), 'Workshop', TrackType.WORKSHOP, total_length=100.0, max_wagons=3)


@pytest.fixture
def occupancy(track: Track) -> TrackOccupancy:
    """Create track occupancy."""
    return TrackOccupancy(track.id, track)


def test_empty_track_occupancy(occupancy: TrackOccupancy) -> None:
    """Test empty track state."""
    assert occupancy.get_current_occupancy_meters() == 0.0
    assert occupancy.get_current_occupancy_percentage() == 0.0
    assert occupancy.get_available_capacity() == 100.0
    assert occupancy.get_wagon_count() == 0
    assert occupancy.is_empty()
    assert not occupancy.is_full()


def test_add_single_occupant(occupancy: TrackOccupancy) -> None:
    """Test adding single occupant."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupancy.add_occupant(occupant, 1.0)

    assert occupancy.get_current_occupancy_meters() == 20.0
    assert occupancy.get_current_occupancy_percentage() == 20.0
    assert occupancy.get_available_capacity() == 80.0
    assert occupancy.get_wagon_count() == 1
    assert not occupancy.is_empty()


def test_add_multiple_occupants(occupancy: TrackOccupancy) -> None:
    """Test adding multiple occupants."""
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 15.0, 20.0)

    occupancy.add_occupant(occupant1, 1.0)
    occupancy.add_occupant(occupant2, 2.0)

    assert occupancy.get_current_occupancy_meters() == 35.0
    assert occupancy.get_wagon_count() == 2


def test_remove_occupant(occupancy: TrackOccupancy) -> None:
    """Test removing occupant."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupancy.add_occupant(occupant, 1.0)

    removed = occupancy.remove_occupant('W1', 2.0)

    assert removed == occupant
    assert occupancy.get_current_occupancy_meters() == 0.0
    assert occupancy.is_empty()


def test_remove_nonexistent_occupant(occupancy: TrackOccupancy) -> None:
    """Test removing non-existent occupant."""
    removed = occupancy.remove_occupant('W999', 1.0)
    assert removed is None


def test_find_optimal_position_empty_track(occupancy: TrackOccupancy) -> None:
    """Test position finding on empty track."""
    position = occupancy.find_optimal_position(20.0)
    assert position == 0.0


def test_find_optimal_position_at_end(occupancy: TrackOccupancy) -> None:
    """Test position finding at track end."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 30.0, 0.0)
    occupancy.add_occupant(occupant, 1.0)

    position = occupancy.find_optimal_position(20.0)
    assert position == 30.0  # After existing occupant


def test_find_optimal_position_at_front(occupancy: TrackOccupancy) -> None:
    """Test position finding at track front."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 30.0, 50.0)  # Leave space at front
    occupancy.add_occupant(occupant, 1.0)

    position = occupancy.find_optimal_position(20.0)
    assert position == 0.0  # At front


def test_find_optimal_position_no_space(occupancy: TrackOccupancy) -> None:
    """Test position finding when no space available."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 100.0, 0.0)  # Fill entire track
    occupancy.add_occupant(occupant, 1.0)

    position = occupancy.find_optimal_position(10.0)
    assert position is None


def test_track_access_front_only() -> None:
    """Test front-only track access."""
    track = Track(uuid4(), 'Front Only', TrackType.COLLECTION, 100.0, access=TrackAccess.FRONT_ONLY)
    occupancy = TrackOccupancy(track.id, track)

    # Add occupant at front
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 30.0, 0.0)
    occupancy.add_occupant(occupant1, 1.0)

    # Should not find position at rear
    position = occupancy.find_optimal_position(20.0)
    assert position is None


def test_track_access_rear_only() -> None:
    """Test rear-only track access."""
    track = Track(uuid4(), 'Rear Only', TrackType.COLLECTION, 100.0, access=TrackAccess.REAR_ONLY)
    occupancy = TrackOccupancy(track.id, track)

    # Add first occupant at position 0 (this should work)
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 30.0, 0.0)
    occupancy.add_occupant(occupant1, 1.0)

    # Should find position at rear only (after existing occupant)
    position = occupancy.find_optimal_position(20.0)
    assert position == 30.0  # Only at rear


def test_workshop_track_wagon_limit() -> None:
    """Test workshop track wagon count limit."""
    track = Track(uuid4(), 'Workshop', TrackType.WORKSHOP, 100.0, max_wagons=2)
    occupancy = TrackOccupancy(track.id, track)

    # Add 2 wagons (at limit)
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 20.0, 20.0)

    occupancy.add_occupant(occupant1, 1.0)
    occupancy.add_occupant(occupant2, 2.0)

    assert occupancy.can_accommodate_wagon_count() is False
    assert occupancy.is_full(10.0)  # Full due to wagon count


def test_collision_detection(occupancy: TrackOccupancy) -> None:
    """Test collision detection prevents overlapping occupants."""
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 30.0, 20.0)  # Position 20-50
    occupancy.add_occupant(occupant1, 1.0)

    # Try to add overlapping occupant
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 20.0, 40.0)  # Position 40-60 (overlaps)

    with pytest.raises(ValueError, match='Occupant overlaps with existing occupant'):
        occupancy.add_occupant(occupant2, 2.0)


def test_occupancy_history(occupancy: TrackOccupancy) -> None:
    """Test occupancy history tracking."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)
    occupancy.add_occupant(occupant, 1.0)

    assert len(occupancy._occupancy_history) == 1
    snapshot = occupancy._occupancy_history[0]
    assert snapshot.timestamp == 1.0
    assert snapshot.occupancy_meters == 20.0
    assert snapshot.occupant_count == 1


def test_rake_with_buffer_space(occupancy: TrackOccupancy) -> None:
    """Test rake occupant with buffer space."""
    rake = TrackOccupant('R1', OccupantType.RAKE, 50.0, 0.0, buffer_space=5.0)
    occupancy.add_occupant(rake, 1.0)

    assert occupancy.get_current_occupancy_meters() == 55.0  # 50 + 5 buffer
    assert rake.effective_length == 55.0


def test_sorted_occupants(occupancy: TrackOccupancy) -> None:
    """Test occupants are kept sorted by position."""
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 20.0, 50.0)
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 20.0, 0.0)

    occupancy.add_occupant(occupant1, 1.0)
    occupancy.add_occupant(occupant2, 2.0)

    # Should be sorted by position_start
    assert occupancy._occupants[0].id == 'W2'  # Position 0
    assert occupancy._occupants[1].id == 'W1'  # Position 50
