"""Test scaled simulation for dashboard postprocessing."""

import pytest

pytestmark = pytest.mark.skip(
    reason="Tests new architecture - moved to new_architecture folder"
)

# from popupsim.backend.src.application.simulation_service import (
#     SimulationApplicationService,
# )
# from popupsim.backend.tests.unit.test_helpers import create_minimal_scenario_with_dtos


@pytest.mark.xfail(reason="New architecture integration - needs completion")
def test_scaled_simulation_30_wagons() -> None:
    """Test scaled simulation: 30 wagons, 3 workshops."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=30, num_stations=2, retrofit_time=8.0, num_workshops=3
    )

    service = SimulationApplicationService(scenario)
    result = service.execute(until=300.0)

    # Basic validation
    assert result.duration >= 0.0
    assert isinstance(result.metrics, dict)
    assert len(service.contexts) > 0

    # Print metrics for dashboard development
    print(f"Simulation duration: {result.duration}")
    print(f"Success: {result.success}")
    print(f"Contexts: {list(service.contexts.keys())}")
    print(f"Metrics keys: {list(result.metrics.keys())}")

    # Check specific context metrics
    for context_name, metrics in result.metrics.items():
        print(
            f"{context_name}: {type(metrics)} - {len(metrics) if isinstance(metrics, dict) else 'N/A'} items"
        )


@pytest.mark.xfail(reason="New architecture integration - needs completion")
def test_scaled_simulation_postprocessing() -> None:
    """Test postprocessing of scaled simulation results."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=20, num_stations=2, retrofit_time=10.0, num_workshops=2
    )

    service = SimulationApplicationService(scenario)
    result = service.execute(until=200.0)

    # Extract and structure metrics for dashboard
    dashboard_data = {
        "simulation_info": {
            "duration": result.duration,
            "success": result.success,
            "contexts": list(service.contexts.keys()),
        },
        "raw_metrics": result.metrics,
        "processed_metrics": {},
    }

    # Process each context's metrics
    for context_name, metrics in result.metrics.items():
        if isinstance(metrics, dict):
            dashboard_data["processed_metrics"][context_name] = {
                "metric_count": len(metrics),
                "keys": list(metrics.keys()),
            }

    # Validate dashboard data structure
    assert "simulation_info" in dashboard_data
    assert "raw_metrics" in dashboard_data
    assert "processed_metrics" in dashboard_data

    print("Dashboard data structure:")
    print(f"  Simulation info: {dashboard_data['simulation_info']}")
    print(f"  Raw metrics contexts: {list(dashboard_data['raw_metrics'].keys())}")
    print(f"  Processed metrics: {dashboard_data['processed_metrics']}")


if __name__ == "__main__":
    test_scaled_simulation_30_wagons()
    print("\n" + "=" * 50 + "\n")
    test_scaled_simulation_postprocessing()
