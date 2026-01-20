"""Unit tests for track occupancy event handler."""

from unittest.mock import Mock

from contexts.railway_infrastructure.application.track_occupancy_event_handler import TrackOccupancyEventHandler
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from shared.domain.events.wagon_movement_events import WagonMovedEvent


def test_handle_wagon_moved_adds_to_destination() -> None:
    """Test handler adds wagon to destination track."""
    repo = TrackOccupancyRepository()
    railway_context = Mock()
    railway_context.get_occupancy_repository.return_value = repo

    dest_track = Track(id='retrofit_1', name='retrofit_1', type=TrackType.RETROFIT, total_length=100.0, fill_factor=0.8)
    railway_context.get_track.return_value = dest_track

    wagon = Mock()
    wagon.id = 'W001'
    wagon.length = 20.0

    yard_context = Mock()
    yard_context.all_wagons = [wagon]

    infra = Mock()
    infra.contexts.get.return_value = yard_context
    railway_context._infra = infra

    handler = TrackOccupancyEventHandler(railway_context)

    event = WagonMovedEvent(
        wagon_id='W001',
        from_track=None,
        to_track='retrofit_1',
        timestamp=100.0,
    )

    handler.handle_wagon_moved(event)

    occupancy = repo.get('retrofit_1')
    assert occupancy is not None
    assert len(occupancy.get_occupants()) == 1


def test_handle_wagon_moved_removes_from_source() -> None:
    """Test handler removes wagon from source track."""
    repo = TrackOccupancyRepository()
    railway_context = Mock()
    railway_context.get_occupancy_repository.return_value = repo

    source_track = Track(
        id='collection_1', name='collection_1', type=TrackType.COLLECTION, total_length=100.0, fill_factor=0.8
    )
    dest_track = Track(id='retrofit_1', name='retrofit_1', type=TrackType.RETROFIT, total_length=100.0, fill_factor=0.8)

    source_occupancy = repo.get_or_create(source_track)
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import OccupantType
    from contexts.railway_infrastructure.domain.value_objects.track_occupant import TrackOccupant

    occupant = TrackOccupant(id='W001', type=OccupantType.WAGON, length=20.0, position_start=0.0)
    source_occupancy.add_occupant(occupant, 50.0)

    railway_context.get_track.return_value = dest_track

    wagon = Mock()
    wagon.id = 'W001'
    wagon.length = 20.0

    yard_context = Mock()
    yard_context.all_wagons = [wagon]

    infra = Mock()
    infra.contexts.get.return_value = yard_context
    railway_context._infra = infra

    handler = TrackOccupancyEventHandler(railway_context)

    event = WagonMovedEvent(
        wagon_id='W001',
        from_track='collection_1',
        to_track='retrofit_1',
        timestamp=100.0,
    )

    handler.handle_wagon_moved(event)

    source_occupancy = repo.get('collection_1')
    assert len(source_occupancy.get_occupants()) == 0
