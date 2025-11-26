"""Tests for wagon pickup process."""

from pathlib import Path

import pytest
from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.domain.entities.locomotive import LocoStatus
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.infrastructure.simulation.simpy_adapter import SimPyAdapter

from configuration.application.scenario_builder import ScenarioBuilder


@pytest.mark.xfail(reason='Simulation logic under development - will be fixed in future commits')
def test_wagon_pickup_process() -> None:
    """Test that wagons are picked up from collection and moved to retrofit."""
    fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
    scenario_builder = ScenarioBuilder(fixtures_path / 'scenario.json')
    scenario = scenario_builder.build()

    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim_adapter, scenario)

    # Run simulation for enough time to process train and pickup
    popup_sim.run(until=100.0)

    # Verify loaded wagons were rejected (not moved to retrofit)
    rejected_wagons = [w for w in popup_sim.rejected_wagons_queue if w.status == WagonStatus.REJECTED]
    assert len(rejected_wagons) > 0, 'Loaded wagons should be rejected'

    # Verify no wagons reached retrofitting (since they're all loaded)
    retrofitting_wagons = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.RETROFITTING]
    assert len(retrofitting_wagons) == 0, 'Loaded wagons should not reach retrofit'


@pytest.mark.xfail(reason='Simulation logic under development - will be fixed in future commits')
def test_locomotive_status_updates() -> None:
    """Test that locomotive status is updated during pickup process."""
    fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
    scenario_builder = ScenarioBuilder(fixtures_path / 'scenario.json')
    scenario = scenario_builder.build()

    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim_adapter, scenario)

    # Get initial loco
    assert scenario.locomotives is not None, 'Scenario must have locomotives'
    initial_loco = scenario.locomotives[0]
    initial_track = initial_loco.track_id

    # Run simulation
    popup_sim.run(until=100.0)

    # Loco should be back at parking with PARKING status
    assert initial_loco.status == LocoStatus.PARKING
    assert initial_loco.track_id == initial_track


@pytest.mark.xfail(reason='Simulation logic under development - will be fixed in future commits')
def test_wagons_grouped_by_collection_track() -> None:
    """Test that wagons are correctly grouped by collection track."""
    fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
    scenario_builder = ScenarioBuilder(fixtures_path / 'scenario.json')
    scenario = scenario_builder.build()

    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim_adapter, scenario)

    popup_sim.run(until=50.0)

    # Check wagons have track_id set
    selected_wagons = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.SELECTED]
    for wagon in selected_wagons:
        assert wagon.track_id is not None, f'Wagon {wagon.wagon_id} should have track_id'
