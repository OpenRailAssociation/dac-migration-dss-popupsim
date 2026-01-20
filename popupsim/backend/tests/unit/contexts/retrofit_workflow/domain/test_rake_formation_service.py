"""Unit tests for RakeFormationService."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.configuration.domain.models.process_times import ProcessTimes
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.rake_formation_service import RakeFormationService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
from contexts.retrofit_workflow.domain.value_objects.rake_formation_request import RakeFormationRequest
import pytest


class TestRakeFormationService:
    """Test cases for RakeFormationService."""

    @pytest.fixture
    def service(self) -> RakeFormationService:
        """Create RakeFormationService instance."""
        return RakeFormationService()

    @pytest.fixture
    def process_times(self) -> ProcessTimes:
        """Create ProcessTimes with test values."""
        return ProcessTimes(
            screw_coupling_time=timedelta(minutes=1.0),
            screw_decoupling_time=timedelta(minutes=1.0),
            dac_coupling_time=timedelta(minutes=0.5),
            dac_decoupling_time=timedelta(minutes=0.5),
        )

    @pytest.fixture
    def screw_wagon(self) -> Wagon:
        """Create wagon with screw couplers."""
        return Wagon(
            id='W001',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )

    @pytest.fixture
    def dac_wagon(self) -> Wagon:
        """Create wagon with DAC couplers."""
        return Wagon(
            id='W002',
            length=15.0,
            coupler_a=Coupler(CouplerType.DAC, 'A'),
            coupler_b=Coupler(CouplerType.DAC, 'B'),
        )

    def test_calculate_coupling_operation_time_single_wagon(
        self, service: RakeFormationService, process_times: ProcessTimes, screw_wagon: Wagon
    ) -> None:
        """Test coupling time calculation for single wagon returns zero."""
        result = service.calculate_coupling_operation_time([screw_wagon], process_times, is_coupling=True)
        assert result == 0.0

    def test_calculate_coupling_operation_time_empty_list(
        self, service: RakeFormationService, process_times: ProcessTimes
    ) -> None:
        """Test coupling time calculation for empty wagon list returns zero."""
        result = service.calculate_coupling_operation_time([], process_times, is_coupling=True)
        assert result == 0.0

    def test_calculate_coupling_operation_time_two_screw_wagons(
        self, service: RakeFormationService, process_times: ProcessTimes
    ) -> None:
        """Test coupling time for two screw wagons."""
        wagon1 = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        wagon2 = Wagon(
            id='W002', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )

        result = service.calculate_coupling_operation_time([wagon1, wagon2], process_times, is_coupling=True)
        expected = process_times.get_coupling_ticks('SCREW')
        assert result == expected

    def test_calculate_coupling_operation_time_two_dac_wagons(
        self, service: RakeFormationService, process_times: ProcessTimes
    ) -> None:
        """Test coupling time for two DAC wagons."""
        wagon1 = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.DAC, 'A'), coupler_b=Coupler(CouplerType.DAC, 'B')
        )
        wagon2 = Wagon(
            id='W002', length=15.0, coupler_a=Coupler(CouplerType.DAC, 'A'), coupler_b=Coupler(CouplerType.DAC, 'B')
        )

        result = service.calculate_coupling_operation_time([wagon1, wagon2], process_times, is_coupling=True)
        expected = process_times.get_coupling_ticks('DAC')
        assert result == expected

    def test_calculate_coupling_operation_time_three_wagons(
        self, service: RakeFormationService, process_times: ProcessTimes
    ) -> None:
        """Test coupling time for three wagons (two coupling operations)."""
        wagon1 = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        wagon2 = Wagon(
            id='W002', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        wagon3 = Wagon(
            id='W003', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )

        result = service.calculate_coupling_operation_time([wagon1, wagon2, wagon3], process_times, is_coupling=True)
        expected = 2 * process_times.get_coupling_ticks('SCREW')  # Two coupling operations
        assert result == expected

    def test_calculate_decoupling_operation_time(
        self, service: RakeFormationService, process_times: ProcessTimes
    ) -> None:
        """Test decoupling time calculation."""
        wagon1 = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        wagon2 = Wagon(
            id='W002', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )

        result = service.calculate_coupling_operation_time([wagon1, wagon2], process_times, is_coupling=False)
        expected = process_times.get_decoupling_ticks('SCREW')
        assert result == expected

    def test_calculate_rake_formation_time(
        self, service: RakeFormationService, process_times: ProcessTimes, screw_wagon: Wagon, dac_wagon: Wagon
    ) -> None:
        """Test rake formation time calculation delegates to coupling operation."""
        result = service.calculate_rake_formation_time([screw_wagon, dac_wagon], process_times)
        expected = service.calculate_coupling_operation_time([screw_wagon, dac_wagon], process_times, is_coupling=True)
        assert result == expected

    def test_calculate_rake_dissolution_time(
        self, service: RakeFormationService, process_times: ProcessTimes, screw_wagon: Wagon, dac_wagon: Wagon
    ) -> None:
        """Test rake dissolution time calculation delegates to decoupling operation."""
        result = service.calculate_rake_dissolution_time([screw_wagon, dac_wagon], process_times)
        expected = service.calculate_coupling_operation_time([screw_wagon, dac_wagon], process_times, is_coupling=False)
        assert result == expected

    def test_can_form_rake_delegates_to_validator(self, service: RakeFormationService, screw_wagon: Wagon) -> None:
        """Test can_form_rake delegates to coupling validator."""
        service.coupling_validator.can_form_rake = Mock(return_value=(True, None))

        result = service.can_form_rake([screw_wagon])

        service.coupling_validator.can_form_rake.assert_called_once_with([screw_wagon])
        assert result == (True, None)

    def test_form_rake_success(self, service: RakeFormationService) -> None:
        """Test successful rake formation."""
        wagon = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        request = RakeFormationRequest(
            rake_id='RAKE_001',
            wagons=[wagon],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='TRACK_A',
            target_track='TRACK_B',
            formation_time=100.0,
        )

        service.coupling_validator.can_form_rake = Mock(return_value=(True, None))

        rake, error = service.form_rake(request)

        assert rake is not None
        assert error is None
        assert rake.id == 'RAKE_001'
        assert rake.wagon_ids == ['W001']
        assert rake.rake_type == RakeType.WORKSHOP_RAKE
        assert wagon.rake_id == 'RAKE_001'

    def test_form_rake_validation_failure(self, service: RakeFormationService) -> None:
        """Test rake formation with validation failure."""
        wagon = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        request = RakeFormationRequest(
            rake_id='RAKE_001',
            wagons=[wagon],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='TRACK_A',
            target_track='TRACK_B',
            formation_time=100.0,
        )

        service.coupling_validator.can_form_rake = Mock(return_value=(False, 'Incompatible couplers'))

        rake, error = service.form_rake(request)

        assert rake is None
        assert error == 'Incompatible couplers'

    def test_dissolve_rake(self, service: RakeFormationService) -> None:
        """Test rake dissolution removes wagon associations."""
        wagon1 = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        wagon2 = Wagon(
            id='W002', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )

        # Set up wagons with rake association
        wagon1.rake_id = 'RAKE_001'
        wagon2.rake_id = 'RAKE_001'

        rake = Rake(
            id='RAKE_001',
            wagon_ids=['W001', 'W002'],
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='TRACK_A',
            target_track='TRACK_B',
            formation_time=100.0,
        )

        service.dissolve_rake(rake, [wagon1, wagon2])

        assert wagon1.rake_id is None
        assert wagon2.rake_id is None

    def test_dissolve_rake_partial_match(self, service: RakeFormationService) -> None:
        """Test rake dissolution only affects wagons in the rake."""
        wagon1 = Wagon(
            id='W001', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )
        wagon2 = Wagon(
            id='W002', length=15.0, coupler_a=Coupler(CouplerType.SCREW, 'A'), coupler_b=Coupler(CouplerType.SCREW, 'B')
        )

        # Only wagon1 is in the rake
        wagon1.rake_id = 'RAKE_001'
        wagon2.rake_id = 'OTHER_RAKE'

        rake = Rake(
            id='RAKE_001',
            wagon_ids=['W001'],  # Only W001 in rake
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='TRACK_A',
            target_track='TRACK_B',
            formation_time=100.0,
        )

        service.dissolve_rake(rake, [wagon1, wagon2])

        assert wagon1.rake_id is None  # Should be cleared
        assert wagon2.rake_id == 'OTHER_RAKE'  # Should remain unchanged
