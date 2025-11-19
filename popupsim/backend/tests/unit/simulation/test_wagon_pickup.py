"""Tests for wagon pickup process."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from builders.scenario_builder import ScenarioBuilder
from models.locomotive import LocoStatus
from models.wagon import WagonStatus
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter


def test_wagon_pickup_process() -> None:
    """Test that wagons are picked up from collection and moved to retrofit."""
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures"
    scenario_builder = ScenarioBuilder(fixtures_path / "scenario.json")
    scenario = scenario_builder.build()
    
    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim_adapter, scenario)
    
    # Run simulation for enough time to process train and pickup
    popup_sim.run(until=100.0)
    
    # Verify wagons were moved to retrofit
    retrofitting_wagons = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.RETROFITTING]
    assert len(retrofitting_wagons) > 0, "Should have wagons in retrofit"


def test_locomotive_status_updates() -> None:
    """Test that locomotive status is updated during pickup process."""
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures"
    scenario_builder = ScenarioBuilder(fixtures_path / "scenario.json")
    scenario = scenario_builder.build()
    
    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim_adapter, scenario)
    
    # Get initial loco
    initial_loco = scenario.locomotives[0]
    initial_track = initial_loco.track_id
    
    # Run simulation
    popup_sim.run(until=100.0)
    
    # Loco should be back at parking with PARKING status
    assert initial_loco.status == LocoStatus.PARKING
    assert initial_loco.track_id == initial_track


def test_wagons_grouped_by_collection_track() -> None:
    """Test that wagons are correctly grouped by collection track."""
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures"
    scenario_builder = ScenarioBuilder(fixtures_path / "scenario.json")
    scenario = scenario_builder.build()
    
    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim_adapter, scenario)
    
    popup_sim.run(until=50.0)
    
    # Check wagons have track_id set
    selected_wagons = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.SELECTED]
    for wagon in selected_wagons:
        assert wagon.track_id is not None, f"Wagon {wagon.wagon_id} should have track_id"
