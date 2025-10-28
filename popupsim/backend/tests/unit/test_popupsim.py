from typing import Any, Optional

import pytest

from configuration.model_route import Route  # type: ignore[import-not-found,import-untyped]
from configuration.model_routes import Routes  # type: ignore[import-not-found,import-untyped]
from configuration.model_wagon import Wagon  # type: ignore[import-not-found,import-untyped]
from simulation.scenariosim import ScenarioBuilder  # type: ignore[import-not-found,import-untyped]
from simulation.sim_adapter import SimPyAdapter  # type: ignore[import-not-found,import-untyped]
from src.simulation.popupsim import PopupSim  # type: ignore[import-not-found,import-untyped]


class FakeAdapter:
    last_until: Optional[float]
    run_called_count: int

    def __init__(self) -> None:
        self.last_until = None
        self.run_called_count = 0

    def run(self, until: Optional[float] = None) -> None:
        self.run_called_count += 1
        self.last_until = until


@pytest.mark.unit
class TestPopupSimWithFakeSim:
    """Test suite for PopupSim with fake simulation."""

    def test_run_calls_adapter_run_with_until(self) -> None:
        adapter = FakeAdapter()
        scenario: Any = {'name': 'test-scenario'}
        sim = PopupSim(adapter, scenario)  # type: ignore[arg-type]

        sim.run(until=123.45)

        assert adapter.run_called_count == 1
        assert adapter.last_until == 123.45
        assert sim.name == 'PopUpSim'

    def test_run_calls_adapter_run_without_until(self) -> None:
        adapter = FakeAdapter()
        scenario: Any = {'name': 'no-until'}
        sim = PopupSim(adapter, scenario)  # type: ignore[arg-type]

        sim.run()

        assert adapter.run_called_count == 1
        assert adapter.last_until is None


@pytest.mark.unit
class TestPopupSimWithSimpyAdapter:
    def test_run_calls_adapter_run_with_until(self) -> None:
        if __name__ == '__main__':
            # Example Data
            wagon1: Wagon = Wagon(wagon_id='W001', train_id='T001', length=15.5, is_loaded=True, needs_retrofit=False)
            wagon2: Wagon = Wagon(wagon_id='W001', train_id='T001', length=15.5, is_loaded=True, needs_retrofit=False)
            route = Route(
                route_id='TEST01',
                from_track='track1',
                to_track='track2',
                track_sequence=['track1', 'middle', 'track2'],
                distance_m=100.5,
                time_min=5,
            )

            # Example Usage
            scenario = ScenarioBuilder().add_wagon(wagon1).add_wagon(wagon2).add_routes(Routes(routes=[route])).build()

            sim_adapter = SimPyAdapter.create_simpy_adapter()
            popup_sim = PopupSim(sim_adapter, scenario)
            popup_sim.run(until=100.0)
