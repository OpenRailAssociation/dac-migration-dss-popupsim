"""Unit tests for RailwayYard aggregate."""

from uuid import uuid4

from contexts.railway_infrastructure.domain.aggregates.railway_yard import RailwayYard
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.exceptions import InsufficientCapacityError
from contexts.railway_infrastructure.domain.exceptions import TrackNotFoundError
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy
import pytest


class TestRailwayYard:
    """Test cases for RailwayYard aggregate."""

    def test_initialization(self) -> None:
        """Test RailwayYard initialization."""
        yard = RailwayYard("test_yard")
        
        assert yard.yard_id == "test_yard"
        assert len(yard._tracks) == 0
        assert len(yard._occupancy) == 0
        assert len(yard._track_groups) == 0

    def test_add_track(self) -> None:
        """Test adding tracks to yard."""
        yard = RailwayYard("test_yard")
        track = Track(
            id=uuid4(),
            name="track_1",
            type=TrackType.COLLECTION,
            total_length=100.0,
            fill_factor=0.8
        )
        
        yard.add_track(track)
        
        assert "track_1" in yard._tracks
        assert yard._tracks["track_1"] == track
        assert yard._occupancy["track_1"] == 0.0

    def test_create_track_group(self) -> None:
        """Test creating track groups."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        track2 = Track(uuid4(), "track_2", TrackType.COLLECTION, 150.0)
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1", "track_2"])
        
        assert TrackType.COLLECTION in yard._track_groups
        group = yard._track_groups[TrackType.COLLECTION]
        assert group.track_type == TrackType.COLLECTION
        assert set(group.track_ids) == {"track_1", "track_2"}

    def test_create_track_group_with_nonexistent_track(self) -> None:
        """Test creating track group with nonexistent track raises error."""
        yard = RailwayYard("test_yard")
        
        with pytest.raises(TrackNotFoundError):
            yard.create_track_group(TrackType.COLLECTION, ["nonexistent_track"])

    def test_can_track_accommodate_basic(self) -> None:
        """Test basic track accommodation check."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)  # 80m capacity
        yard.add_track(track)
        
        assert yard.can_track_accommodate("track_1", 50.0) is True
        assert yard.can_track_accommodate("track_1", 90.0) is False
        assert yard.can_track_accommodate("nonexistent", 10.0) is False

    def test_can_track_accommodate_workshop_wagon_limit(self) -> None:
        """Test workshop track wagon count limit."""
        yard = RailwayYard("test_yard")
        workshop_track = Track(
            uuid4(), "workshop_1", TrackType.WORKSHOP, 
            total_length=200.0, fill_factor=0.8, max_wagons=3
        )
        yard.add_track(workshop_track)
        
        # Add 3 wagons (at limit)
        yard.add_wagon_to_track("workshop_1", 20.0)
        yard.add_wagon_to_track("workshop_1", 20.0)
        yard.add_wagon_to_track("workshop_1", 20.0)
        
        # Should not accommodate 4th wagon due to count limit
        assert yard.can_track_accommodate("workshop_1", 20.0) is False

    def test_add_wagon_to_track(self) -> None:
        """Test adding wagons to tracks."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)
        yard.add_track(track)
        
        yard.add_wagon_to_track("track_1", 30.0)
        assert yard._occupancy["track_1"] == 30.0
        
        yard.add_wagon_to_track("track_1", 20.0)
        assert yard._occupancy["track_1"] == 50.0

    def test_add_wagon_insufficient_capacity(self) -> None:
        """Test adding wagon when insufficient capacity."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)  # 80m capacity
        yard.add_track(track)
        
        with pytest.raises(InsufficientCapacityError):
            yard.add_wagon_to_track("track_1", 90.0)

    def test_remove_wagon_from_track(self) -> None:
        """Test removing wagons from tracks."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        yard.add_track(track)
        
        yard.add_wagon_to_track("track_1", 50.0)
        yard.remove_wagon_from_track("track_1", 20.0)
        
        assert yard._occupancy["track_1"] == 30.0

    def test_remove_wagon_nonexistent_track(self) -> None:
        """Test removing wagon from nonexistent track."""
        yard = RailwayYard("test_yard")
        
        with pytest.raises(TrackNotFoundError):
            yard.remove_wagon_from_track("nonexistent", 10.0)

    def test_select_track_for_type_least_occupied(self) -> None:
        """Test track selection with least occupied strategy."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        track2 = Track(uuid4(), "track_2", TrackType.COLLECTION, 100.0)
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1", "track_2"], TrackSelectionStrategy.LEAST_OCCUPIED)
        
        # Add some occupancy to track_1
        yard.add_wagon_to_track("track_1", 30.0)
        
        # Should select track_2 (less occupied)
        selected = yard.select_track_for_type(TrackType.COLLECTION, 20.0)
        assert selected == "track_2"

    def test_select_track_for_type_first_available(self) -> None:
        """Test track selection with first available strategy."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        track2 = Track(uuid4(), "track_2", TrackType.COLLECTION, 100.0)
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1", "track_2"], TrackSelectionStrategy.FIRST_AVAILABLE)
        
        selected = yard.select_track_for_type(TrackType.COLLECTION, 20.0)
        assert selected == "track_1"  # First in list

    def test_add_wagon_to_group(self) -> None:
        """Test adding wagon to group using selection strategy."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        track2 = Track(uuid4(), "track_2", TrackType.COLLECTION, 100.0)
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1", "track_2"])
        
        selected_track, success = yard.add_wagon_to_group(TrackType.COLLECTION, 30.0)
        
        assert success is True
        assert selected_track in ["track_1", "track_2"]
        assert yard._occupancy[selected_track] == 30.0

    def test_add_wagon_to_group_no_capacity(self) -> None:
        """Test adding wagon to group when no tracks have capacity."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 50.0, fill_factor=1.0)  # 50m capacity
        
        yard.add_track(track)
        yard.create_track_group(TrackType.COLLECTION, ["track_1"])
        
        # Fill track to capacity
        yard.add_wagon_to_track("track_1", 50.0)
        
        selected_track, success = yard.add_wagon_to_group(TrackType.COLLECTION, 10.0)
        
        assert success is False
        assert selected_track is None

    def test_remove_wagon_from_group(self) -> None:
        """Test removing wagon from group (most occupied track)."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        track2 = Track(uuid4(), "track_2", TrackType.COLLECTION, 100.0)
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1", "track_2"])
        
        # Add different amounts to tracks
        yard.add_wagon_to_track("track_1", 50.0)
        yard.add_wagon_to_track("track_2", 30.0)
        
        success = yard.remove_wagon_from_group(TrackType.COLLECTION, 20.0)
        
        assert success is True
        # Should remove from track_1 (most occupied)
        assert yard._occupancy["track_1"] == 30.0
        assert yard._occupancy["track_2"] == 30.0

    def test_get_track_capacity(self) -> None:
        """Test getting track capacity."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)
        yard.add_track(track)
        
        assert yard.get_track_capacity("track_1") == 80.0
        assert yard.get_track_capacity("nonexistent") == 0.0

    def test_get_available_capacity(self) -> None:
        """Test getting available capacity."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)
        yard.add_track(track)
        
        yard.add_wagon_to_track("track_1", 30.0)
        
        assert yard.get_available_capacity("track_1") == 50.0  # 80 - 30
        assert yard.get_available_capacity("nonexistent") == 0.0

    def test_get_track_utilization(self) -> None:
        """Test getting track utilization percentage."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)  # 80m capacity
        yard.add_track(track)
        
        yard.add_wagon_to_track("track_1", 40.0)
        
        assert yard.get_track_utilization("track_1") == 50.0  # 40/80 * 100

    def test_get_tracks_by_type(self) -> None:
        """Test getting tracks by type."""
        yard = RailwayYard("test_yard")
        collection_track = Track(uuid4(), "collection_1", TrackType.COLLECTION, 100.0)
        workshop_track = Track(uuid4(), "workshop_1", TrackType.WORKSHOP, 150.0)
        
        yard.add_track(collection_track)
        yard.add_track(workshop_track)
        
        collection_tracks = yard.get_tracks_by_type(TrackType.COLLECTION)
        workshop_tracks = yard.get_tracks_by_type(TrackType.WORKSHOP)
        
        assert len(collection_tracks) == 1
        assert collection_tracks[0] == collection_track
        assert len(workshop_tracks) == 1
        assert workshop_tracks[0] == workshop_track

    def test_get_group_metrics(self) -> None:
        """Test getting group metrics."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)  # 80m
        track2 = Track(uuid4(), "track_2", TrackType.COLLECTION, 150.0, fill_factor=0.8)  # 120m
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1", "track_2"])
        
        # Add some occupancy
        yard.add_wagon_to_track("track_1", 40.0)
        yard.add_wagon_to_track("track_2", 60.0)
        
        metrics = yard.get_group_metrics(TrackType.COLLECTION)
        
        assert metrics['track_count'] == 2
        assert metrics['total_capacity'] == 200.0  # 80 + 120
        assert metrics['total_occupancy'] == 100.0  # 40 + 60
        assert metrics['utilization_percent'] == 50.0  # 100/200 * 100

    def test_get_yard_metrics(self) -> None:
        """Test getting overall yard metrics."""
        yard = RailwayYard("test_yard")
        track1 = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0, fill_factor=0.8)
        track2 = Track(uuid4(), "track_2", TrackType.WORKSHOP, 150.0, fill_factor=0.8)
        
        yard.add_track(track1)
        yard.add_track(track2)
        yard.create_track_group(TrackType.COLLECTION, ["track_1"])
        yard.create_track_group(TrackType.WORKSHOP, ["track_2"])
        
        yard.add_wagon_to_track("track_1", 40.0)
        
        metrics = yard.get_yard_metrics()
        
        assert metrics['yard_id'] == "test_yard"
        assert metrics['total_tracks'] == 2
        assert metrics['total_capacity'] == 200.0  # 80 + 120
        assert metrics['total_occupancy'] == 40.0
        assert metrics['utilization_percent'] == 20.0  # 40/200 * 100
        assert 'collection_group' in metrics['track_groups']
        assert 'workshop_area_group' in metrics['track_groups']

    def test_set_selection_strategy(self) -> None:
        """Test setting selection strategy for track type."""
        yard = RailwayYard("test_yard")
        track = Track(uuid4(), "track_1", TrackType.COLLECTION, 100.0)
        
        yard.add_track(track)
        yard.create_track_group(TrackType.COLLECTION, ["track_1"], TrackSelectionStrategy.FIRST_AVAILABLE)
        
        # Change strategy
        yard.set_selection_strategy(TrackType.COLLECTION, TrackSelectionStrategy.RANDOM)
        
        group = yard._track_groups[TrackType.COLLECTION]
        assert group.selection_strategy == TrackSelectionStrategy.RANDOM