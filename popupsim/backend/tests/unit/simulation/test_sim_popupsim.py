"""Unit tests for the PopupSim simulation entry point.

This module contains unit tests that exercise the PopupSim façade used by the
backend simulation. Tests verify that PopupSim delegates simulation control to
the provided adapter objects and that integration-style examples show how to
construct a full simulation using ScenarioBuilder and SimPyAdapter.

The tests are written for pytest and use lightweight fake adapters to avoid
depending on an actual simpy environment in unit test runs.
"""

from datetime import date
from pathlib import Path

from builders.scenario_builder import ScenarioBuilder
from models.scenario import Scenario
import pytest
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter


class FakeAdapter:
    """Lightweight fake adapter used in tests to observe run() calls.

    Attributes
    ----------
    last_until : float | None
        The last `until` value passed to run().
    run_called_count : int
        Number of times run() was called.
    """

    last_until: float | None
    run_called_count: int

    def __init__(self) -> None:
        """Initialize the fake adapter with default state."""
        self.last_until = None
        self.run_called_count = 0

    def run(self, until: float | None = None) -> None:
        """Simulate adapter.run by recording the call.

        Parameters
        ----------
        until : float | None, optional
            Time until which the adapter would run the simulation.
        """
        self.run_called_count += 1
        self.last_until = until

    def run_process(self, process, *args) -> None:
        """Simulate adapter.run_process."""
        pass

    def create_store(self, capacity: int) -> 'FakeStore':
        """Simulate adapter.create_store."""
        return FakeStore()


class FakeStore:
    """Fake store for testing."""
    def put(self, item: object) -> None:
        """Fake put."""
        pass

    def get(self) -> None:
        """Fake get."""
        return None

    def current_time(self) -> float:
        """Simulate adapter.current_time."""
        return 0.0


@pytest.mark.unit
class TestPopupSimWithFakeSim:
    """Test suite for PopupSim using a fake adapter."""

    def test_run_calls_adapter_run_without_until(self) -> None:
        """Ensure PopupSim.run calls adapter.run when `until` is not provided."""
        from datetime import UTC
        from datetime import datetime

        from models.locomotive import Locomotive
        from models.topology import Topology
        from models.track import Track
        from models.track import TrackType
        from models.train import Train
        from models.wagon import Wagon
        from models.workshop import Workshop

        adapter = FakeAdapter()

        topology = Topology({'edges': [{'edge_id': 'e1', 'from_node': 'n1', 'to_node': 'n2', 'length': 100.0}]})
        track = Track(id='t1', name='Track 1', type=TrackType.COLLECTION, edges=['e1'])
        loco = Locomotive(
            locomotive_id='L1',
            name='Loco 1',
            start_date=datetime(2024, 1, 15, tzinfo=UTC),
            end_date=datetime(2024, 1, 16, tzinfo=UTC),
            track_id='t1',
        )
        workshop = Workshop(
            workshop_id='W1', start_date='2024-01-15T00:00:00Z', end_date='2024-01-16T00:00:00Z', track_id='t1'
        )
        wagon = Wagon(wagon_id='W1', length=20.0, is_loaded=False, needs_retrofit=True)
        train = Train(train_id='T1', arrival_time=datetime(2024, 1, 15, 8, 0, tzinfo=UTC), wagons=[wagon])

        scenario_data = {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'locomotives': [loco],
            'workshops': [workshop],
            'tracks': [track],
            'trains': [train],
            'topology': topology,
        }

        scenario = Scenario(**scenario_data)
        sim = PopupSim(adapter, scenario)  # type: ignore[arg-type]

        sim.run()

        assert adapter.run_called_count == 1
        assert adapter.last_until == 1440.0  # 1 day in minutes


@pytest.mark.unit
class TestPopupSimWithSimpyAdapter:
    """Integration-style example that demonstrates creating real adapters."""

    def test_run_calls_adapter_run_with_until(self) -> None:
        """Example usage constructing a full simulation and running it."""
        if __name__ == '__main__':
            scenario = Scenario(
                scenario_id='test_scenario',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                random_seed=42,
                train_schedule_file='schedule.csv',
            )
            sim_adapter = SimPyAdapter.create_simpy_adapter()
            popup_sim = PopupSim(sim_adapter, scenario)
            popup_sim.run(until=100.0)


class TestPopupSimWithScenarioBuilder:
    """Integration-style example using ScenarioBuilder."""

    def test_popsim_with_scenario_from_fixture(self, test_scenario_json_path: Path) -> None:
        """Test PopupSim with scenario loaded from fixture file.

        Parameters
        ----------
        test_scenario_json_path : Path
            Path to scenario JSON fixture file.
        """
        scenario = ScenarioBuilder(test_scenario_json_path).build()
        sim_adapter = SimPyAdapter.create_simpy_adapter()
        popup_sim = PopupSim(sim_adapter, scenario)
        popup_sim.run()
