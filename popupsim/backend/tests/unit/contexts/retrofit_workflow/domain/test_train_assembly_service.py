"""Unit tests for TrainAssemblyService."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.configuration.domain.models.process_times import ProcessTimes
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.train_assembly_service import TrainAssemblyService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


class TestTrainAssemblyService:
    """Test cases for TrainAssemblyService."""

    @pytest.fixture
    def service(self) -> TrainAssemblyService:
        """Create TrainAssemblyService instance."""
        return TrainAssemblyService()

    @pytest.fixture
    def process_times(self) -> ProcessTimes:
        """Create ProcessTimes with test values."""
        return ProcessTimes(
            screw_coupling_time=timedelta(minutes=1.0),
            screw_decoupling_time=timedelta(minutes=1.0),
            dac_coupling_time=timedelta(minutes=0.5),
            dac_decoupling_time=timedelta(minutes=0.5),
            brake_continuity_check_time=timedelta(seconds=30.0),
            full_brake_test_time=timedelta(minutes=4.0),
            technical_inspection_time=timedelta(minutes=2.0),
        )

    @pytest.fixture
    def locomotive(self) -> Locomotive:
        """Create locomotive with DAC couplers."""
        return Locomotive(
            id='LOCO_001',
            home_track='LOCO_PARK',
            coupler_front=Coupler(CouplerType.DAC, 'FRONT'),
            coupler_back=Coupler(CouplerType.DAC, 'BACK'),
        )

    @pytest.fixture
    def rake(self) -> Rake:
        """Create test rake."""
        return Rake(
            id='RAKE_001',
            wagon_ids=['W001', 'W002'],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='TRACK_A',
            target_track='TRACK_B',
            formation_time=100.0,
        )

    @pytest.fixture
    def wagon_repository(self) -> Mock:
        """Create mock wagon repository."""
        repo = Mock()
        wagon = Wagon(
            id='W001',
            length=15.0,
            coupler_a=Coupler(CouplerType.DAC, 'A'),
            coupler_b=Coupler(CouplerType.DAC, 'B'),
        )
        repo.get_by_id.return_value = wagon
        return repo

    def test_calculate_rake_assembly_time_with_dac_coupler(
        self, service: TrainAssemblyService, rake: Rake, wagon_repository: Mock, process_times: ProcessTimes
    ) -> None:
        """Test assembly time calculation with DAC coupler."""
        result = service.calculate_rake_assembly_time(rake, wagon_repository, process_times)

        expected_coupling = process_times.get_coupling_ticks('DAC')
        expected_continuity = process_times.brake_continuity_check_time.total_seconds() / 60.0
        expected_total = expected_coupling + expected_continuity

        assert result == expected_total
        wagon_repository.get_by_id.assert_called_once_with('W001')

    def test_calculate_rake_assembly_time_with_screw_coupler(
        self, service: TrainAssemblyService, rake: Rake, process_times: ProcessTimes
    ) -> None:
        """Test assembly time calculation with screw coupler."""
        wagon_repository = Mock()
        wagon = Wagon(
            id='W001',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )
        wagon_repository.get_by_id.return_value = wagon

        result = service.calculate_rake_assembly_time(rake, wagon_repository, process_times)

        expected_coupling = process_times.get_coupling_ticks('SCREW')
        expected_continuity = process_times.brake_continuity_check_time.total_seconds() / 60.0
        expected_total = expected_coupling + expected_continuity

        assert result == expected_total

    def test_calculate_final_assembly_time(self, service: TrainAssemblyService, process_times: ProcessTimes) -> None:
        """Test final assembly time calculation."""
        result = service.calculate_final_assembly_time(process_times)

        expected_brake_test = process_times.full_brake_test_time.total_seconds() / 60.0
        expected_inspection = process_times.technical_inspection_time.total_seconds() / 60.0
        expected_total = expected_brake_test + expected_inspection

        assert result == expected_total

    def test_can_assemble_rake_to_locomotive_success(
        self, service: TrainAssemblyService, locomotive: Locomotive, rake: Rake, wagon_repository: Mock
    ) -> None:
        """Test successful rake assembly validation."""
        # Mock coupling validator to return success
        service.coupling_validator.can_couple_loco_to_first_wagon = Mock(return_value=True)

        can_assemble, error = service.can_assemble_rake_to_locomotive(locomotive, rake, wagon_repository)

        assert can_assemble is True
        assert error is None
        wagon_repository.get_by_id.assert_called_once_with('W001')

    def test_can_assemble_rake_to_locomotive_incompatible_couplers(
        self, service: TrainAssemblyService, locomotive: Locomotive, rake: Rake, wagon_repository: Mock
    ) -> None:
        """Test rake assembly validation with incompatible couplers."""
        # Mock coupling validator to return failure
        service.coupling_validator.can_couple_loco_to_first_wagon = Mock(return_value=False)

        can_assemble, error = service.can_assemble_rake_to_locomotive(locomotive, rake, wagon_repository)

        assert can_assemble is False
        assert error is not None
        assert 'incompatible' in error.lower()
        assert 'LOCO_001' in error
        assert 'W001' in error

    def test_can_assemble_rake_to_locomotive_empty_rake(
        self, service: TrainAssemblyService, locomotive: Locomotive, wagon_repository: Mock
    ) -> None:
        """Test rake assembly validation with empty rake."""
        # Create rake with one wagon but mock repository to simulate empty rake behavior
        rake_with_missing_wagon = Rake(
            id='RAKE_WITH_MISSING_WAGON',
            wagon_ids=['MISSING_WAGON'],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='TRACK_A',
            target_track='TRACK_B',
            formation_time=100.0,
        )

        # Mock repository to raise ValueError when trying to get the missing wagon
        wagon_repository.get_by_id.side_effect = ValueError('Rake RAKE_WITH_MISSING_WAGON has no wagons')

        can_assemble, error = service.can_assemble_rake_to_locomotive(
            locomotive, rake_with_missing_wagon, wagon_repository
        )

        assert can_assemble is False
        assert error is not None
        assert 'no wagons' in error

    def test_can_assemble_rake_to_locomotive_repository_error(
        self, service: TrainAssemblyService, locomotive: Locomotive, rake: Rake, wagon_repository: Mock
    ) -> None:
        """Test rake assembly validation with repository error."""
        wagon_repository.get_by_id.side_effect = ValueError('Wagon not found')

        can_assemble, error = service.can_assemble_rake_to_locomotive(locomotive, rake, wagon_repository)

        assert can_assemble is False
        assert error == 'Wagon not found'
