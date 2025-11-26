"""Validation scenarios with precomputed expected results."""

from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.infrastructure.simulation.simpy_adapter import SimPyAdapter

from .test_helpers import create_minimal_scenario_with_dtos


def test_single_wagon_single_station() -> None:
    """Test 1 wagon, 1 station - validates state at each timestep."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    from .timeline_validator import validate_timeline_from_docstring

    validate_timeline_from_docstring(popup_sim, test_single_wagon_single_station)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 1


def test_two_wagons_one_station() -> None:
    """Test 2 wagons, 1 station - sequential processing."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=2, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    from .timeline_validator import validate_timeline_from_docstring

    validate_timeline_from_docstring(popup_sim, test_two_wagons_one_station)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 2


def test_two_wagons_two_stations() -> None:
    """Test 2 wagons, 2 stations - parallel processing."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=2, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    from .timeline_validator import validate_timeline_from_docstring

    validate_timeline_from_docstring(popup_sim, test_single_wagon_single_station)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 1
    assert stations[1].wagons_completed == 1


def test_four_wagons_two_stations() -> None:
    """Test 4 wagons, 2 stations - two batches."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=4, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    from .timeline_validator import validate_timeline_from_docstring

    validate_timeline_from_docstring(popup_sim, test_four_wagons_two_stations)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 2
    assert stations[1].wagons_completed == 2


def test_six_wagons_two_workshops() -> None:
    """Test 6 wagons, 2 workshops (WS1 and WS2), each with 2 stations."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=6, num_stations=2, retrofit_time=10.0, num_workshops=2)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=60.0)

    from .timeline_validator import validate_timeline_from_docstring

    validate_timeline_from_docstring(popup_sim, test_six_wagons_two_workshops)

    ws1_stations = popup_sim.workshop_capacity.stations['WS1']
    assert ws1_stations[0].wagons_completed == 2, f'WS1[0] expected 2, got {ws1_stations[0].wagons_completed}'
    assert ws1_stations[1].wagons_completed == 2, f'WS1[1] expected 2, got {ws1_stations[1].wagons_completed}'

    ws2_stations = popup_sim.workshop_capacity.stations['WS2']
    assert ws2_stations[0].wagons_completed == 1, f'WS2[0] expected 1, got {ws2_stations[0].wagons_completed}'
    assert ws2_stations[1].wagons_completed == 1, f'WS2[1] expected 1, got {ws2_stations[1].wagons_completed}'


def test_seven_wagons_two_workshops() -> None:
    """Test 7 wagons, 2 workshops - tests partial batch handling."""
    scenario = create_minimal_scenario_with_dtos(num_wagons=7, num_stations=2, retrofit_time=10.0, num_workshops=2)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=100.0)

    from .timeline_validator import validate_timeline_from_docstring

    validate_timeline_from_docstring(popup_sim, test_seven_wagons_two_workshops)

    ws1_stations = popup_sim.workshop_capacity.stations['WS1']
    ws1_total = sum(s.wagons_completed for s in ws1_stations)
    ws2_stations = popup_sim.workshop_capacity.stations['WS2']
    ws2_total = sum(s.wagons_completed for s in ws2_stations)

    # Current behavior: WS1=5, WS2=2 (not optimal but correct given current algorithm)
    assert ws1_total == 5, f'WS1 expected 5 wagons, got {ws1_total}'
    assert ws2_total == 2, f'WS2 expected 2 wagons, got {ws2_total}'

    # Verify all 7 wagons were processed
    processed_wagons = [w for w in popup_sim.wagons_queue if w.retrofit_start_time is not None]
    assert len(processed_wagons) == 7, f'Expected 7 wagons processed, got {len(processed_wagons)}'