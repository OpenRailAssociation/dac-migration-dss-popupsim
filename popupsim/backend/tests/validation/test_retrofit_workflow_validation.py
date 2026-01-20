"""Validation tests for retrofit workflow context."""

from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
import simpy

from .scenario_builder import create_minimal_scenario


def test_context_basic_initialization() -> None:
    """Test that retrofit workflow context initializes correctly with minimal scenario."""
    env = simpy.Environment()
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Verify basic initialization
    assert context.workshops is not None
    assert context.locomotives is not None
    assert context.event_collector is not None
    assert context.locomotive_manager is not None


def test_context_with_multiple_workshops() -> None:
    """Test retrofit workflow context with multiple workshops."""
    env = simpy.Environment()
    scenario = create_minimal_scenario(num_wagons=4, num_stations=2, num_workshops=2)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Should have 2 workshops
    assert len(context.workshops) == 2
    assert 'WS1' in context.workshops
    assert 'WS2' in context.workshops

    # Each workshop should have 2 stations
    for workshop in context.workshops.values():
        assert workshop.capacity == 2


def test_context_simulation_run() -> None:
    """Test that retrofit workflow context can run a basic simulation."""
    env = simpy.Environment()
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=5.0)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()
    context.start_processes()

    # Run brief simulation
    env.run(until=10.0)

    # Should complete without errors
    metrics = context.get_metrics()
    assert 'workshops' in metrics
    assert 'locomotives' in metrics


def test_context_metrics_collection() -> None:
    """Test that retrofit workflow context collects metrics correctly."""
    env = simpy.Environment()
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    metrics = context.get_metrics()

    # Should have metrics for all major components
    assert isinstance(metrics, dict)
    assert 'workshops' in metrics or 'locomotives' in metrics or 'tracks' in metrics

    # Status should be available
    status = context.get_status()
    assert status['status'] == 'ready'
    assert status['workshops'] >= 1
    assert status['locomotives'] >= 1


def test_context_event_export() -> None:
    """Test that retrofit workflow context can export events."""
    import tempfile

    env = simpy.Environment()
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()

    # Should be able to export events without error
    with tempfile.TemporaryDirectory() as temp_dir:
        context.export_events(temp_dir)
        # No exception means success


def test_context_cleanup() -> None:
    """Test that retrofit workflow context cleans up properly."""
    env = simpy.Environment()
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1)

    context = RetrofitWorkshopContext(env, scenario)
    context.initialize()
    context.start_processes()

    # Should cleanup without error
    context.cleanup()
