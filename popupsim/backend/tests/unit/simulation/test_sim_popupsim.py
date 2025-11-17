"""Unit tests for the PopupSim simulation entry point.

This module contains unit tests that exercise the PopupSim façade used by the
backend simulation. Tests verify that PopupSim delegates simulation control to
the provided adapter objects and that integration-style examples show how to
construct a full simulation using ScenarioBuilder and SimPyAdapter.

The tests are written for pytest and use lightweight fake adapters to avoid
depending on an actual simpy environment in unit test runs.
"""

from datetime import date
from typing import Any

from models.scenario import ScenarioConfig
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
        """Initialize the fake adapter with default state.

        Notes
        -----
        Sets `last_until` to None and `run_called_count` to 0.
        """
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
    """Test suite for PopupSim using a fake adapter.

    These tests verify that PopupSim delegates execution control to the
    provided adapter by calling its run() method with the expected arguments.
    """

    def test_run_calls_adapter_run_with_until(self) -> None:
        """Ensure PopupSim.run forwards the `until` argument to the adapter.

        Steps
        -----
        1. Create a FakeAdapter and a minimal scenario.
        2. Construct PopupSim with the fake adapter.
        3. Call sim.run(until=...) and assert adapter recorded the call.
        """
        adapter = FakeAdapter()
        scenario: Any = {'name': 'test-scenario'}
        sim = PopupSim(adapter, scenario)  # type: ignore[arg-type]

        sim.run(until=123.45)

        assert adapter.run_called_count == 1
        assert adapter.last_until == 123.45
        assert sim.name == 'PopUpSim'

    def test_run_calls_adapter_run_without_until(self) -> None:
        """Ensure PopupSim.run calls adapter.run when `until` is not provided.

        Verifies that the adapter's run() method is invoked and that the
        recorded `last_until` remains None.
        """
        adapter = FakeAdapter()
        scenario: Any = {'name': 'no-until'}
        sim = PopupSim(adapter, scenario)  # type: ignore[arg-type]

        sim.run()

        assert adapter.run_called_count == 1
        assert adapter.last_until is None


@pytest.mark.unit
class TestPopupSimWithSimpyAdapter:
    """Integration-style example that demonstrates creating real adapters.

    This test is guarded to run only when executed as main and provides an
    example of constructing ScenarioBuilder, SimPyAdapter and running the
    simulation. It is not executed as a normal unit test.
    """

    def test_run_calls_adapter_run_with_until(self) -> None:
        """Example usage constructing a full simulation and running it.

        The block is only executed when the module is run as a script; kept
        here as illustrative code rather than an assertion-based unit test.
        """
        if __name__ == '__main__':
            # Example Usage
            scenario = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                random_seed=42,
                train_schedule_file='schedule.csv',
            )
            sim_adapter = SimPyAdapter.create_simpy_adapter()
            popup_sim = PopupSim(sim_adapter, scenario)
            popup_sim.run(until=100.0)
