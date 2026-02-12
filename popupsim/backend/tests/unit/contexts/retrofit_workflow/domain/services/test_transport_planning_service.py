"""Unit tests for simplified TransportPlanningService domain service."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.configuration.application.dtos.route_input_dto import RouteType
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.services.route_service import RouteService
from contexts.retrofit_workflow.domain.services.transport_planning_service import TransportPlanningService
import pytest


@pytest.fixture
def route_service() -> RouteService:
    """Create mock route service."""
    mock_service = Mock(spec=RouteService)

    # Setup route durations (in simulation ticks = minutes)
    mock_service.get_duration.side_effect = lambda from_track, to_track: {
        ('collection', 'retrofit'): 5.0,
        ('retrofit', 'workshop_01'): 8.0,
        ('workshop_01', 'retrofitted'): 7.0,
        ('retrofitted', 'parking'): 10.0,
    }.get((from_track, to_track), 1.0)  # Default 1.0 minute

    # Setup route types
    mock_service.get_route_type.side_effect = lambda from_track, to_track: {
        ('collection', 'retrofit'): RouteType.SHUNTING,
        ('retrofit', 'workshop_01'): RouteType.SHUNTING,
        ('workshop_01', 'retrofitted'): RouteType.SHUNTING,
        ('retrofitted', 'parking'): RouteType.MAINLINE,
    }.get((from_track, to_track), RouteType.SHUNTING)

    return mock_service


@pytest.fixture
def transport_service(route_service: RouteService) -> TransportPlanningService:
    """Create transport planning service."""
    return TransportPlanningService(route_service)


@pytest.fixture
def sample_rake() -> Rake:
    """Create sample rake for testing."""
    return Rake(
        id='RAKE_001',
        wagon_ids=['W001', 'W002', 'W003'],
        rake_type=RakeType.WORKSHOP_RAKE,
        formation_track='collection',
        target_track='retrofit',
        formation_time=0.0,
    )


def test_plan_transport_success(transport_service: TransportPlanningService, sample_rake: Rake) -> None:
    """Test successful transport planning."""
    result = transport_service.plan_transport(sample_rake, 'collection', 'retrofit')

    assert result.success
    assert result.plan is not None
    assert result.plan.rake_id == 'RAKE_001'
    assert result.plan.from_track == 'collection'
    assert result.plan.to_track == 'retrofit'
    assert result.plan.transport_time == timedelta(minutes=5)
    assert result.plan.route_type == RouteType.SHUNTING


def test_plan_transport_null_rake(transport_service: TransportPlanningService) -> None:
    """Test transport planning with null rake."""
    result = transport_service.plan_transport(None, 'collection', 'retrofit')

    assert not result.success
    assert result.plan is None
    assert 'null rake' in result.error_message


def test_plan_transport_same_tracks(transport_service: TransportPlanningService, sample_rake: Rake) -> None:
    """Test transport planning with same source and destination."""
    result = transport_service.plan_transport(sample_rake, 'same_track', 'same_track')

    assert not result.success
    assert result.plan is None
    assert 'same' in result.error_message.lower()


def test_calculate_transport_time(transport_service: TransportPlanningService) -> None:
    """Test transport time calculation."""
    duration = transport_service.calculate_transport_time('collection', 'retrofit')

    assert duration == timedelta(minutes=5)


def test_get_route_type(transport_service: TransportPlanningService) -> None:
    """Test route type lookup."""
    route_type = transport_service.get_route_type('collection', 'retrofit')

    assert route_type == RouteType.SHUNTING


def test_get_route_type_mainline(transport_service: TransportPlanningService) -> None:
    """Test route type lookup for mainline route."""
    route_type = transport_service.get_route_type('retrofitted', 'parking')

    assert route_type == RouteType.MAINLINE
