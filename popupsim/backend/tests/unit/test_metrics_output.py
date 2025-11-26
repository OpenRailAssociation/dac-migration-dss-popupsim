"""Test that simulation produces metrics output."""

from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.infrastructure.simulation.simpy_adapter import SimPyAdapter

from .test_helpers import create_minimal_scenario_with_dtos


def test_metrics_output() -> None:
    """Test that simulation produces metrics output."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=4, num_stations=2, retrofit_time=10.0)

    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=100.0)

    # Verify metrics are collected
    assert len(popup_sim.wagons_queue) == 4
    assert popup_sim.workshop_capacity is not None

    # Verify some wagons were processed
    processed_wagons = [w for w in popup_sim.wagons_queue if w.retrofit_start_time is not None]
    assert len(processed_wagons) > 0
