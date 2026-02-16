"""Unit tests for RakeOperationsService."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.configuration.application.dtos.route_input_dto import RouteType
from contexts.retrofit_workflow.application.services.rake_operations_service import RakeOperation
from contexts.retrofit_workflow.application.services.rake_operations_service import RakeOperationResult
from contexts.retrofit_workflow.application.services.rake_operations_service import RakeOperationsService
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeDissolutionResult
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeFormationContext
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeFormationResult
from contexts.retrofit_workflow.domain.services.transport_planning_service import TransportPlan
from contexts.retrofit_workflow.domain.services.transport_planning_service import TransportPlanResult
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


class TestRakeOperationsService:
    """Test cases for RakeOperationsService."""

    @pytest.fixture
    def mock_rake_lifecycle(self) -> Mock:
        """Mock rake lifecycle manager."""
        return Mock()

    @pytest.fixture
    def mock_transport_planning(self) -> Mock:
        """Mock transport planning service."""
        return Mock()

    @pytest.fixture
    def service(self, mock_rake_lifecycle: Mock, mock_transport_planning: Mock) -> RakeOperationsService:
        """Create service with mocked dependencies."""
        return RakeOperationsService(mock_rake_lifecycle, mock_transport_planning)

    @pytest.fixture
    def sample_wagons(self) -> list[Wagon]:
        """Create sample wagons for testing."""
        return [
            Wagon(
                id='W1',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            ),
            Wagon(
                id='W2',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            ),
            Wagon(
                id='W3',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            ),
        ]

    @pytest.fixture
    def sample_rake(self) -> Rake:
        """Create sample rake for testing."""
        return Rake(
            id='RAKE_TEST_001',
            wagon_ids=['W1', 'W2', 'W3'],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='collection',
            target_track='retrofit',
            formation_time=100.0,
        )

    def test_create_formation_operation_success(
        self,
        service: RakeOperationsService,
        mock_rake_lifecycle: Mock,
        sample_wagons: list[Wagon],
        sample_rake: Rake,
    ) -> None:
        """Test successful rake formation operation."""
        # Arrange
        formation_result = RakeFormationResult(
            rake=sample_rake,
            success=True,
            error_message=None,
            formation_duration=timedelta(minutes=5),
        )
        mock_rake_lifecycle.form_rake.return_value = formation_result

        # Act
        context = RakeFormationContext(
            formation_track='collection',
            target_track='retrofit',
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_time=100.0,
        )
        result = service.create_formation_operation(
            wagons=sample_wagons,
            context=context,
        )

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.rake_id == 'RAKE_TEST_001'
        assert result.operation.formation_time == timedelta(minutes=5)
        assert result.operation.total_time == timedelta(minutes=5)
        assert result.completed_wagons == sample_wagons

    def test_create_formation_operation_empty_wagons(
        self,
        service: RakeOperationsService,
    ) -> None:
        """Test formation operation with empty wagon list."""
        # Act
        context = RakeFormationContext(
            formation_track='collection',
            target_track='retrofit',
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_time=100.0,
        )
        result = service.create_formation_operation(
            wagons=[],
            context=context,
        )

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'no wagons' in result.error_message
        assert result.operation is None
        assert result.completed_wagons == []

    def test_create_formation_operation_failure(
        self,
        service: RakeOperationsService,
        mock_rake_lifecycle: Mock,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test formation operation failure."""
        # Arrange
        formation_result = RakeFormationResult(
            rake=None,
            success=False,
            error_message='Incompatible coupler types',
            formation_duration=timedelta(0),
        )
        mock_rake_lifecycle.form_rake.return_value = formation_result

        # Act
        context = RakeFormationContext(
            formation_track='collection',
            target_track='retrofit',
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_time=100.0,
        )
        result = service.create_formation_operation(
            wagons=sample_wagons,
            context=context,
        )

        # Assert
        assert result.success is False
        assert result.error_message == 'Incompatible coupler types'
        assert result.operation is None
        assert result.completed_wagons == []

    def test_create_transport_operation_success(
        self,
        service: RakeOperationsService,
        mock_transport_planning: Mock,
        sample_rake: Rake,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test successful transport operation."""
        # Arrange
        transport_plan = TransportPlan(
            rake_id='RAKE_TEST_001',
            from_track='collection',
            to_track='retrofit',
            route_type=RouteType.SHUNTING,
            transport_time=timedelta(minutes=10),
        )
        transport_result = TransportPlanResult(
            plan=transport_plan,
            success=True,
            error_message=None,
        )
        mock_transport_planning.plan_transport.return_value = transport_result

        # Act
        result = service.create_transport_operation(
            rake=sample_rake,
            wagons=sample_wagons,
            from_track='collection',
            to_track='retrofit',
        )

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.transport_time == timedelta(minutes=10)
        assert result.operation.total_time == timedelta(minutes=10)
        assert result.completed_wagons == sample_wagons

    def test_create_transport_operation_failure(
        self,
        service: RakeOperationsService,
        mock_transport_planning: Mock,
        sample_rake: Rake,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test transport operation failure."""
        # Arrange
        transport_result = TransportPlanResult(
            plan=None,
            success=False,
            error_message='No route available',
        )
        mock_transport_planning.plan_transport.return_value = transport_result

        # Act
        result = service.create_transport_operation(
            rake=sample_rake,
            wagons=sample_wagons,
            from_track='collection',
            to_track='retrofit',
        )

        # Assert
        assert result.success is False
        assert result.error_message == 'No route available'
        assert result.operation is None
        assert result.completed_wagons == []

    def test_create_dissolution_operation_success(
        self,
        service: RakeOperationsService,
        mock_rake_lifecycle: Mock,
        sample_rake: Rake,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test successful dissolution operation."""
        # Arrange
        dissolution_result = RakeDissolutionResult(
            wagons=sample_wagons,
            success=True,
            dissolution_duration=timedelta(minutes=3),
        )
        mock_rake_lifecycle.dissolve_rake.return_value = dissolution_result

        # Act
        result = service.create_dissolution_operation(
            rake=sample_rake,
            wagons=sample_wagons,
        )

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.dissolution_time == timedelta(minutes=3)
        assert result.operation.total_time == timedelta(minutes=3)
        assert result.completed_wagons == sample_wagons

    def test_create_dissolution_operation_failure(
        self,
        service: RakeOperationsService,
        mock_rake_lifecycle: Mock,
        sample_rake: Rake,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test dissolution operation failure."""
        # Arrange
        dissolution_result = RakeDissolutionResult(
            wagons=[],
            success=False,
            dissolution_duration=timedelta(0),
        )
        mock_rake_lifecycle.dissolve_rake.return_value = dissolution_result

        # Act
        result = service.create_dissolution_operation(
            rake=sample_rake,
            wagons=sample_wagons,
        )

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'dissolution failed' in result.error_message
        assert result.operation is None
        assert result.completed_wagons == []

    def test_create_complete_operation_success(
        self,
        service: RakeOperationsService,
        mock_rake_lifecycle: Mock,
        mock_transport_planning: Mock,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test successful complete operation."""
        # Arrange
        mock_rake_lifecycle.calculate_formation_time.return_value = timedelta(minutes=5)
        mock_transport_planning.calculate_transport_time.return_value = timedelta(minutes=10)
        mock_rake_lifecycle.calculate_dissolution_time.return_value = timedelta(minutes=3)

        # Act
        result = service.create_complete_operation(
            wagons=sample_wagons,
            formation_track='collection',
            target_track='retrofit',
            rake_type=RakeType.WORKSHOP_RAKE,
        )

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.formation_time == timedelta(minutes=5)
        assert result.operation.transport_time == timedelta(minutes=10)
        assert result.operation.dissolution_time == timedelta(minutes=3)
        assert result.operation.total_time == timedelta(minutes=18)
        assert result.completed_wagons == sample_wagons

    def test_create_complete_operation_empty_wagons(
        self,
        service: RakeOperationsService,
    ) -> None:
        """Test complete operation with empty wagon list."""
        # Act
        result = service.create_complete_operation(
            wagons=[],
            formation_track='collection',
            target_track='retrofit',
            rake_type=RakeType.WORKSHOP_RAKE,
        )

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'no wagons' in result.error_message
        assert result.operation is None
        assert result.completed_wagons == []

    def test_rake_operation_dataclass(self) -> None:
        """Test RakeOperation dataclass creation."""
        # Act
        operation = RakeOperation(
            rake_id='TEST_RAKE',
            formation_track='track1',
            target_track='track2',
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_time=timedelta(minutes=5),
            transport_time=timedelta(minutes=10),
            dissolution_time=timedelta(minutes=3),
            total_time=timedelta(minutes=18),
        )

        # Assert
        assert operation.rake_id == 'TEST_RAKE'
        assert operation.formation_track == 'track1'
        assert operation.target_track == 'track2'
        assert operation.rake_type == RakeType.WORKSHOP_RAKE
        assert operation.total_time == timedelta(minutes=18)

    def test_rake_operation_result_dataclass(self) -> None:
        """Test RakeOperationResult dataclass creation."""
        # Arrange
        operation = RakeOperation(
            rake_id='TEST_RAKE',
            formation_track='track1',
            target_track='track2',
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_time=timedelta(minutes=5),
            transport_time=timedelta(minutes=10),
            dissolution_time=timedelta(minutes=3),
            total_time=timedelta(minutes=18),
        )
        wagons = [
            Wagon(
                id='W1',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )
        ]

        # Act
        result = RakeOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            completed_wagons=wagons,
        )

        # Assert
        assert result.operation == operation
        assert result.success is True
        assert result.error_message is None
        assert result.completed_wagons == wagons
