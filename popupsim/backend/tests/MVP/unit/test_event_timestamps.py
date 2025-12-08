"""Test to check if events have timestamps."""

import pytest

pytestmark = pytest.mark.skip(
    reason="Tests new architecture - moved to new_architecture folder"
)

# from popupsim.backend.src.application.simulation_service import (
#     SimulationApplicationService,
# )
# from popupsim.backend.tests.unit.test_helpers import create_minimal_scenario_with_dtos


@pytest.mark.xfail(
    reason="New architecture integration - analytics context needs completion"
)
def test_event_timestamps() -> None:
    """Check if collected events have timestamps."""
    scenario = create_minimal_scenario_with_dtos(
        num_wagons=3, num_stations=1, retrofit_time=5.0
    )
    service = SimulationApplicationService(scenario)
    result = service.execute(until=30.0)

    # Get analytics context
    analytics = service.contexts.get("analytics")
    assert analytics is not None

    collector = analytics.event_collector
    print(f"Events collected: {len(collector.events)}")

    # Check first few events
    for i, event in enumerate(collector.events[:3]):
        print(f"\nEvent {i}: {type(event).__name__}")
        attrs = [attr for attr in dir(event) if not attr.startswith("_")]
        print(f"  Attributes: {attrs}")

        # Check for timestamp-like attributes
        for attr in attrs:
            value = getattr(event, attr)
            if "time" in attr.lower():
                print(f"  {attr}: {value}")

    # Check if we can get simulation time from engine
    if hasattr(service, "engine"):
        print(f"\nSimulation engine time: {service.engine.now}")

    assert len(collector.events) > 0
