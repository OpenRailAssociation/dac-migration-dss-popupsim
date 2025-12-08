"""Tests for Yard aggregate and related components."""

from popupsim.backend.src.MVP.workshop_operations.domain.entities.track import (
    Track,
    TrackType,
)
from popupsim.backend.src.MVP.yard_operations.domain.aggregates.yard import Yard
from popupsim.backend.src.MVP.yard_operations.domain.entities.yard_area import (
    AreaType,
    YardArea,
)
from popupsim.backend.src.MVP.yard_operations.domain.services.yard_coordinator import (
    YardCoordinator,
)


def test_yard_creation() -> None:
    """Test creating a yard with areas."""
    yard = Yard(yard_id="yard_1", name="Main Yard")

    assert yard.yard_id == "yard_1"
    assert yard.name == "Main Yard"
    assert yard.get_total_areas() == 0


def test_yard_add_area() -> None:
    """Test adding areas to yard."""
    yard = Yard(yard_id="yard_1", name="Main Yard")
    tracks = [Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])]
    area = YardArea(
        area_id="classification_1", area_type=AreaType.CLASSIFICATION, tracks=tracks
    )

    yard.add_area("classification_1", area)

    assert yard.get_total_areas() == 1
    assert yard.get_area("classification_1") == area


def test_yard_get_areas_by_type() -> None:
    """Test retrieving areas by type."""
    yard = Yard(yard_id="yard_1", name="Main Yard")

    classification_area = YardArea(
        area_id="classification_1",
        area_type=AreaType.CLASSIFICATION,
        tracks=[Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])],
    )
    parking_area = YardArea(
        area_id="parking_1",
        area_type=AreaType.PARKING,
        tracks=[Track(id="track_2", type=TrackType.PARKING, edges=["e2"])],
    )

    yard.add_area("classification_1", classification_area)
    yard.add_area("parking_1", parking_area)

    classification_areas = yard.get_areas_by_type(AreaType.CLASSIFICATION)
    parking_areas = yard.get_areas_by_type(AreaType.PARKING)

    assert len(classification_areas) == 1
    assert len(parking_areas) == 1
    assert classification_areas[0] == classification_area
    assert parking_areas[0] == parking_area


def test_yard_has_area_type() -> None:
    """Test checking if yard has specific area type."""
    yard = Yard(yard_id="yard_1", name="Main Yard")
    area = YardArea(
        area_id="classification_1",
        area_type=AreaType.CLASSIFICATION,
        tracks=[Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])],
    )

    yard.add_area("classification_1", area)

    assert yard.has_area_type(AreaType.CLASSIFICATION)
    assert not yard.has_area_type(AreaType.PARKING)


def test_yard_area_get_track_ids() -> None:
    """Test getting track IDs from area."""
    tracks = [
        Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"]),
        Track(id="track_2", type=TrackType.COLLECTION, edges=["e2"]),
    ]
    area = YardArea(
        area_id="classification_1", area_type=AreaType.CLASSIFICATION, tracks=tracks
    )

    track_ids = area.get_track_ids()

    assert len(track_ids) == 2
    assert "track_1" in track_ids
    assert "track_2" in track_ids


def test_yard_area_has_capacity() -> None:
    """Test checking area capacity."""
    area_with_tracks = YardArea(
        area_id="area_1",
        area_type=AreaType.CLASSIFICATION,
        tracks=[Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])],
    )
    area_without_tracks = YardArea(
        area_id="area_2", area_type=AreaType.PARKING, tracks=[]
    )

    assert area_with_tracks.has_capacity()
    assert not area_without_tracks.has_capacity()


def test_yard_coordinator_get_areas() -> None:
    """Test yard coordinator getting areas."""
    yard = Yard(yard_id="yard_1", name="Main Yard")
    classification_area = YardArea(
        area_id="classification_1",
        area_type=AreaType.CLASSIFICATION,
        tracks=[Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])],
    )
    parking_area = YardArea(
        area_id="parking_1",
        area_type=AreaType.PARKING,
        tracks=[Track(id="track_2", type=TrackType.PARKING, edges=["e2"])],
    )

    yard.add_area("classification_1", classification_area)
    yard.add_area("parking_1", parking_area)

    coordinator = YardCoordinator(yard)

    assert coordinator.get_classification_area() == classification_area
    assert coordinator.get_parking_area() == parking_area


def test_yard_coordinator_has_capacity() -> None:
    """Test yard coordinator checking capacity."""
    yard = Yard(yard_id="yard_1", name="Main Yard")
    area = YardArea(
        area_id="classification_1",
        area_type=AreaType.CLASSIFICATION,
        tracks=[Track(id="track_1", type=TrackType.COLLECTION, edges=["e1"])],
    )

    yard.add_area("classification_1", area)
    coordinator = YardCoordinator(yard)

    assert coordinator.has_capacity_for_wagon(AreaType.CLASSIFICATION)
    assert not coordinator.has_capacity_for_wagon(AreaType.PARKING)
