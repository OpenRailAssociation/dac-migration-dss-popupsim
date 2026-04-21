"""Unit tests for WorkshopOperationsService."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.retrofit_workflow.application.services.workshop_operations_service import WorkshopOperation
from contexts.retrofit_workflow.application.services.workshop_operations_service import WorkshopOperationResult
from contexts.retrofit_workflow.application.services.workshop_operations_service import WorkshopOperationsService
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.services.workshop_scheduling_service import SchedulingResult
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


class TestWorkshopOperationsService:
    """Test cases for WorkshopOperationsService."""

    @pytest.fixture
    def mock_workshop_assignment(self) -> Mock:
        """Mock workshop assignment service."""
        return Mock()

    @pytest.fixture
    def mock_workshop_scheduling(self) -> Mock:
        """Mock workshop scheduling service."""
        return Mock()

    @pytest.fixture
    def mock_batch_formation(self) -> Mock:
        """Mock batch formation service."""
        return Mock()

    @pytest.fixture
    def service(
        self,
        mock_workshop_assignment: Mock,
        mock_workshop_scheduling: Mock,
        mock_batch_formation: Mock,
    ) -> WorkshopOperationsService:
        """Create service with mocked dependencies."""
        return WorkshopOperationsService(
            mock_workshop_assignment,
            mock_workshop_scheduling,
            mock_batch_formation,
        )

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
        ]

    @pytest.fixture
    def sample_workshop(self) -> Workshop:
        """Create sample workshop for testing."""
        from contexts.retrofit_workflow.domain.entities.workshop import create_workshop

        return create_workshop('WS001', 'Test Location', 5)

    @pytest.fixture
    def sample_batch_aggregate(self) -> BatchAggregate:
        """Create sample batch aggregate for testing."""
        wagons = [
            Wagon(
                id='W1',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )
        ]
        return BatchAggregate(
            id='BATCH_001',
            wagons=wagons,
            destination='WS001',
            rake_id='RAKE_001',
        )

    def test_create_processing_operation_success(
        self,
        service: WorkshopOperationsService,
        mock_batch_formation: Mock,
        mock_workshop_scheduling: Mock,
        sample_wagons: list[Wagon],
        sample_workshop: Workshop,
        sample_batch_aggregate: BatchAggregate,
    ) -> None:
        """Test successful processing operation creation."""
        # Arrange
        mock_batch_formation.form_batch_for_workshop.return_value = sample_wagons
        mock_workshop_scheduling.schedule_batch.return_value = SchedulingResult(
            workshop_id='WS001',
            batch_size=2,
            estimated_processing_time=timedelta(hours=2),
            success=True,
        )
        mock_batch_formation.create_batch_aggregate.return_value = sample_batch_aggregate

        # Act
        result = service.create_processing_operation(sample_wagons, sample_workshop)

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.workshop_id == 'WS001'
        assert result.operation.wagon_count == 2
        assert result.operation.processing_time == timedelta(hours=2)
        assert result.processed_wagons == sample_wagons
        assert result.batch_aggregate == sample_batch_aggregate

    def test_create_processing_operation_empty_wagons(
        self,
        service: WorkshopOperationsService,
        sample_workshop: Workshop,
    ) -> None:
        """Test processing operation with empty wagon list."""
        # Act
        result = service.create_processing_operation([], sample_workshop)

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'no wagons' in result.error_message
        assert result.operation is None
        assert result.processed_wagons == []

    def test_create_processing_operation_no_batch_wagons(
        self,
        service: WorkshopOperationsService,
        mock_batch_formation: Mock,
        sample_wagons: list[Wagon],
        sample_workshop: Workshop,
    ) -> None:
        """Test processing operation when no wagons can form batch."""
        # Arrange
        mock_batch_formation.form_batch_for_workshop.return_value = []

        # Act
        result = service.create_processing_operation(sample_wagons, sample_workshop)

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'No wagons can be processed' in result.error_message
        assert result.operation is None
        assert result.processed_wagons == []

    def test_create_processing_operation_scheduling_failure(
        self,
        service: WorkshopOperationsService,
        mock_batch_formation: Mock,
        mock_workshop_scheduling: Mock,
        sample_wagons: list[Wagon],
        sample_workshop: Workshop,
    ) -> None:
        """Test processing operation with scheduling failure."""
        # Arrange
        mock_batch_formation.form_batch_for_workshop.return_value = sample_wagons
        mock_workshop_scheduling.schedule_batch.return_value = SchedulingResult(
            workshop_id='WS001',
            batch_size=2,
            estimated_processing_time=timedelta(0),
            success=False,
            error_message='Insufficient capacity',
        )

        # Act
        result = service.create_processing_operation(sample_wagons, sample_workshop)

        # Assert
        assert result.success is False
        assert result.error_message == 'Insufficient capacity'
        assert result.operation is None
        assert result.processed_wagons == []

    def test_create_processing_operation_batch_aggregate_failure(
        self,
        service: WorkshopOperationsService,
        mock_batch_formation: Mock,
        mock_workshop_scheduling: Mock,
        sample_wagons: list[Wagon],
        sample_workshop: Workshop,
    ) -> None:
        """Test processing operation with batch aggregate creation failure."""
        # Arrange
        mock_batch_formation.form_batch_for_workshop.return_value = sample_wagons
        mock_workshop_scheduling.schedule_batch.return_value = SchedulingResult(
            workshop_id='WS001',
            batch_size=2,
            estimated_processing_time=timedelta(hours=2),
            success=True,
        )
        mock_batch_formation.create_batch_aggregate.side_effect = Exception('Coupling error')

        # Act
        result = service.create_processing_operation(sample_wagons, sample_workshop)

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'Failed to create batch aggregate' in result.error_message
        assert result.operation is None
        assert result.processed_wagons == []

    def test_select_optimal_workshop_success(
        self,
        service: WorkshopOperationsService,
        mock_workshop_assignment: Mock,
        mock_workshop_scheduling: Mock,
        sample_wagons: list[Wagon],
        sample_workshop: Workshop,
    ) -> None:
        """Test successful workshop selection."""
        # Arrange
        wagon = sample_wagons[0]
        workshops = {'WS001': sample_workshop}
        mock_workshop_assignment.select_workshop.return_value = 'WS001'
        mock_workshop_scheduling.calculate_processing_time.return_value = timedelta(hours=2)

        # Act
        result = service.select_optimal_workshop(wagon, workshops)

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.workshop_id == 'WS001'
        assert result.operation.wagon_count == 1
        assert result.processed_wagons == [wagon]

    def test_select_optimal_workshop_no_workshop_available(
        self,
        service: WorkshopOperationsService,
        mock_workshop_assignment: Mock,
        sample_wagons: list[Wagon],
        sample_workshop: Workshop,
    ) -> None:
        """Test workshop selection when no workshop available."""
        # Arrange
        wagon = sample_wagons[0]
        workshops = {'WS001': sample_workshop}
        mock_workshop_assignment.select_workshop.return_value = None

        # Act
        result = service.select_optimal_workshop(wagon, workshops)

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'No suitable workshop available' in result.error_message
        assert result.operation is None
        assert result.processed_wagons == []

    def test_calculate_batch_capacity(
        self,
        service: WorkshopOperationsService,
        mock_batch_formation: Mock,
        mock_workshop_scheduling: Mock,
        sample_workshop: Workshop,
    ) -> None:
        """Test batch capacity calculation."""
        # Arrange
        mock_batch_formation.calculate_batch_size_for_workshop.return_value = 3
        mock_workshop_scheduling.calculate_processing_time.return_value = timedelta(hours=2)

        # Act
        result = service.calculate_batch_capacity(sample_workshop, 5)

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is not None
        assert result.operation.workshop_id == 'WS001'
        assert result.operation.wagon_count == 3
        assert result.operation.processing_time == timedelta(hours=2)

    def test_validate_workshop_assignment_success(
        self,
        service: WorkshopOperationsService,
        mock_workshop_assignment: Mock,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test successful workshop assignment validation."""
        # Arrange
        wagon = sample_wagons[0]
        mock_workshop_assignment.can_assign.return_value = True

        # Act
        result = service.validate_workshop_assignment(wagon, 'WS001')

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.operation is None
        assert result.processed_wagons == [wagon]

    def test_validate_workshop_assignment_failure(
        self,
        service: WorkshopOperationsService,
        mock_workshop_assignment: Mock,
        sample_wagons: list[Wagon],
    ) -> None:
        """Test workshop assignment validation failure."""
        # Arrange
        wagon = sample_wagons[0]
        mock_workshop_assignment.can_assign.return_value = False

        # Act
        result = service.validate_workshop_assignment(wagon, 'WS001')

        # Assert
        assert result.success is False
        assert result.error_message is not None
        assert 'cannot be assigned to workshop' in result.error_message
        assert result.operation is None
        assert result.processed_wagons == []

    def test_workshop_operation_dataclass(self) -> None:
        """Test WorkshopOperation dataclass creation."""
        # Act
        operation = WorkshopOperation(
            workshop_id='WS001',
            batch_id='BATCH_001',
            wagon_count=3,
            processing_time=timedelta(hours=2),
            total_time=timedelta(hours=2),
        )

        # Assert
        assert operation.workshop_id == 'WS001'
        assert operation.batch_id == 'BATCH_001'
        assert operation.wagon_count == 3
        assert operation.processing_time == timedelta(hours=2)
        assert operation.total_time == timedelta(hours=2)

    def test_workshop_operation_result_dataclass(self, sample_batch_aggregate: BatchAggregate) -> None:
        """Test WorkshopOperationResult dataclass creation."""
        # Arrange
        operation = WorkshopOperation(
            workshop_id='WS001',
            batch_id='BATCH_001',
            wagon_count=3,
            processing_time=timedelta(hours=2),
            total_time=timedelta(hours=2),
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
        result = WorkshopOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            processed_wagons=wagons,
            batch_aggregate=sample_batch_aggregate,
        )

        # Assert
        assert result.operation == operation
        assert result.success is True
        assert result.error_message is None
        assert result.processed_wagons == wagons
        assert result.batch_aggregate == sample_batch_aggregate
