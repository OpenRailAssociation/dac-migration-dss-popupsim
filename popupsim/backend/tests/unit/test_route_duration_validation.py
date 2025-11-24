"""Test route duration validation in timeline validator."""

import pytest
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter

from .test_validation_scenarios import create_minimal_scenario
from .timeline_validator import validate_timeline


def test_route_duration_validation() -> None:
    """Test that route durations are validated correctly.

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=4->5: loco[L1] MOVING retrofit->WS1
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)

    # This should pass - routes have 1.0 min duration
    validate_timeline(
        popup_sim,
        """
        t=0->1: loco[L1] MOVING parking->collection
        t=4->5: loco[L1] MOVING retrofit->WS1
    """,
    )


def test_route_duration_mismatch() -> None:
    """Test that incorrect route duration is caught."""
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)

    # This should fail - route duration is 1.0, not 2.0
    with pytest.raises(AssertionError, match=r'expected duration 2.0, got 1'):
        validate_timeline(
            popup_sim,
            """
            t=0->2: loco[L1] MOVING parking->collection
        """,
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
