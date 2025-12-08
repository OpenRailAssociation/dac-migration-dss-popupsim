"""Tests for Simulation Context architecture."""

import pytest

from popupsim.backend.src.MVP.simulation.application.simulation_orchestrator import (
    SimulationOrchestrator,
)
from popupsim.backend.src.MVP.simulation.domain.aggregates.simulation_session import (
    SimulationSession,
)
from popupsim.backend.src.MVP.simulation.domain.ports.context_port import (
    BoundedContextPort,
)
from popupsim.backend.src.MVP.simulation.domain.ports.simulation_engine_port import (
    SimulationEnginePort,
)


class MockEngine(SimulationEnginePort):
    """Mock simulation engine for testing."""

    def __init__(self) -> None:
        self._time = 0.0
        self._running = False

    def current_time(self) -> float:
        return self._time

    def schedule_process(self, process: object) -> object:
        return process

    def create_resource(self, capacity: int) -> object:
        return object()

    def create_store(self, capacity: int | None = None) -> object:
        return object()

    def delay(self, duration: float) -> object:
        self._time += duration
        return object()

    def run(self, until: float | None = None) -> None:
        self._running = True
        if until:
            self._time = until

    def create_event(self) -> object:
        return object()


class MockContext:
    """Mock bounded context for testing."""

    def __init__(self) -> None:
        self.initialized = False
        self.started = False
        self.metrics_called = False

    def initialize(self, simulation_session: object) -> None:
        self.initialized = True

    def start_processes(self) -> None:
        self.started = True

    def get_metrics(self) -> dict[str, object]:
        self.metrics_called = True
        return {"test_metric": 42}

    def cleanup(self) -> None:
        pass


def test_simulation_engine_port_is_abstract() -> None:
    """Test that SimulationEnginePort is abstract."""
    with pytest.raises(TypeError):
        SimulationEnginePort()  # type: ignore[abstract]


def test_mock_engine_implements_port() -> None:
    """Test that MockEngine implements SimulationEnginePort."""
    engine = MockEngine()
    assert isinstance(engine, SimulationEnginePort)
    assert engine.current_time() == 0.0


def test_simulation_session_creation() -> None:
    """Test SimulationSession creation."""
    from popupsim.backend.src.MVP.configuration.domain.models.scenario import Scenario

    engine = MockEngine()
    scenario = Scenario(
        id="test",
        start_date="2025-01-01",
        end_date="2025-01-02",
    )
    session = SimulationSession(scenario, engine)

    assert session.scenario == scenario
    assert session.engine == engine
    assert not session.is_running


def test_simulation_session_lifecycle() -> None:
    """Test SimulationSession start/stop."""
    from popupsim.backend.src.MVP.configuration.domain.models.scenario import Scenario

    engine = MockEngine()
    scenario = Scenario(
        id="test",
        start_date="2025-01-01",
        end_date="2025-01-02",
    )
    session = SimulationSession(scenario, engine)

    session.start()
    assert session.is_running

    session.stop()
    assert not session.is_running


def test_simulation_orchestrator_creation() -> None:
    """Test SimulationOrchestrator creation."""
    from popupsim.backend.src.MVP.configuration.domain.models.scenario import Scenario

    engine = MockEngine()
    scenario = Scenario(
        id="test",
        start_date="2025-01-01",
        end_date="2025-01-02",
    )
    orchestrator = SimulationOrchestrator(engine, scenario)

    assert orchestrator.engine == engine
    assert orchestrator.scenario == scenario
    assert len(orchestrator.contexts) == 0


def test_orchestrator_register_context() -> None:
    """Test registering a context with orchestrator."""
    from popupsim.backend.src.MVP.configuration.domain.models.scenario import Scenario

    engine = MockEngine()
    scenario = Scenario(
        id="test",
        start_date="2025-01-01",
        end_date="2025-01-02",
    )
    orchestrator = SimulationOrchestrator(engine, scenario)
    context = MockContext()

    orchestrator.register_context(context, "test_context")

    assert "test_context" in orchestrator.contexts
    assert context.initialized


def test_orchestrator_run_simulation() -> None:
    """Test running simulation with orchestrator."""
    from popupsim.backend.src.MVP.configuration.domain.models.scenario import Scenario

    engine = MockEngine()
    scenario = Scenario(
        id="test",
        start_date="2025-01-01",
        end_date="2025-01-02",
    )
    orchestrator = SimulationOrchestrator(engine, scenario)
    context = MockContext()

    orchestrator.register_context(context, "test_context")
    results = orchestrator.run(until=100.0)

    assert context.started
    assert context.metrics_called
    assert "test_context" in results
    assert results["test_context"]["test_metric"] == 42


def test_orchestrator_multiple_contexts() -> None:
    """Test orchestrator with multiple contexts."""
    from popupsim.backend.src.MVP.configuration.domain.models.scenario import Scenario

    engine = MockEngine()
    scenario = Scenario(
        id="test",
        start_date="2025-01-01",
        end_date="2025-01-02",
    )
    orchestrator = SimulationOrchestrator(engine, scenario)

    context1 = MockContext()
    context2 = MockContext()

    orchestrator.register_context(context1, "context1")
    orchestrator.register_context(context2, "context2")

    results = orchestrator.run(until=100.0)

    assert context1.initialized and context1.started
    assert context2.initialized and context2.started
    assert "context1" in results
    assert "context2" in results


def test_bounded_context_port_protocol() -> None:
    """Test that MockContext satisfies BoundedContextPort protocol."""
    context = MockContext()

    # Protocol check - should not raise
    def accepts_context(ctx: BoundedContextPort) -> None:
        pass

    accepts_context(context)
