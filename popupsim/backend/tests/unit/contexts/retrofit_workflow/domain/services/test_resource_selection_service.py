"""Tests for ResourceSelectionService with TrackCapacityManager."""

from contexts.retrofit_workflow.domain.services.resource_selection_service import ResourceSelectionService
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackCapacityManager
import pytest
from shared.domain.value_objects.selection_strategy import SelectionStrategy
import simpy


@pytest.fixture
def env() -> simpy.Environment:
    """Create SimPy environment."""
    return simpy.Environment()


@pytest.fixture
def tracks(env: simpy.Environment) -> dict[str, TrackCapacityManager]:
    """Create test track capacity managers."""
    return {
        'T1': TrackCapacityManager(env, 'T1', 100.0),
        'T2': TrackCapacityManager(env, 'T2', 100.0),
        'T3': TrackCapacityManager(env, 'T3', 100.0),
    }


def test_first_available(tracks: dict[str, TrackCapacityManager]) -> None:
    """Test FIRST_AVAILABLE returns first track with capacity."""
    service = ResourceSelectionService(tracks, SelectionStrategy.FIRST_AVAILABLE)
    selected_id = service.select()
    assert selected_id in tracks


def test_least_occupied(env: simpy.Environment, tracks: dict[str, TrackCapacityManager]) -> None:
    """Test LEAST_OCCUPIED returns track with most capacity."""

    def fill_track() -> simpy.events.Event:  # type: ignore[type-arg]
        yield tracks['T1'].container.put(50.0)

    env.process(fill_track())
    env.run()
    service = ResourceSelectionService(tracks, SelectionStrategy.LEAST_OCCUPIED)
    selected_id = service.select()
    assert selected_id in ['T2', 'T3']


def test_round_robin(tracks: dict[str, TrackCapacityManager]) -> None:
    """Test ROUND_ROBIN cycles through tracks."""
    service = ResourceSelectionService(tracks, SelectionStrategy.ROUND_ROBIN)
    selections = [service.select() for _ in range(6)]
    assert len(set(selections)) == 3  # All tracks used


def test_random(tracks: dict[str, TrackCapacityManager]) -> None:
    """Test RANDOM returns valid track."""
    service = ResourceSelectionService(tracks, SelectionStrategy.RANDOM)
    selected_id = service.select()
    assert selected_id in tracks


def test_no_capacity(env: simpy.Environment, tracks: dict[str, TrackCapacityManager]) -> None:
    """Test returns None when no tracks have capacity."""

    def fill_tracks() -> simpy.events.Event:  # type: ignore[type-arg]
        for track in tracks.values():
            yield track.container.put(track.capacity_meters)

    env.process(fill_tracks())
    env.run()
    service = ResourceSelectionService(tracks, SelectionStrategy.FIRST_AVAILABLE)
    assert service.select() is None


def test_empty_dict() -> None:
    """Test with empty resource dict."""
    service: ResourceSelectionService[TrackCapacityManager] = ResourceSelectionService(
        {}, SelectionStrategy.FIRST_AVAILABLE
    )
    assert service.select() is None
