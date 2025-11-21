"""Example test using generic timeline validation."""

import pytest
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter
from .test_validation_scenarios import create_minimal_scenario
from .timeline_validator import validate_timeline


def test_generic_timeline() -> None:
    """Test with generic resource timeline format.
    
    TIMELINE:
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=15: wagon[W01] RETROFITTED retrofit_end track=retrofitted
    t=0: loco[L1] PARKING
    t=3: loco[L1] PARKING
    t=18: loco[L1] PARKING
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    validate_timeline(popup_sim, """
        t=5: wagon[W01] RETROFITTING retrofit_start
        t=15: wagon[W01] RETROFITTED retrofit_end track=retrofitted
        t=0: loco[L1] PARKING
        t=3: loco[L1] PARKING
        t=18: loco[L1] PARKING
    """)


def test_two_wagons_timeline() -> None:
    """Test two wagons with timeline validation.
    
    TIMELINE:
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=20: wagon[W02] RETROFITTING retrofit_start
    t=30: wagon[W02] RETROFITTED retrofit_end
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    validate_timeline(popup_sim, """
        t=5: wagon[W01] RETROFITTING retrofit_start
        t=15: wagon[W01] RETROFITTED retrofit_end
        t=20: wagon[W02] RETROFITTING retrofit_start
        t=30: wagon[W02] RETROFITTED retrofit_end
    """)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
