"""Tests for Railway Yard aggregate."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.aggregates.railway_yard import RailwayYard
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant
import pytest


@pytest.fixture
def tracks() -> list[Track]:
    """Create test tracks."""
    return [
        Track(uuid4(), 'Collection_1', TrackType.COLLECTION, 200.0, fill_factor=1.0),
        Track(uuid4(), 'Workshop_1', TrackType.WORKSHOP, 150.0, max_wagons=5),
        Track(uuid4(), 'Parking_1', TrackType.PARKING, 300.0, fill_factor=0.8),
    ]


@pytest.fixture
def yard(tracks: list[Track]) -> RailwayYard:
    """Create test railway yard."""
    yard = RailwayYard('YARD_01', 'Test Yard')
    for track in tracks:
        yard.add_track(track)
    return yard


def test_yard_creation(yard: RailwayYard) -> None:
    """Test yard creation and initialization."""
    assert yard.yard_id == 'YARD_01'
    assert yard.name == 'Test Yard'
    assert len(yard.tracks) == 3
    assert len(yard._track_occupancies) == 3
    assert yard.get_yard_utilization() == 0.0


def test_add_occupant_to_track(yard: RailwayYard) -> None:
    """Test adding occupant to track."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)

    success = yard.add_occupant_to_track('Collection_1', occupant, 1.0)
    assert success

    occupancy = yard.get_track_occupancy('Collection_1')
    assert occupancy is not None
    assert occupancy.get_wagon_count() == 1
    assert occupancy.get_current_occupancy_meters() == 20.0


def test_yard_utilization_calculation(yard: RailwayYard) -> None:
    """Test yard utilization calculation."""
    # Add occupants to different tracks
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 50.0, 0.0)
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 30.0, 0.0)

    yard.add_occupant_to_track('Collection_1', occupant1, 1.0)
    yard.add_occupant_to_track('Workshop_1', occupant2, 1.0)

    # Total capacity: 200 + 112.5 + 240 = 552.5
    # Total occupied: 50 + 30 = 80
    # Utilization: 80/552.5 ≈ 14.48%
    utilization = yard.get_yard_utilization()
    assert 14.0 < utilization < 15.0


def test_move_occupant_between_tracks(yard: RailwayYard) -> None:
    """Test moving occupant between tracks."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)

    # Add to first track
    yard.add_occupant_to_track('Collection_1', occupant, 1.0)

    # Move to second track
    success = yard.move_occupant_between_tracks('W1', 'Collection_1', 'Workshop_1', 2.0)
    assert success

    # Verify move
    collection_occupancy = yard.get_track_occupancy('Collection_1')
    workshop_occupancy = yard.get_track_occupancy('Workshop_1')

    assert collection_occupancy is not None
    assert workshop_occupancy is not None
    assert collection_occupancy.get_wagon_count() == 0
    assert workshop_occupancy.get_wagon_count() == 1


def test_move_occupant_insufficient_capacity(yard: RailwayYard) -> None:
    """Test moving occupant when destination has insufficient capacity."""
    # Fill workshop track to capacity (5 wagons max)
    for i in range(5):
        occupant = TrackOccupant(f'W{i}', OccupantType.WAGON, 20.0, float(i * 20))
        yard.add_occupant_to_track('Workshop_1', occupant, 1.0)

    # Add occupant to collection track
    extra_occupant = TrackOccupant('W_EXTRA', OccupantType.WAGON, 20.0, 0.0)
    yard.add_occupant_to_track('Collection_1', extra_occupant, 1.0)

    # Try to move to full workshop - should fail
    success = yard.move_occupant_between_tracks('W_EXTRA', 'Collection_1', 'Workshop_1', 2.0)
    assert not success

    # Verify occupant stayed in original track
    collection_occupancy = yard.get_track_occupancy('Collection_1')
    assert collection_occupancy is not None
    assert collection_occupancy.get_wagon_count() == 1


def test_shunting_operation_management(yard: RailwayYard) -> None:
    """Test shunting operation capacity management."""
    assert yard.can_start_shunting_operation()

    # Start operations up to limit
    for _ in range(3):
        success = yard.start_shunting_operation()
        assert success

    # Should not be able to start another
    assert not yard.can_start_shunting_operation()
    success = yard.start_shunting_operation()
    assert not success

    # End one operation
    yard.end_shunting_operation()
    assert yard.can_start_shunting_operation()


def test_yard_capacity_limit(yard: RailwayYard) -> None:
    """Test yard capacity limit enforcement."""
    # Set low capacity limit for testing
    yard._max_capacity_percentage = 15.0

    # Fill yard to near capacity
    large_occupant = TrackOccupant('LARGE', OccupantType.RAKE, 100.0, 0.0)
    yard.add_occupant_to_track('Collection_1', large_occupant, 1.0)

    # Should be at capacity (100/552.5 = 18.1% > 15%)
    assert yard.is_yard_at_capacity()

    # Should not be able to add more
    another_occupant = TrackOccupant('W2', OccupantType.WAGON, 20.0, 0.0)
    success = yard.add_occupant_to_track('Workshop_1', another_occupant, 1.0)
    assert not success


def test_get_available_tracks_for_type(yard: RailwayYard) -> None:
    """Test getting available tracks by type."""
    available_collection = yard.get_available_tracks_for_type('collection')
    assert len(available_collection) == 1
    assert available_collection[0].name == 'Collection_1'

    available_workshop = yard.get_available_tracks_for_type('workshop_area')
    assert len(available_workshop) == 1
    assert available_workshop[0].name == 'Workshop_1'


def test_yard_metrics(yard: RailwayYard) -> None:
    """Test comprehensive yard metrics."""
    # Add some occupants
    occupant1 = TrackOccupant('W1', OccupantType.WAGON, 30.0, 0.0)
    occupant2 = TrackOccupant('W2', OccupantType.WAGON, 25.0, 0.0)

    yard.add_occupant_to_track('Collection_1', occupant1, 1.0)
    yard.add_occupant_to_track('Workshop_1', occupant2, 1.0)
    yard.start_shunting_operation()

    metrics = yard.get_yard_metrics()

    assert metrics['yard_id'] == 'YARD_01'
    assert metrics['total_tracks'] == 3
    assert metrics['active_shunting_operations'] == 1
    assert not metrics['at_capacity']
    assert 'track_metrics' in metrics
    assert len(metrics['track_metrics']) == 3


def test_nonexistent_track_operations(yard: RailwayYard) -> None:
    """Test operations on non-existent tracks."""
    occupant = TrackOccupant('W1', OccupantType.WAGON, 20.0, 0.0)

    # Should fail for non-existent track
    success = yard.add_occupant_to_track('NonExistent', occupant, 1.0)
    assert not success

    # Should return None for non-existent track
    occupancy = yard.get_track_occupancy('NonExistent')
    assert occupancy is None
