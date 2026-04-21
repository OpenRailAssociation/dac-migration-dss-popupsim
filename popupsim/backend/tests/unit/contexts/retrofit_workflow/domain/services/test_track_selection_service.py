"""Tests for TrackSelectionFacade."""

from contexts.retrofit_workflow.domain.services.track_selection_service import TrackSelectionFacade
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackCapacityManager
import pytest
import simpy


@pytest.fixture
def env() -> simpy.Environment:
    """Create SimPy environment."""
    return simpy.Environment()


@pytest.fixture
def tracks_by_type(env: simpy.Environment) -> dict[str, list[TrackCapacityManager]]:
    """Create test tracks grouped by type."""
    return {
        'collection': [
            TrackCapacityManager(env, 'C1', 100.0),
            TrackCapacityManager(env, 'C2', 100.0),
        ],
        'retrofit': [
            TrackCapacityManager(env, 'R1', 150.0),
        ],
    }


def test_select_track_with_capacity(tracks_by_type: dict[str, list[TrackCapacityManager]]) -> None:
    """Test select_track_with_capacity returns track with capacity."""
    facade = TrackSelectionFacade(tracks_by_type)
    selected = facade.select_track_with_capacity('collection')
    assert selected is not None
    assert selected.track_id in ['C1', 'C2']


def test_select_single_track(tracks_by_type: dict[str, list[TrackCapacityManager]]) -> None:
    """Test selecting from single track type."""
    facade = TrackSelectionFacade(tracks_by_type)
    selected = facade.select_track_with_capacity('retrofit')
    assert selected is not None
    assert selected.track_id == 'R1'


def test_no_capacity(env: simpy.Environment, tracks_by_type: dict[str, list[TrackCapacityManager]]) -> None:
    """Test returns None when no capacity."""

    def fill_tracks() -> simpy.events.Event:  # type: ignore[type-arg]
        for track in tracks_by_type['collection']:
            yield track.container.put(track.capacity_meters)

    env.process(fill_tracks())
    env.run()
    facade = TrackSelectionFacade(tracks_by_type)
    assert facade.select_track_with_capacity('collection') is None


def test_get_total_available_capacity(tracks_by_type: dict[str, list[TrackCapacityManager]]) -> None:
    """Test total capacity calculation."""
    facade = TrackSelectionFacade(tracks_by_type)
    total = facade.get_total_available_capacity('collection')
    assert total == 200.0


def test_get_tracks_of_type(tracks_by_type: dict[str, list[TrackCapacityManager]]) -> None:
    """Test retrieving tracks by type."""
    facade = TrackSelectionFacade(tracks_by_type)
    tracks = facade.get_tracks_of_type('collection')
    assert len(tracks) == 2
