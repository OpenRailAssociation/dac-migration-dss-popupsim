"""Unit tests for simplified WorkshopSchedulingService domain service."""

from datetime import timedelta

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import RetrofitBay
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.services.workshop_scheduling_service import WorkshopSchedulingService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


@pytest.fixture
def scheduling_service() -> WorkshopSchedulingService:
    """Create workshop scheduling service."""
    return WorkshopSchedulingService(base_processing_time_minutes=120.0)


@pytest.fixture
def sample_wagons() -> list[Wagon]:
    """Create sample wagons for testing."""
    return [
        Wagon(
            id=f'W{i:03d}',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )
        for i in range(1, 4)  # 3 wagons
    ]


@pytest.fixture
def workshop_with_capacity() -> Workshop:
    """Create workshop with available capacity."""
    bays = [
        RetrofitBay(id=f'WS01_bay_{i}', workshop_id='WS01')
        for i in range(5)  # 5 bays
    ]
    return Workshop(id='WS01', location='workshop_track', bays=bays)


@pytest.fixture
def workshop_no_capacity() -> Workshop:
    """Create workshop with no available capacity."""
    bays = [
        RetrofitBay(id=f'WS02_bay_{i}', workshop_id='WS02')
        for i in range(2)  # 2 bays
    ]
    workshop = Workshop(id='WS02', location='workshop_track', bays=bays)

    # Make all bays busy
    for i, bay in enumerate(bays):
        bay.start_retrofit(f'BUSY_WAGON_{i}', 0.0)

    return workshop


def test_schedule_batch_success(
    scheduling_service: WorkshopSchedulingService, sample_wagons: list[Wagon], workshop_with_capacity: Workshop
) -> None:
    """Test successful batch scheduling."""
    result = scheduling_service.schedule_batch(sample_wagons, workshop_with_capacity)

    assert result.success
    assert result.workshop_id == 'WS01'
    assert result.batch_size == 3
    assert result.estimated_processing_time == timedelta(minutes=120)  # Parallel processing
    assert result.error_message is None


def test_schedule_batch_empty_wagons(
    scheduling_service: WorkshopSchedulingService, workshop_with_capacity: Workshop
) -> None:
    """Test batch scheduling with empty wagon list."""
    result = scheduling_service.schedule_batch([], workshop_with_capacity)

    assert not result.success
    assert result.batch_size == 0
    assert 'empty wagon list' in result.error_message.lower()


def test_schedule_batch_insufficient_capacity(
    scheduling_service: WorkshopSchedulingService, sample_wagons: list[Wagon], workshop_no_capacity: Workshop
) -> None:
    """Test batch scheduling with insufficient workshop capacity."""
    result = scheduling_service.schedule_batch(sample_wagons, workshop_no_capacity)

    assert not result.success
    assert result.batch_size == 3
    assert 'insufficient capacity' in result.error_message.lower()


def test_calculate_processing_time(scheduling_service: WorkshopSchedulingService) -> None:
    """Test processing time calculation."""
    # Single wagon
    time_1 = scheduling_service.calculate_processing_time(1)
    assert time_1 == timedelta(minutes=120)

    # Multiple wagons (parallel processing)
    time_3 = scheduling_service.calculate_processing_time(3)
    assert time_3 == timedelta(minutes=120)  # Same time due to parallel processing

    # Zero wagons
    time_0 = scheduling_service.calculate_processing_time(0)
    assert time_0 == timedelta(0)


def test_can_workshop_handle_batch(
    scheduling_service: WorkshopSchedulingService, workshop_with_capacity: Workshop, workshop_no_capacity: Workshop
) -> None:
    """Test workshop capacity checking."""
    # Workshop with capacity
    assert scheduling_service.can_workshop_handle_batch(3, workshop_with_capacity)
    assert scheduling_service.can_workshop_handle_batch(5, workshop_with_capacity)
    assert not scheduling_service.can_workshop_handle_batch(6, workshop_with_capacity)  # Exceeds capacity

    # Workshop without capacity
    assert not scheduling_service.can_workshop_handle_batch(1, workshop_no_capacity)
