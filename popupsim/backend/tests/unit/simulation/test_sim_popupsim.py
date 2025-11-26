"""Unit tests for the WorkshopOrchestrator simulation entry point.

This module contains unit tests that exercise the WorkshopOrchestrator façade used by the
backend simulation. Tests verify that WorkshopOrchestrator delegates simulation control to
the provided adapter objects and that integration-style examples show how to
construct a full simulation using ScenarioBuilder and SimPyAdapter.

The tests are written for pytest and use lightweight fake adapters to avoid
depending on an actual simpy environment in unit test runs.
"""

from pathlib import Path
from typing import Any

import pytest
from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.infrastructure.simulation.simpy_adapter import SimPyAdapter

from configuration.application.scenario_builder import ScenarioBuilder
from configuration.domain.models.scenario import Scenario


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

    def run_process(self, process, *args: Any) -> None:
        """Simulate adapter.run_process."""
        pass

    def create_store(self, capacity: int) -> 'FakeStore':  # noqa: ARG002
        """Simulate adapter.create_store."""
        return FakeStore()

    def create_resource(self, capacity: int) -> 'FakeResource':  # noqa: ARG002
        """Simulate adapter.create_resource."""
        return FakeResource()

    def create_event(self) -> 'FakeEvent':
        """Simulate adapter.create_event."""
        return FakeEvent()

    def current_time(self) -> float:
        """Simulate adapter.current_time."""
        return 0.0


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


class FakeResource:
    """Fake resource for testing."""

    def request(self) -> 'FakeRequest':
        """Fake request."""
        return FakeRequest()


class FakeRequest:
    """Fake request for testing."""

    pass


class FakeEvent:
    """Fake event for testing."""

    def succeed(self) -> None:
        """Fake succeed."""
        pass


@pytest.mark.unit
class TestPopupSimWithFakeSim:
    """Test suite for WorkshopOrchestrator using a fake adapter."""

    def test_run_calls_adapter_run_without_until(self) -> None:
        """Ensure WorkshopOrchestrator.run calls adapter.run when `until` is not provided."""
        from datetime import UTC
        from datetime import datetime

        from workshop_operations.domain.aggregates.train import Train
        from workshop_operations.domain.entities.locomotive import Locomotive
        from workshop_operations.domain.entities.track import Track
        from workshop_operations.domain.entities.track import TrackType
        from workshop_operations.domain.entities.wagon import Wagon
        from workshop_operations.domain.entities.workshop import Workshop

        from configuration.domain.models.topology import Topology

        adapter = FakeAdapter()

        topology = Topology({'edges': [{'edge_id': 'e1', 'from_node': 'n1', 'to_node': 'n2', 'length': 100.0}]})
        track = Track(id='t1', name='Track 1', type=TrackType.COLLECTION, edges=['e1'])
        retrofitted_track = Track(id='t2', name='Track 2', type=TrackType.RETROFITTED, edges=['e1'])
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
            'tracks': [track, retrofitted_track],
            'trains': [train],
            'topology': topology,
        }

        scenario = Scenario(**scenario_data)
        sim = WorkshopOrchestrator(adapter, scenario)  # type: ignore[arg-type]

        sim.run()

        assert adapter.run_called_count == 1
        assert adapter.last_until == 1440.0  # 1 day in minutes


@pytest.mark.unit
class TestPopupSimWithSimpyAdapter:
    """Integration-style example that demonstrates creating real adapters."""

    def test_run_calls_adapter_run_with_until(self) -> None:
        """Example usage constructing a full simulation and running it."""
        from datetime import UTC
        from datetime import datetime

        from workshop_operations.domain.aggregates.train import Train
        from workshop_operations.domain.entities.locomotive import Locomotive
        from workshop_operations.domain.entities.track import Track
        from workshop_operations.domain.entities.track import TrackType
        from workshop_operations.domain.entities.wagon import Wagon
        from workshop_operations.domain.entities.workshop import Workshop
        from workshop_operations.domain.value_objects.route import Route
        from workshop_operations.domain.value_objects.routes import Routes

        from configuration.domain.models.process_times import ProcessTimes
        from configuration.domain.models.topology import Topology

        topology = Topology({'edges': [{'edge_id': 'e1', 'from_node': 'n1', 'to_node': 'n2', 'length': 100.0}]})
        process_times = ProcessTimes()
        route = Route(route_id='r1', from_track='t1', to_track='t2', path=['t1', 't2'], duration=10.0)
        routes = Routes(routes=[route])
        track = Track(id='t1', name='Track 1', type=TrackType.COLLECTION, edges=['e1'])
        retrofitted_track = Track(id='t2', name='Track 2', type=TrackType.RETROFITTED, edges=['e1'])
        loco = Locomotive(
            locomotive_id='L1',
            name='Loco 1',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 2, tzinfo=UTC),
            track_id='t1',
        )
        workshop = Workshop(
            workshop_id='W1', start_date='2024-01-01T00:00:00Z', end_date='2024-01-02T00:00:00Z', track_id='t1'
        )
        wagon = Wagon(wagon_id='W1', length=20.0, is_loaded=False, needs_retrofit=True)
        train = Train(train_id='T1', arrival_time=datetime(2024, 1, 1, 8, 0, tzinfo=UTC), wagons=[wagon])

        scenario_data = {
            'scenario_id': 'test_scenario',
            'start_date': datetime(2024, 1, 1, tzinfo=UTC),
            'end_date': datetime(2024, 1, 2, tzinfo=UTC),
            'locomotives': [loco],
            'workshops': [workshop],
            'tracks': [track, retrofitted_track],
            'trains': [train],
            'topology': topology,
            'process_times': process_times,
            'routes': routes,
        }

        scenario = Scenario(**scenario_data)
        sim_adapter = SimPyAdapter.create_simpy_adapter()
        popup_sim = WorkshopOrchestrator(sim_adapter, scenario)
        popup_sim.run(until=100.0)


class TestPopupSimWithScenarioBuilder:
    """Integration-style example using ScenarioBuilder."""

    def test_popsim_with_scenario_from_fixture(self, test_scenario_json_path: Path) -> None:
        """Test WorkshopOrchestrator with scenario loaded from fixture file.

        Parameters
        ----------
        test_scenario_json_path : Path
            Path to scenario JSON fixture file.
        """
        scenario = ScenarioBuilder(test_scenario_json_path).build()
        sim_adapter = SimPyAdapter.create_simpy_adapter()
        popup_sim = WorkshopOrchestrator(sim_adapter, scenario)
        popup_sim.run()
