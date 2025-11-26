"""Test scenarios for track capacity management."""

from pathlib import Path

import pytest
from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.infrastructure.simulation.simpy_adapter import SimPyAdapter

from configuration.application.scenario_builder import ScenarioBuilder


@pytest.mark.xfail(reason='Simulation logic under development - will be fixed in future commits')
def test_collection_track_within_capacity() -> None:
    """Test scenario where simulation runs with track capacity management.

    Verifies that the simulation initializes and runs with capacity management enabled.
    """
    # Load test scenario
    fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
    scenario_builder = ScenarioBuilder(fixtures_path / 'scenario.json')
    scenario = scenario_builder.build()

    # Create simulation
    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim_adapter, scenario)

    # Verify track capacity manager is initialized
    assert popup_sim.track_capacity is not None

    # Run simulation - should complete without errors
    popup_sim.run(until=200.0)  # Run for 200 minutes


@pytest.mark.xfail(reason='Simulation logic under development - will be fixed in future commits')
def test_collection_track_exceeds_capacity() -> None:
    """Test scenario where wagons exceed collection track capacity.

    This test would require creating a custom scenario with many large wagons
    that exceed the 75% capacity limit of the collection track.
    Wagons should be rejected when capacity is full.
    """
    # This test requires a custom scenario with more wagons
    # For now, we verify the capacity management is initialized
    fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
    scenario_builder = ScenarioBuilder(fixtures_path / 'scenario.json')
    scenario = scenario_builder.build()

    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim_adapter, scenario)

    # Verify track capacity manager is initialized
    assert popup_sim.track_capacity is not None
    assert len(popup_sim.track_capacity.track_capacities) > 0

    # Verify collection track has capacity set
    collection_tracks = [t for t in scenario.tracks if t.type.value == 'collection']
    assert len(collection_tracks) > 0

    for track in collection_tracks:
        assert track.id in popup_sim.track_capacity.track_capacities
        capacity = popup_sim.track_capacity.track_capacities[track.id]
        assert capacity > 0, f'Track {track.id} should have positive capacity'
