"""Unit tests for CouplingService."""

from datetime import timedelta
from unittest.mock import Mock

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.coupling_service import CouplingService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


@pytest.fixture
def process_times() -> Mock:
    """Create mock process times."""
    times = Mock()
    times.screw_coupling_time = timedelta(minutes=2.0)
    times.screw_decoupling_time = timedelta(minutes=2.0)
    times.dac_coupling_time = timedelta(minutes=1.0)
    times.dac_decoupling_time = timedelta(minutes=1.0)

    # Mock the get_coupling_ticks and get_decoupling_ticks methods
    def get_coupling_ticks(coupler_type: str) -> float:
        if coupler_type.upper() == 'DAC':
            return 1.0
        return 2.0

    def get_decoupling_ticks(coupler_type: str) -> float:
        if coupler_type.upper() == 'DAC':
            return 1.0
        return 2.0

    times.get_coupling_ticks = get_coupling_ticks
    times.get_decoupling_ticks = get_decoupling_ticks

    return times


@pytest.fixture
def coupling_service(process_times: Mock) -> CouplingService:
    """Create coupling service."""
    return CouplingService(process_times)


@pytest.fixture
def screw_wagons() -> list[Wagon]:
    """Create wagons with SCREW couplers."""
    return [
        Wagon('W1', 15.0, Coupler(CouplerType.SCREW, 'A'), Coupler(CouplerType.SCREW, 'B')),
        Wagon('W2', 15.0, Coupler(CouplerType.SCREW, 'A'), Coupler(CouplerType.SCREW, 'B')),
        Wagon('W3', 15.0, Coupler(CouplerType.SCREW, 'A'), Coupler(CouplerType.SCREW, 'B')),
    ]


@pytest.fixture
def dac_wagons() -> list[Wagon]:
    """Create wagons with DAC couplers."""
    return [
        Wagon('W1', 15.0, Coupler(CouplerType.DAC, 'A'), Coupler(CouplerType.DAC, 'B')),
        Wagon('W2', 15.0, Coupler(CouplerType.DAC, 'A'), Coupler(CouplerType.DAC, 'B')),
        Wagon('W3', 15.0, Coupler(CouplerType.DAC, 'A'), Coupler(CouplerType.DAC, 'B')),
    ]


def test_rake_coupling_time_single_wagon(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Single wagon has 0 couplings."""
    time = coupling_service.get_rake_coupling_time([screw_wagons[0]])
    assert time == 0.0


def test_rake_coupling_time_two_screw_wagons(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Two SCREW wagons have 1 coupling = 2 minutes."""
    time = coupling_service.get_rake_coupling_time(screw_wagons[:2])
    assert time == 2.0


def test_rake_coupling_time_three_screw_wagons(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Three SCREW wagons have 2 couplings = 4 minutes."""
    time = coupling_service.get_rake_coupling_time(screw_wagons)
    assert time == 4.0


def test_rake_coupling_time_two_dac_wagons(coupling_service: CouplingService, dac_wagons: list[Wagon]) -> None:
    """Two DAC wagons have 1 coupling = 1 minute."""
    time = coupling_service.get_rake_coupling_time(dac_wagons[:2])
    assert time == 1.0


def test_rake_coupling_time_three_dac_wagons(coupling_service: CouplingService, dac_wagons: list[Wagon]) -> None:
    """Three DAC wagons have 2 couplings = 2 minutes."""
    time = coupling_service.get_rake_coupling_time(dac_wagons)
    assert time == 2.0


def test_rake_decoupling_time_single_wagon(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Single wagon has 0 decouplings."""
    time = coupling_service.get_rake_decoupling_time([screw_wagons[0]])
    assert time == 0.0


def test_rake_decoupling_time_two_screw_wagons(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Two SCREW wagons have 1 decoupling = 2 minutes."""
    time = coupling_service.get_rake_decoupling_time(screw_wagons[:2])
    assert time == 2.0


def test_rake_decoupling_time_three_dac_wagons(coupling_service: CouplingService, dac_wagons: list[Wagon]) -> None:
    """Three DAC wagons have 2 decouplings = 2 minutes."""
    time = coupling_service.get_rake_decoupling_time(dac_wagons)
    assert time == 2.0


def test_loco_coupling_time_screw_wagons(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Loco coupling to SCREW wagons = 2 minutes."""
    time = coupling_service.get_loco_coupling_time(screw_wagons)
    assert time == 2.0


def test_loco_coupling_time_dac_wagons(coupling_service: CouplingService, dac_wagons: list[Wagon]) -> None:
    """Loco coupling to DAC wagons = 1 minute."""
    time = coupling_service.get_loco_coupling_time(dac_wagons)
    assert time == 1.0


def test_loco_coupling_time_empty_list(coupling_service: CouplingService) -> None:
    """Empty wagon list returns 0."""
    time = coupling_service.get_loco_coupling_time([])
    assert time == 0.0


def test_loco_decoupling_time_screw_wagons(coupling_service: CouplingService, screw_wagons: list[Wagon]) -> None:
    """Loco decoupling from SCREW wagons = 2 minutes."""
    time = coupling_service.get_loco_decoupling_time(screw_wagons)
    assert time == 2.0


def test_loco_decoupling_time_dac_wagons(coupling_service: CouplingService, dac_wagons: list[Wagon]) -> None:
    """Loco decoupling from DAC wagons = 1 minute."""
    time = coupling_service.get_loco_decoupling_time(dac_wagons)
    assert time == 1.0


def test_loco_decoupling_time_empty_list(coupling_service: CouplingService) -> None:
    """Empty wagon list returns 0."""
    time = coupling_service.get_loco_decoupling_time([])
    assert time == 0.0
