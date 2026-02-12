"""Unit tests for RakeLifecycleManager domain service."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.coupling_service import CouplingService
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeFormationContext
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeLifecycleManager
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


@pytest.fixture
def coupling_service() -> CouplingService:
    """Create mock coupling service."""
    mock_service = Mock(spec=CouplingService)
    mock_service.get_rake_coupling_time.return_value = 10.0  # 10 minutes in ticks
    mock_service.get_rake_decoupling_time.return_value = 6.0  # 6 minutes in ticks
    return mock_service


@pytest.fixture
def rake_manager(coupling_service: CouplingService) -> RakeLifecycleManager:
    """Create rake lifecycle manager."""
    return RakeLifecycleManager(coupling_service)


@pytest.fixture
def screw_wagons() -> list[Wagon]:
    """Create wagons with SCREW couplers."""
    return [
        Wagon(
            id=f'W{i:03d}',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )
        for i in range(1, 4)
    ]


def test_form_rake_success(rake_manager: RakeLifecycleManager, screw_wagons: list[Wagon]) -> None:
    """Test successful rake formation."""
    context = RakeFormationContext(
        formation_track='collection', target_track='retrofit', rake_type=RakeType.WORKSHOP_RAKE, formation_time=0.0
    )

    result = rake_manager.form_rake(screw_wagons, context)

    assert result.success
    assert result.rake is not None
    assert result.rake.wagon_count == 3
    assert result.formation_duration == timedelta(minutes=10)  # From mock: 10 ticks = 10 min


def test_form_rake_empty_wagons(rake_manager: RakeLifecycleManager) -> None:
    """Test rake formation with empty wagon list."""
    context = RakeFormationContext(
        formation_track='collection', target_track='retrofit', rake_type=RakeType.WORKSHOP_RAKE, formation_time=0.0
    )

    result = rake_manager.form_rake([], context)

    assert not result.success
    assert result.rake is None
    assert 'no wagons' in result.error_message


def test_dissolve_rake(rake_manager: RakeLifecycleManager, screw_wagons: list[Wagon]) -> None:
    """Test rake dissolution."""
    # First form a rake
    context = RakeFormationContext(
        formation_track='collection', target_track='retrofit', rake_type=RakeType.WORKSHOP_RAKE, formation_time=0.0
    )
    formation_result = rake_manager.form_rake(screw_wagons, context)

    # Then dissolve it
    dissolution_result = rake_manager.dissolve_rake(formation_result.rake, screw_wagons)

    assert dissolution_result.success
    assert len(dissolution_result.wagons) == 3
    assert dissolution_result.dissolution_duration == timedelta(minutes=6)  # From mock: 6 ticks = 6 min


def test_validate_rake_formation_success(rake_manager: RakeLifecycleManager, screw_wagons: list[Wagon]) -> None:
    """Test successful rake formation validation."""
    result = rake_manager.validate_rake_formation(screw_wagons)

    assert result.is_valid
    assert result.error_message is None


def test_validate_rake_formation_empty(rake_manager: RakeLifecycleManager) -> None:
    """Test rake formation validation with empty list."""
    result = rake_manager.validate_rake_formation([])

    assert not result.is_valid
    assert 'empty wagon list' in result.error_message


def test_calculate_formation_time_single_wagon(rake_manager: RakeLifecycleManager, screw_wagons: list[Wagon]) -> None:
    """Test formation time calculation for single wagon."""
    single_wagon = screw_wagons[:1]

    # Mock should return 0 for single wagon
    rake_manager._coupling_service.get_rake_coupling_time.return_value = 0.0

    duration = rake_manager.calculate_formation_time(single_wagon)

    assert duration == timedelta(0)


def test_calculate_formation_time_multiple_wagons(
    rake_manager: RakeLifecycleManager, screw_wagons: list[Wagon]
) -> None:
    """Test formation time calculation for multiple wagons."""
    duration = rake_manager.calculate_formation_time(screw_wagons)

    # From mock: 10 ticks = 10 minutes
    assert duration == timedelta(minutes=10)


def test_calculate_dissolution_time(rake_manager: RakeLifecycleManager, screw_wagons: list[Wagon]) -> None:
    """Test dissolution time calculation."""
    duration = rake_manager.calculate_dissolution_time(screw_wagons)

    # From mock: 6 ticks = 6 minutes
    assert duration == timedelta(minutes=6)
