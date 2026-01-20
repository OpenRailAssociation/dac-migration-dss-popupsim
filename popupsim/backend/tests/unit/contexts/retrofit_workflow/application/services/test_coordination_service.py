"""Tests for coordination service."""

from contexts.retrofit_workflow.application.services.coordination_service import CoordinationService
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


@pytest.fixture
def coordination_service() -> CoordinationService:
    """Create coordination service for testing."""
    return CoordinationService()


@pytest.fixture
def sample_wagon() -> Wagon:
    """Create sample wagon for testing."""
    coupler_a = Coupler(type=CouplerType.SCREW, side='A')
    coupler_b = Coupler(type=CouplerType.SCREW, side='B')
    return Wagon(id='W001', length=15.0, coupler_a=coupler_a, coupler_b=coupler_b)


def test_initial_state(coordination_service: CoordinationService) -> None:
    """Test initial coordination service state."""
    assert coordination_service.can_workshop_proceed() is True
    assert coordination_service.is_parking_in_progress() is False
    assert coordination_service.get_accumulator_size() == 0
    assert coordination_service.get_workshop_turn_index() == 0


def test_parking_blocks_workshop(coordination_service: CoordinationService) -> None:
    """Test that parking blocks workshop operations."""
    # Initially workshop can proceed
    assert coordination_service.can_workshop_proceed() is True

    # Start parking - should block workshop
    coordination_service.start_parking()
    assert coordination_service.can_workshop_proceed() is False
    assert coordination_service.is_parking_in_progress() is True

    # Finish parking - should unblock workshop
    coordination_service.finish_parking()
    assert coordination_service.can_workshop_proceed() is True
    assert coordination_service.is_parking_in_progress() is False


def test_accumulator_blocks_workshop(coordination_service: CoordinationService, sample_wagon: Wagon) -> None:
    """Test that wagons in accumulator block workshop operations."""
    # Initially workshop can proceed
    assert coordination_service.can_workshop_proceed() is True

    # Add wagon to accumulator - should block workshop
    coordination_service.add_to_accumulator([sample_wagon])
    assert coordination_service.can_workshop_proceed() is False
    assert coordination_service.get_accumulator_size() == 1

    # Finish parking (clears accumulator) - should unblock workshop
    coordination_service.finish_parking()
    assert coordination_service.can_workshop_proceed() is True
    assert coordination_service.get_accumulator_size() == 0


def test_workshop_turn_management(coordination_service: CoordinationService) -> None:
    """Test workshop turn index management."""
    assert coordination_service.get_workshop_turn_index() == 0

    coordination_service.set_workshop_turn_index(2)
    assert coordination_service.get_workshop_turn_index() == 2


def test_status_reporting(coordination_service: CoordinationService, sample_wagon: Wagon) -> None:
    """Test status reporting functionality."""
    status = coordination_service.get_status()

    expected_keys = {'parking_in_progress', 'accumulator_size', 'workshop_turn_index', 'can_workshop_proceed'}
    assert set(status.keys()) == expected_keys

    # Test with parking active
    coordination_service.start_parking()
    coordination_service.add_to_accumulator([sample_wagon])

    status = coordination_service.get_status()
    assert status['parking_in_progress'] is True
    assert status['accumulator_size'] == 1
    assert status['can_workshop_proceed'] is False


def test_multiple_wagons_in_accumulator(coordination_service: CoordinationService) -> None:
    """Test handling multiple wagons in accumulator."""
    coupler_a = Coupler(type=CouplerType.SCREW, side='A')
    coupler_b = Coupler(type=CouplerType.SCREW, side='B')

    wagons = [
        Wagon(id='W001', length=15.0, coupler_a=coupler_a, coupler_b=coupler_b),
        Wagon(id='W002', length=12.0, coupler_a=coupler_a, coupler_b=coupler_b),
        Wagon(id='W003', length=18.0, coupler_a=coupler_a, coupler_b=coupler_b),
    ]

    coordination_service.add_to_accumulator(wagons)
    assert coordination_service.get_accumulator_size() == 3
    assert coordination_service.can_workshop_proceed() is False

    # Clear accumulator
    coordination_service.finish_parking()
    assert coordination_service.get_accumulator_size() == 0
    assert coordination_service.can_workshop_proceed() is True
