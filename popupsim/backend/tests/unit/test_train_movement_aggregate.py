"""Unit tests for TrainMovement aggregate."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.configuration.application.dtos.route_input_dto import RouteType
from contexts.configuration.domain.models.process_times import ProcessTimes
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainMovement
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainMovementStatus
from contexts.retrofit_workflow.domain.aggregates.train_movement_aggregate import TrainType
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.train_formation_service import TrainFormationService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


@pytest.fixture
def mock_locomotive() -> Locomotive:
    """Create mock locomotive."""
    loco = Mock(spec=Locomotive)
    loco.id = 'LOCO-001'
    loco.length = 20.0
    return loco


@pytest.fixture
def mock_wagons() -> list[Wagon]:
    """Create mock wagons."""
    wagons: list[Wagon] = []
    for i in range(3):
        wagon = Mock(spec=Wagon)
        wagon.id = f'WAGON-{i + 1:03d}'
        wagon.length = 15.0
        wagon.coupler_a = Coupler(type=CouplerType.SCREW, side='A')
        wagon.coupler_b = Coupler(type=CouplerType.SCREW, side='B')
        wagon.needs_retrofit = True
        wagons.append(wagon)
    return wagons


@pytest.fixture
def mock_batch(mock_wagons: list[Wagon]) -> BatchAggregate:
    """Create mock batch aggregate."""
    return BatchAggregate(
        id='BATCH-001',
        wagons=mock_wagons,
        destination='workshop_1',
        rake_id='RAKE-001',
    )


@pytest.fixture
def process_times() -> ProcessTimes:
    """Create process times configuration."""
    return ProcessTimes(
        loco_coupling_time=timedelta(minutes=3),
        loco_decoupling_time=timedelta(minutes=2),
        full_brake_test_time=timedelta(minutes=5),
        technical_inspection_time=timedelta(minutes=2),
        shunting_preparation_time=timedelta(minutes=1),
    )


def test_create_shunting_train(mock_locomotive: Locomotive, mock_batch: BatchAggregate) -> None:
    """Test creating a shunting train movement."""
    train = TrainMovement(
        id='TRAIN-001',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.SHUNTING,
        origin='retrofit',
        destination='workshop_1',
    )

    assert train.id == 'TRAIN-001'
    assert train.locomotive == mock_locomotive
    assert train.batch == mock_batch
    assert train.train_type == TrainType.SHUNTING
    assert train.is_shunting
    assert not train.is_mainline
    assert train.status == TrainMovementStatus.FORMING
    assert train.wagon_count == 3


def test_create_mainline_train(mock_locomotive: Locomotive, mock_batch: BatchAggregate) -> None:
    """Test creating a mainline train movement."""
    train = TrainMovement(
        id='TRAIN-002',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.MAINLINE,
        origin='collection',
        destination='retrofit',
    )

    assert train.train_type == TrainType.MAINLINE
    assert train.is_mainline
    assert not train.is_shunting


def test_shunting_train_ready_immediately(mock_locomotive: Locomotive, mock_batch: BatchAggregate) -> None:
    """Test that shunting train is ready immediately without brake test."""
    train = TrainMovement(
        id='TRAIN-003',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.SHUNTING,
        origin='retrofit',
        destination='workshop_1',
    )

    assert train.is_ready_for_departure()
    train.mark_ready_for_departure(0.0)
    assert train.status == TrainMovementStatus.READY


def test_mainline_train_requires_brake_test_and_inspection(
    mock_locomotive: Locomotive, mock_batch: BatchAggregate
) -> None:
    """Test that mainline train requires brake test and inspection."""
    train = TrainMovement(
        id='TRAIN-004',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.MAINLINE,
        origin='collection',
        destination='retrofit',
    )

    # Not ready without brake test and inspection
    assert not train.is_ready_for_departure()

    # Complete brake test
    train.complete_brake_test()
    assert not train.is_ready_for_departure()  # Still need inspection

    # Complete inspection
    train.complete_inspection()
    assert train.is_ready_for_departure()

    # Mark ready
    train.mark_ready_for_departure(0.0)
    assert train.status == TrainMovementStatus.READY


def test_shunting_preparation_time(
    mock_locomotive: Locomotive, mock_batch: BatchAggregate, process_times: ProcessTimes
) -> None:
    """Test shunting preparation time (loco coupling + preparation)."""
    train = TrainMovement(
        id='TRAIN-005',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.SHUNTING,
        origin='retrofit',
        destination='workshop_1',
    )

    prep_time = train.get_preparation_time(process_times)
    # Should be 4 minutes (3 loco coupling + 1 preparation)
    assert prep_time == 4.0


def test_mainline_preparation_time(
    mock_locomotive: Locomotive, mock_batch: BatchAggregate, process_times: ProcessTimes
) -> None:
    """Test mainline preparation time (loco coupling + brake test + inspection)."""
    train = TrainMovement(
        id='TRAIN-006',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.MAINLINE,
        origin='collection',
        destination='retrofit',
    )

    prep_time = train.get_preparation_time(process_times)
    # Should be 3 + 5 + 2 = 10 minutes
    assert prep_time == 10.0


def test_train_lifecycle(mock_locomotive: Locomotive, mock_batch: BatchAggregate) -> None:
    """Test complete train lifecycle."""
    train = TrainMovement(
        id='TRAIN-007',
        locomotive=mock_locomotive,
        batch=mock_batch,
        train_type=TrainType.SHUNTING,
        origin='retrofit',
        destination='workshop_1',
    )

    # Form -> Ready
    train.mark_ready_for_departure(0.0)
    assert train.status == TrainMovementStatus.READY

    # Ready -> In Transit
    train.depart(0.0)
    assert train.status == TrainMovementStatus.IN_TRANSIT

    # In Transit -> Arrived
    train.arrive(5.0)
    assert train.status == TrainMovementStatus.ARRIVED

    # Arrived -> Dissolved
    loco, batch = train.dissolve()
    assert loco == mock_locomotive
    assert batch == mock_batch
    assert train.status == TrainMovementStatus.DISSOLVED


def test_train_formation_service_shunting(
    mock_locomotive: Locomotive, mock_batch: BatchAggregate, process_times: ProcessTimes
) -> None:
    """Test TrainFormationService for shunting operations."""
    service = TrainFormationService()

    train = service.form_train(
        locomotive=mock_locomotive,
        batch=mock_batch,
        origin='retrofit',
        destination='workshop_1',
        route_type=RouteType.SHUNTING,
    )

    assert train.is_shunting
    assert train.origin == 'retrofit'
    assert train.destination == 'workshop_1'

    # Prepare train
    prep_time = service.prepare_train(train, process_times, 0.0)
    assert prep_time == 4.0  # Loco coupling + preparation
    assert train.status == TrainMovementStatus.READY


def test_train_formation_service_mainline(
    mock_locomotive: Locomotive, mock_batch: BatchAggregate, process_times: ProcessTimes
) -> None:
    """Test TrainFormationService for mainline operations."""
    service = TrainFormationService()

    train = service.form_train(
        locomotive=mock_locomotive,
        batch=mock_batch,
        origin='collection',
        destination='retrofit',
        route_type=RouteType.MAINLINE,
    )

    assert train.is_mainline
    assert train.origin == 'collection'
    assert train.destination == 'retrofit'

    # Prepare train
    prep_time = service.prepare_train(train, process_times, 0.0)
    assert prep_time == 10.0  # Loco coupling + brake test + inspection
    assert train.status == TrainMovementStatus.READY
