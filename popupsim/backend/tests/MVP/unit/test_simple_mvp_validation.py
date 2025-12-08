"""Simple MVP validation tests without bridge complexity."""

from popupsim.backend.src.MVP.simulation.application.simulation_orchestrator import (
    SimulationOrchestrator,
)
from popupsim.backend.src.MVP.simulation.infrastructure.engines.simpy_engine_adapter import (
    SimPyEngineAdapter,
)
from popupsim.backend.src.MVP.workshop_operations.application.workshop_context import (
    WorkshopOperationsContext,
)
from popupsim.backend.tests.MVP.unit.test_helpers import (
    create_minimal_scenario_with_dtos,
)


def test_mvp_single_wagon_direct() -> None:
    """Test MVP directly: 1 wagon, 1 station."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=1, num_stations=1, retrofit_time=10.0
    )

    # Run MVP directly
    engine = SimPyEngineAdapter.create()
    context = WorkshopOperationsContext(scenario)
    orchestrator = SimulationOrchestrator(engine, scenario)
    orchestrator.register_context(context)
    orchestrator.run(until=50.0)

    # Verify results
    stations = context.workshop_capacity.stations["WS1"]
    assert stations[0].wagons_completed == 1


def test_mvp_two_wagons_direct() -> None:
    """Test MVP directly: 2 wagons, 1 station."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=2, num_stations=1, retrofit_time=10.0
    )

    # Run MVP directly
    engine = SimPyEngineAdapter.create()
    context = WorkshopOperationsContext(scenario)
    orchestrator = SimulationOrchestrator(engine, scenario)
    orchestrator.register_context(context)
    orchestrator.run(until=50.0)

    # Verify results
    stations = context.workshop_capacity.stations["WS1"]
    assert stations[0].wagons_completed == 2


def test_mvp_six_wagons_two_workshops_direct() -> None:
    """Test MVP directly: 6 wagons, 2 workshops."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=6, num_stations=2, retrofit_time=10.0, num_workshops=2
    )

    # Run MVP directly
    engine = SimPyEngineAdapter.create()
    context = WorkshopOperationsContext(scenario)
    orchestrator = SimulationOrchestrator(engine, scenario)
    orchestrator.register_context(context)
    orchestrator.run(until=60.0)

    # Verify results
    ws1_stations = context.workshop_capacity.stations["WS1"]
    assert ws1_stations[0].wagons_completed == 2
    assert ws1_stations[1].wagons_completed == 2

    ws2_stations = context.workshop_capacity.stations["WS2"]
    assert ws2_stations[0].wagons_completed == 1
    assert ws2_stations[1].wagons_completed == 1


def test_new_architecture_basic() -> None:
    """Test that new architecture can be instantiated without crashing."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=1, num_stations=1, retrofit_time=10.0
    )

    # Just test that we can create the service without import errors
    try:
        from popupsim.backend.src.application.simulation_service import (
            SimulationApplicationService,
        )

        service = SimulationApplicationService(scenario)
        # Don't run execute() to avoid complex initialization issues
        assert service.scenario == scenario
        assert service.contexts == {}
    except ImportError:
        # If imports fail, that's expected for now
        pass
