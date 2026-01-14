"""Integration test for event-driven track occupancy with minimal scenario.

Test scenario:
- 1 collection track (500m * 0.75 = 375m capacity)
- 1 retrofit track (500m * 0.75 = 375m capacity)
- 1 workshop with 1 bay
- 1 parking track (500m * 0.75 = 375m capacity)
- 1 train with 4 wagons (each 20m = 80m total)

Expected: All 4 wagons should complete the full cycle:
1. Arrive and classify to collection track
2. Move to retrofit track
3. Move to workshop
4. Get retrofitted
5. Move to retrofitted track
6. Move to parking track
"""

from unittest.mock import Mock

from contexts.railway_infrastructure.application.track_occupancy_event_handler import TrackOccupancyEventHandler
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from shared.domain.events.wagon_movement_events import WagonMovedEvent


def test_minimal_scenario_track_occupancy() -> None:
    """Test that 4 wagons can move through the system with event-driven track occupancy."""
    # Setup
    repo = TrackOccupancyRepository()
    railway_context = Mock()
    railway_context.get_occupancy_repository.return_value = repo

    # Create tracks
    collection_track = Track(
        id='collection1', name='collection1', type=TrackType.COLLECTION, total_length=500.0, fill_factor=0.75
    )
    retrofit_track = Track(
        id='retrofit1', name='retrofit1', type=TrackType.RETROFIT, total_length=500.0, fill_factor=0.75
    )
    parking_track = Track(id='parking1', name='parking1', type=TrackType.PARKING, total_length=500.0, fill_factor=0.75)

    def get_track(track_id: str) -> Track | None:
        tracks = {'collection1': collection_track, 'retrofit1': retrofit_track, 'parking1': parking_track}
        return tracks.get(track_id)

    railway_context.get_track.side_effect = get_track

    # Create wagons
    wagons = []
    for i in range(4):
        wagon = Mock()
        wagon.id = f'W{i:03d}'
        wagon.length = 20.0
        wagons.append(wagon)

    # Mock yard context
    yard_context = Mock()
    yard_context.all_wagons = wagons

    infra = Mock()
    infra.contexts.get.return_value = yard_context
    railway_context._infra = infra

    # Create event handler
    handler = TrackOccupancyEventHandler(railway_context)

    # Test 1: Add wagons to collection track
    for wagon in wagons:
        event = WagonMovedEvent(
            wagon_id=wagon.id, from_track=None, to_track='collection1', timestamp=0.0, movement_type='classification'
        )
        handler.handle_wagon_moved(event)

    collection_occupancy = repo.get('collection1')
    assert collection_occupancy is not None
    assert len(collection_occupancy.get_occupants()) == 4
    assert collection_occupancy.get_current_occupancy_meters() == 80.0

    # Test 2: Move wagons from collection to retrofit
    for wagon in wagons:
        event = WagonMovedEvent(
            wagon_id=wagon.id, from_track='collection1', to_track='retrofit1', timestamp=100.0, movement_type='shunting'
        )
        handler.handle_wagon_moved(event)

    # Collection should be empty
    collection_occupancy = repo.get('collection1')
    assert len(collection_occupancy.get_occupants()) == 0
    assert collection_occupancy.get_current_occupancy_meters() == 0.0

    # Retrofit should have all wagons
    retrofit_occupancy = repo.get('retrofit1')
    assert retrofit_occupancy is not None
    assert len(retrofit_occupancy.get_occupants()) == 4
    assert retrofit_occupancy.get_current_occupancy_meters() == 80.0

    # Test 3: Move wagons from retrofit to parking
    for wagon in wagons:
        event = WagonMovedEvent(
            wagon_id=wagon.id, from_track='retrofit1', to_track='parking1', timestamp=200.0, movement_type='shunting'
        )
        handler.handle_wagon_moved(event)

    # Retrofit should be empty
    retrofit_occupancy = repo.get('retrofit1')
    assert len(retrofit_occupancy.get_occupants()) == 0
    assert retrofit_occupancy.get_current_occupancy_meters() == 0.0

    # Parking should have all wagons
    parking_occupancy = repo.get('parking1')
    assert parking_occupancy is not None
    assert len(parking_occupancy.get_occupants()) == 4
    assert parking_occupancy.get_current_occupancy_meters() == 80.0


def test_track_capacity_enforcement() -> None:
    """Test that track capacity is properly enforced."""
    repo = TrackOccupancyRepository()
    railway_context = Mock()
    railway_context.get_occupancy_repository.return_value = repo

    # Create small track (100m * 0.75 = 75m capacity)
    small_track = Track(
        id='small_track', name='small_track', type=TrackType.COLLECTION, total_length=100.0, fill_factor=0.75
    )

    railway_context.get_track.return_value = small_track

    # Create 5 wagons (20m each = 100m total, exceeds 75m capacity)
    wagons = []
    for i in range(5):
        wagon = Mock()
        wagon.id = f'W{i:03d}'
        wagon.length = 20.0
        wagons.append(wagon)

    yard_context = Mock()
    yard_context.all_wagons = wagons

    infra = Mock()
    infra.contexts.get.return_value = yard_context
    railway_context._infra = infra

    handler = TrackOccupancyEventHandler(railway_context)

    # Try to add all 5 wagons
    for wagon in wagons:
        event = WagonMovedEvent(
            wagon_id=wagon.id, from_track=None, to_track='small_track', timestamp=0.0, movement_type='classification'
        )
        handler.handle_wagon_moved(event)

        occupancy = repo.get('small_track')

    # Should only fit 3 wagons (60m) in 75m capacity
    occupancy = repo.get('small_track')
    assert occupancy is not None
    assert len(occupancy.get_occupants()) == 3
    assert occupancy.get_current_occupancy_meters() == 60.0


def test_wagon_removal_from_nonexistent_track() -> None:
    """Test that removing wagon from track where it doesn't exist doesn't crash."""
    repo = TrackOccupancyRepository()
    railway_context = Mock()
    railway_context.get_occupancy_repository.return_value = repo

    track = Track(id='test_track', name='test_track', type=TrackType.COLLECTION, total_length=500.0, fill_factor=0.75)

    railway_context.get_track.return_value = track

    wagon = Mock()
    wagon.id = 'W001'
    wagon.length = 20.0

    yard_context = Mock()
    yard_context.all_wagons = [wagon]

    infra = Mock()
    infra.contexts.get.return_value = yard_context
    railway_context._infra = infra

    handler = TrackOccupancyEventHandler(railway_context)

    # Try to move wagon from track where it doesn't exist (should not crash)
    event = WagonMovedEvent(
        wagon_id='W001', from_track='nonexistent_track', to_track='test_track', timestamp=0.0, movement_type='shunting'
    )

    # Should not raise exception
    handler.handle_wagon_moved(event)

    # Wagon should be added to destination track
    occupancy = repo.get('test_track')
    assert occupancy is not None
    assert len(occupancy.get_occupants()) == 1
