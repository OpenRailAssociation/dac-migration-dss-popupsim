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


@pytest.mark.unit
class TestPopupSimWithFakeSim:
    """Test suite for PopupSim using a fake adapter."""

    def test_run_calls_adapter_run_without_until(self) -> None:
        """Ensure PopupSim.run calls adapter.run when `until` is not provided."""
        adapter = FakeAdapter()
        scenario_data = {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
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
