"""Unit tests for batch-rake integration (Option 4 implementation)."""

from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import DomainError
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


def create_test_wagon(
    wagon_id: str, coupler_a_type: CouplerType = CouplerType.SCREW, coupler_b_type: CouplerType = CouplerType.SCREW
) -> Wagon:
    """Create test wagon with specified coupler types."""
    wagon = Wagon(
        id=wagon_id,
        length=15.0,
        coupler_a=Coupler(type=coupler_a_type, side='A'),
        coupler_b=Coupler(type=coupler_b_type, side='B'),
    )
    # Set wagon to classified status so it needs retrofit
    wagon.classify()
    return wagon


class TestBatchRakeIntegration:
    """Test batch-rake integration following Option 4 approach."""

    def test_batch_formation_service_creates_batch_with_rake(self) -> None:
        """Test that BatchFormationService creates batch with associated rake."""
        # Arrange
        service = BatchFormationService()
        wagons = [create_test_wagon('W001'), create_test_wagon('W002'), create_test_wagon('W003')]

        # Act
        batch = service.create_batch_aggregate(wagons, 'WORKSHOP_A')

        # Assert
        assert batch.rake_id.endswith('_RAKE')
        assert batch.destination == 'WORKSHOP_A'
        assert len(batch.wagons) == 3

        # Verify wagons are assigned to rake
        for wagon in wagons:
            assert wagon.rake_id == batch.rake_id

    def test_batch_formation_fails_with_incompatible_couplers(self) -> None:
        """Test that batch formation fails when wagons have incompatible couplers."""
        # Arrange
        service = BatchFormationService()
        wagons = [
            create_test_wagon('W001', CouplerType.SCREW, CouplerType.SCREW),
            create_test_wagon('W002', CouplerType.DAC, CouplerType.DAC),  # Incompatible
        ]

        # Act & Assert
        with pytest.raises(DomainError, match='Cannot form batch - insufficient wagons'):
            service.create_batch_aggregate(wagons, 'WORKSHOP_B')

    def test_batch_formation_fails_with_empty_wagons(self) -> None:
        """Test that batch formation fails with empty wagon list."""
        # Arrange
        service = BatchFormationService()

        # Act & Assert
        with pytest.raises(DomainError, match='insufficient wagons'):
            service.create_batch_aggregate([], 'WORKSHOP_C')

    def test_can_form_batch_validates_coupling_compatibility(self) -> None:
        """Test that can_form_batch validates coupling compatibility."""
        # Arrange
        service = BatchFormationService()
        compatible_wagons = [
            create_test_wagon('W001', CouplerType.SCREW, CouplerType.SCREW),
            create_test_wagon('W002', CouplerType.SCREW, CouplerType.SCREW),
        ]
        incompatible_wagons = [
            create_test_wagon('W003', CouplerType.SCREW, CouplerType.SCREW),
            create_test_wagon('W004', CouplerType.DAC, CouplerType.DAC),
        ]

        # Act & Assert
        assert service.can_form_batch(compatible_wagons) is True
        assert service.can_form_batch(incompatible_wagons) is False

    def test_batch_with_compatible_hybrid_couplers(self) -> None:
        """Test batch creation with compatible hybrid coupler configuration."""
        # Arrange
        service = BatchFormationService()
        wagons = [
            create_test_wagon('W001', CouplerType.SCREW, CouplerType.HYBRID),
            create_test_wagon('W002', CouplerType.HYBRID, CouplerType.DAC),
            create_test_wagon('W003', CouplerType.DAC, CouplerType.DAC),
        ]

        # Act
        batch = service.create_batch_aggregate(wagons, 'WORKSHOP_E')

        # Assert
        assert batch.rake_id.endswith('_RAKE')
        assert len(batch.wagons) == 3

        # Verify all wagons are properly assigned
        for wagon in wagons:
            assert wagon.rake_id == batch.rake_id

    def test_batch_transport_validation_includes_rake(self) -> None:
        """Test that batch transport validation includes rake existence."""
        # Arrange
        service = BatchFormationService()
        wagons = [create_test_wagon('W001')]

        # Act
        batch = service.create_batch_aggregate(wagons, 'WORKSHOP_D')

        # Assert
        assert batch.can_start_transport() is True
        assert batch.rake_id is not None
