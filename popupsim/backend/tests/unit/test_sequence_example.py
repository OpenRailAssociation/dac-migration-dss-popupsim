"""Example test using declarative sequence validation."""

import pytest
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter
from .test_validation_scenarios import create_minimal_scenario
from .sequence_validator import validate_sequence


def test_single_wagon_declarative() -> None:
    """Test single wagon with declarative sequence validation.
    
    SEQUENCE:
    wagon[W01] retrofit_start=5.0 retrofit_end=15.0 track=retrofitted
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    validate_sequence(test_single_wagon_declarative.__doc__, popup_sim)


def test_two_wagons_declarative() -> None:
    """Test two wagons sequential processing.
    
    SEQUENCE:
    wagon[W01] retrofit_start=5.0 retrofit_end=15.0
    wagon[W02] retrofit_start=20.0 retrofit_end=30.0
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    validate_sequence(test_two_wagons_declarative.__doc__, popup_sim)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
