"""Test configuration for retrofit workflow context tests."""

from unittest.mock import Mock

from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import create_workshop
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest
import simpy


@pytest.fixture
def simpy_env() -> simpy.Environment:
    """Create SimPy environment for testing."""
    return simpy.Environment()


@pytest.fixture
def test_wagon() -> Wagon:
    """Create test wagon."""
    return Wagon(
        id='test_wagon',
        length=15.0,
        coupler_a=Coupler(CouplerType.SCREW, 'A'),
        coupler_b=Coupler(CouplerType.SCREW, 'B'),
    )


@pytest.fixture
def test_wagons() -> list[Wagon]:
    """Create list of test wagons."""
    return [
        Wagon(
            id=f'wagon_{i}',
            length=15.0,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )
        for i in range(5)
    ]


@pytest.fixture
def test_locomotive() -> Locomotive:
    """Create test locomotive."""
    return Locomotive(
        id='test_loco',
        home_track='locoparking',
        coupler_front=Coupler(CouplerType.HYBRID, 'FRONT'),
        coupler_back=Coupler(CouplerType.HYBRID, 'BACK'),
    )


@pytest.fixture
def test_locomotives() -> list[Locomotive]:
    """Create list of test locomotives."""
    return [
        Locomotive(
            id=f'loco_{i}',
            home_track='locoparking',
            coupler_front=Coupler(CouplerType.HYBRID, 'FRONT'),
            coupler_back=Coupler(CouplerType.HYBRID, 'BACK'),
        )
        for i in range(3)
    ]


@pytest.fixture
def test_workshop():
    """Create test workshop."""
    return create_workshop('test_workshop', 'track_1', 2)


@pytest.fixture
def test_workshops():
    """Create list of test workshops."""
    return {
        'ws_1': create_workshop('ws_1', 'track_1', 2),
        'ws_2': create_workshop('ws_2', 'track_2', 3),
    }


@pytest.fixture
def mock_scenario():
    """Create mock scenario for testing."""
    scenario = Mock()

    # Workshops
    scenario.workshops = [
        Mock(id='ws_1', track='track_1', retrofit_stations=2),
        Mock(id='ws_2', track='track_2', retrofit_stations=3),
    ]

    # Locomotives
    scenario.locomotives = [Mock(id='loco_1', track='locoparking'), Mock(id='loco_2', track='locoparking')]

    # Tracks
    scenario.tracks = [
        Mock(id='collection', type='collection', length=100.0, fillfactor=0.8),
        Mock(id='retrofit', type='retrofit', length=80.0, fillfactor=0.9),
        Mock(id='retrofitted', type='retrofitted', length=120.0, fillfactor=0.8),
        Mock(id='parking_1', type='parking', length=200.0, fillfactor=0.7),
    ]

    # Routes
    scenario.routes = [
        Mock(from_location='collection', to_location='retrofit', time_minutes=2.0, path=['collection', 'retrofit']),
        Mock(from_location='retrofit', to_location='ws_1', time_minutes=3.0, path=['retrofit', 'ws_1']),
    ]

    # Trains
    scenario.trains = [
        Mock(train_id='train_1', wagons=[Mock(id='wagon_1', length=15.0), Mock(id='wagon_2', length=18.0)])
    ]

    # Process times
    scenario.process_times = Mock(wagon_retrofit_time=Mock(total_seconds=lambda: 600))

    # Priority strategy
    scenario.loco_priority_strategy = Mock(value='workshop_priority')

    return scenario
