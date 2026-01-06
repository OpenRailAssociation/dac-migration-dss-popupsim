"""Tests for Track entity."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
import pytest


def test_track_creation() -> None:
    """Test basic track creation."""
    track_id = uuid4()
    track = Track(track_id, 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    assert track.id == track_id
    assert track.name == 'Collection 1'
    assert track.type == TrackType.COLLECTION
    assert track.total_length == 100.0
    assert track.fill_factor == 0.75


def test_track_capacity_calculation() -> None:
    """Test capacity calculation with fill factor."""
    track = Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=100.0, fill_factor=0.75)
    assert track.capacity == 75.0


def test_track_custom_fill_factor() -> None:
    """Test track with custom fill factor."""
    track = Track(uuid4(), 'Retrofit 1', TrackType.RETROFIT, total_length=200.0, fill_factor=0.9)
    assert track.capacity == 180.0


def test_track_immutability() -> None:
    """Test that track is immutable (frozen dataclass)."""
    track = Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    with pytest.raises(AttributeError):
        track.total_length = 200.0  # type: ignore[misc]


def test_track_hashable() -> None:
    """Test that track can be used in sets and dicts."""
    track1 = Track(uuid4(), 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    track2 = Track(uuid4(), 'Retrofit 1', TrackType.RETROFIT, total_length=150.0)
    track_set = {track1, track2}
    assert len(track_set) == 2


def test_track_equality() -> None:
    """Test track equality based on id."""
    track_id = uuid4()
    track1 = Track(track_id, 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    track2 = Track(track_id, 'Collection 1', TrackType.COLLECTION, total_length=100.0)
    assert track1 == track2


def test_track_types() -> None:
    """Test all track types can be created."""
    track_id = uuid4()
    for track_type in TrackType:
        track = Track(track_id, f'Track {track_type.value}', track_type, total_length=100.0)
        assert track.type == track_type
