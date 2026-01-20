"""Unit tests for wagon movement events."""

from shared.domain.events.wagon_movement_events import WagonMovedEvent


def test_wagon_moved_event_creation() -> None:
    """Test WagonMovedEvent can be created with required fields."""
    event = WagonMovedEvent(
        wagon_id='W001',
        from_track='collection_1',
        to_track='retrofit_1',
        timestamp=100.0,
        movement_type='shunting',
    )

    assert event.wagon_id == 'W001'
    assert event.from_track == 'collection_1'
    assert event.to_track == 'retrofit_1'
    assert event.timestamp == 100.0
    assert event.movement_type == 'shunting'


def test_wagon_moved_event_without_from_track() -> None:
    """Test WagonMovedEvent can be created without from_track."""
    event = WagonMovedEvent(
        wagon_id='W001',
        from_track=None,
        to_track='retrofit_1',
        timestamp=100.0,
    )

    assert event.wagon_id == 'W001'
    assert event.from_track is None
    assert event.to_track == 'retrofit_1'
