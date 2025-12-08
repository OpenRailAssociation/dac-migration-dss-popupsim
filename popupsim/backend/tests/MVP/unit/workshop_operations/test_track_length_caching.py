"""Unit tests for track length caching (Issue #9)."""

import pytest

from popupsim.backend.src.MVP.workshop_operations.domain.entities.track import (
    Track,
    TrackType,
)


def test_track_length_initially_none() -> None:
    """Test that track length is initially None."""
    track = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1", "e2"])

    assert track.get_total_length() is None


def test_track_length_can_be_set() -> None:
    """Test that track length can be set."""
    track = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1", "e2"])

    track.set_total_length(100.0)

    assert track.get_total_length() == 100.0


def test_track_length_persists() -> None:
    """Test that cached track length persists."""
    track = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1", "e2"])

    track.set_total_length(150.5)

    # Multiple calls return same value
    assert track.get_total_length() == 150.5
    assert track.get_total_length() == 150.5


def test_track_length_can_be_updated() -> None:
    """Test that track length can be updated."""
    track = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1", "e2"])

    track.set_total_length(100.0)
    assert track.get_total_length() == 100.0

    # Update value
    track.set_total_length(200.0)
    assert track.get_total_length() == 200.0


def test_track_length_zero_is_valid() -> None:
    """Test that zero length is a valid cached value."""
    track = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])

    track.set_total_length(0.0)

    assert track.get_total_length() == 0.0
    assert track.get_total_length() is not None  # Distinguish from uncached


def test_track_length_negative_is_allowed() -> None:
    """Test that negative length can be set (validation elsewhere)."""
    track = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])

    # Caching doesn't validate, just stores
    track.set_total_length(-10.0)

    assert track.get_total_length() == -10.0


def test_track_length_different_tracks_independent() -> None:
    """Test that different tracks have independent caches."""
    track1 = Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])
    track2 = Track(id="track_2", type=TrackType.RETROFIT, edges=["e2"])

    track1.set_total_length(100.0)
    track2.set_total_length(200.0)

    assert track1.get_total_length() == 100.0
    assert track2.get_total_length() == 200.0


def test_track_length_with_multiple_edges() -> None:
    """Test caching with track having multiple edges."""
    track = Track(
        id="track_1", type=TrackType.COLLECTION, edges=["e1", "e2", "e3", "e4"]
    )

    # Simulate sum of edge lengths
    total = 10.0 + 20.0 + 15.0 + 25.0  # 70.0
    track.set_total_length(total)

    assert track.get_total_length() == 70.0


def test_track_length_with_single_edge() -> None:
    """Test caching with track having single edge."""
    track = Track(id="track_1", type=TrackType.PARKING, edges=["e1"])

    track.set_total_length(50.0)

    assert track.get_total_length() == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
