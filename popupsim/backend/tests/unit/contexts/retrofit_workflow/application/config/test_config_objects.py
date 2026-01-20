"""Tests for configuration objects."""

from contexts.retrofit_workflow.application.config.coordinator_config import CoordinatorConfig
from contexts.retrofit_workflow.application.config.publisher_config import PublisherConfig
from contexts.retrofit_workflow.application.config.queue_config import QueueConfig
from contexts.retrofit_workflow.application.config.service_config import ServiceConfig
from contexts.retrofit_workflow.application.services.coordination_service import CoordinationService
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
import pytest
import simpy


class MockLocomotiveManager:
    """Mock locomotive manager for testing."""

    pass


class MockTrackSelector:
    """Mock track selector for testing."""

    pass


class MockRouteService:
    """Mock route service for testing."""

    pass


@pytest.fixture
def env() -> simpy.Environment:
    """Create SimPy environment for testing."""
    return simpy.Environment()


@pytest.fixture
def queue_config(env: simpy.Environment) -> QueueConfig:
    """Create queue configuration for testing."""
    return QueueConfig(
        collection_queue=simpy.FilterStore(env),
        retrofit_queue=simpy.FilterStore(env),
        retrofitted_queue=simpy.FilterStore(env),
    )


@pytest.fixture
def service_config() -> ServiceConfig:
    """Create service configuration for testing."""
    return ServiceConfig(
        batch_service=BatchFormationService(),
        route_service=MockRouteService(),
        coordination_service=CoordinationService(),
    )


@pytest.fixture
def publisher_config() -> PublisherConfig:
    """Create publisher configuration for testing."""
    return PublisherConfig()


def test_queue_config_sizes(queue_config: QueueConfig) -> None:
    """Test queue size reporting."""
    # Initially empty
    sizes = queue_config.get_queue_sizes()
    assert sizes['collection'] == 0
    assert sizes['retrofit'] == 0
    assert sizes['retrofitted'] == 0
    assert queue_config.get_total_wagons() == 0

    # Add items to queues
    queue_config.collection_queue.put('item1')
    queue_config.retrofit_queue.put('item2')
    queue_config.retrofitted_queue.put('item3')

    sizes = queue_config.get_queue_sizes()
    assert sizes['collection'] == 1
    assert sizes['retrofit'] == 1
    assert sizes['retrofitted'] == 1
    assert queue_config.get_total_wagons() == 3


def test_service_config_validation(service_config: ServiceConfig) -> None:
    """Test service configuration validation."""
    # Valid config should not raise
    service_config.validate()

    # Invalid configs should raise
    invalid_config = ServiceConfig(
        batch_service=None,
        route_service=MockRouteService(),
        coordination_service=CoordinationService(),
    )

    with pytest.raises(ValueError, match='BatchFormationService is required'):
        invalid_config.validate()


def test_publisher_config_functionality() -> None:
    """Test publisher configuration functionality."""
    events = []

    def mock_publisher(event):
        events.append(event)

    config = PublisherConfig(
        wagon_event_publisher=mock_publisher,
        locomotive_event_publisher=None,
        batch_event_publisher=mock_publisher,
    )

    # Test publisher checks
    assert config.has_wagon_publisher() is True
    assert config.has_locomotive_publisher() is False
    assert config.has_batch_publisher() is True

    # Test event publishing
    config.publish_wagon_event('wagon_event')
    config.publish_locomotive_event('loco_event')  # Should be ignored
    config.publish_batch_event('batch_event')

    assert events == ['wagon_event', 'batch_event']


def test_coordinator_config_validation(
    env: simpy.Environment,
    queue_config: QueueConfig,
    service_config: ServiceConfig,
    publisher_config: PublisherConfig,
) -> None:
    """Test coordinator configuration validation."""
    config = CoordinatorConfig(
        env=env,
        queues=queue_config,
        services=service_config,
        publishers=publisher_config,
        locomotive_manager=MockLocomotiveManager(),
        track_selector=MockTrackSelector(),
        scenario={'test': 'scenario'},
    )

    # Valid config should not raise
    config.validate()

    # Test current time property
    assert config.current_time == env.now

    # Invalid config should raise
    invalid_config = CoordinatorConfig(
        env=None,
        queues=queue_config,
        services=service_config,
        publishers=publisher_config,
        locomotive_manager=MockLocomotiveManager(),
        track_selector=MockTrackSelector(),
        scenario={'test': 'scenario'},
    )

    with pytest.raises(ValueError, match='SimPy environment is required'):
        invalid_config.validate()
