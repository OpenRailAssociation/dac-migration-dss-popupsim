"""Test scenario builder for validation tests."""

from .scenario_builder import create_minimal_scenario


def test_create_single_wagon_scenario() -> None:
    """Test creating scenario with 1 wagon, 1 station."""
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)

    assert scenario.id == 'validation_test'
    assert len(scenario.workshops) == 1  # type: ignore[arg-type]
    assert scenario.workshops[0].retrofit_stations == 1  # type: ignore[index]
    assert scenario.process_times.wagon_retrofit_time.total_seconds() == 600.0
    assert len(scenario.locomotives) == 1  # type: ignore[arg-type]


def test_create_two_workshop_scenario() -> None:
    """Test creating scenario with 2 workshops."""
    scenario = create_minimal_scenario(num_wagons=6, num_stations=2, retrofit_time=10.0, num_workshops=2)

    assert len(scenario.workshops) == 2  # type: ignore[arg-type]
    assert scenario.workshops[0].id == 'WS1'  # type: ignore[index]
    assert scenario.workshops[1].id == 'WS2'  # type: ignore[index]
    assert all(w.retrofit_stations == 2 for w in scenario.workshops)


def test_routes_created_for_workshops() -> None:
    """Test that routes are created for each workshop."""
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, num_workshops=2)

    route_ids = [r.id for r in scenario.routes]
    assert 'retrofit_WS1' in route_ids
    assert 'retrofit_WS2' in route_ids
