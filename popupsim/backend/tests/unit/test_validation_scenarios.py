"""Validation scenarios with precomputed expected results."""

from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.infrastructure.simulation.simpy_adapter import SimPyAdapter

from .test_helpers import create_minimal_scenario_with_dtos
from .timeline_validator import validate_timeline_from_docstring


def test_single_wagon_single_station() -> None:
    """Test 1 wagon, 1 station - validates state at each timestep.

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->parking
    t=3->4: loco[L1] MOVING parking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->parking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING parking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->parking
    t=18->19: loco[L1] MOVING parking->retrofitted
    t=19->20: loco[L1] MOVING retrofitted->parking
    t=20: wagon[W01] PARKING track=parking
    """
    scenario = create_minimal_scenario_with_dtos(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    validate_timeline_from_docstring(popup_sim, test_single_wagon_single_station)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 1


def test_two_wagons_one_station() -> None:
    """Test 2 wagons, 1 station - sequential processing.

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->parking
    t=3->4: loco[L1] MOVING parking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->parking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING parking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->parking
    t=18->19: loco[L1] MOVING parking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20: wagon[W02] RETROFITTING retrofit_start
    t=20->21: loco[L1] MOVING WS1->parking
    t=30: wagon[W02] RETROFITTED retrofit_end
    t=30->31: loco[L1] MOVING parking->WS1
    t=31->32: loco[L1] MOVING WS1->retrofitted
    t=32: wagon[W02] RETROFITTED track=retrofitted
    t=32->33: loco[L1] MOVING retrofitted->parking
    """
    scenario = create_minimal_scenario_with_dtos(num_wagons=2, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    validate_timeline_from_docstring(popup_sim, test_two_wagons_one_station)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 2


def test_two_wagons_two_stations() -> None:
    """Test 2 wagons, 2 stations - parallel processing.

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->parking
    t=3->4: loco[L1] MOVING parking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->parking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING parking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17: wagon[W02] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->parking
    """
    scenario = create_minimal_scenario_with_dtos(num_wagons=2, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    validate_timeline_from_docstring(popup_sim, test_two_wagons_two_stations)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 1
    assert stations[1].wagons_completed == 1


def test_four_wagons_two_stations() -> None:
    """Test 4 wagons, 2 stations - two batches.

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->parking
    t=3->4: loco[L1] MOVING parking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->parking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING parking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17: wagon[W02] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->parking
    t=18->19: loco[L1] MOVING parking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20: wagon[W03] RETROFITTING retrofit_start
    t=20: wagon[W04] RETROFITTING retrofit_start
    t=20->21: loco[L1] MOVING WS1->parking
    t=30: wagon[W03] RETROFITTED retrofit_end
    t=30: wagon[W04] RETROFITTED retrofit_end
    t=30->31: loco[L1] MOVING parking->WS1
    t=31->32: loco[L1] MOVING WS1->retrofitted
    t=32: wagon[W03] RETROFITTED track=retrofitted
    t=32: wagon[W04] RETROFITTED track=retrofitted
    t=32->33: loco[L1] MOVING retrofitted->parking
    """
    scenario = create_minimal_scenario_with_dtos(num_wagons=4, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=50.0)

    validate_timeline_from_docstring(popup_sim, test_four_wagons_two_stations)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 2
    assert stations[1].wagons_completed == 2


def test_six_wagons_two_workshops() -> None:
    """Test 6 wagons, 2 workshops (WS1 and WS2), each with 2 stations.

    With proper load balancing, wagons are distributed to fill both workshops:
    - Batch 1: W01, W02 → WS1 (2 stations)
    - Batch 2: W03, W04 → WS2 (2 stations) - arrives after WS1 had alreadz started working
    - Batch 3: W05, W06 → WS1 (after first batch completes)

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->parking
    t=3->4: loco[L1] MOVING parking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->parking
    t=6->7: loco[L1] MOVING parking->retrofit
    t=7->8: loco[L1] MOVING retrofit->WS2
    t=8: wagon[W03] RETROFITTING retrofit_start
    t=8: wagon[W04] RETROFITTING retrofit_start
    t=8->9: loco[L1] MOVING WS2->parking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING parking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17: wagon[W02] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->parking
    t=18: wagon[W03] RETROFITTED retrofit_end
    t=18: wagon[W04] RETROFITTED retrofit_end
    t=18->19: loco[L1] MOVING parking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20: wagon[W05] RETROFITTING retrofit_start
    t=20: wagon[W06] RETROFITTING retrofit_start
    t=20->21: loco[L1] MOVING WS1->parking
    t=21->22: loco[L1] MOVING parking->WS2
    t=22->23: loco[L1] MOVING WS2->retrofitted
    t=23: wagon[W03] RETROFITTED track=retrofitted
    t=23: wagon[W04] RETROFITTED track=retrofitted
    t=23->24: loco[L1] MOVING retrofitted->parking
    t=30: wagon[W05] RETROFITTED retrofit_end
    t=30: wagon[W06] RETROFITTED retrofit_end
    t=30->31: loco[L1] MOVING parking->WS1
    t=31->32: loco[L1] MOVING WS1->retrofitted
    t=32: wagon[W05] RETROFITTED track=retrofitted
    t=32: wagon[W06] RETROFITTED track=retrofitted
    t=32->33: loco[L1] MOVING retrofitted->parking

    """
    scenario = create_minimal_scenario_with_dtos(num_wagons=6, num_stations=2, retrofit_time=10.0, num_workshops=2)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=60.0)

    validate_timeline_from_docstring(popup_sim, test_six_wagons_two_workshops)

    ws1_stations = popup_sim.workshop_capacity.stations['WS1']
    assert ws1_stations[0].wagons_completed == 2, f'WS1[0] expected 2, got {ws1_stations[0].wagons_completed}'
    assert ws1_stations[1].wagons_completed == 2, f'WS1[1] expected 2, got {ws1_stations[1].wagons_completed}'

    ws2_stations = popup_sim.workshop_capacity.stations['WS2']
    assert ws2_stations[0].wagons_completed == 1, f'WS2[0] expected 1, got {ws2_stations[0].wagons_completed}'
    assert ws2_stations[1].wagons_completed == 1, f'WS2[1] expected 1, got {ws2_stations[1].wagons_completed}'


def test_seven_wagons_two_workshops() -> None:
    """Test 7 wagons, 2 workshops - tests partial batch handling.

    With 7 wagons and 2 workshops (2 stations each), the last wagon forms a partial batch.
    All batch assignments happen at t=3 before any processing starts:
    - Batch 1: W01, W02 → WS1 (both workshops have 2 available)
    - Batch 2: W03, W04 → WS2 (both workshops have 2 available)
    - Batch 3: W05, W06 → WS1 (both workshops show 0 available, queued to WS1)
    - Batch 4: W07 → WS1 (both workshops show 0 available, defaults to first workshop)

    Note: Distribution happens before processing, so capacity claims don't reflect
    future availability. This results in WS1=5, WS2=2 instead of optimal WS1=4, WS2=3.

    TIMELINE:
    t=0->1: loco[L1] MOVING parking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->parking
    t=3->4: loco[L1] MOVING parking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->parking
    t=6->7: loco[L1] MOVING parking->retrofit
    t=7->8: loco[L1] MOVING retrofit->WS2
    t=8: wagon[W03] RETROFITTING retrofit_start
    t=8: wagon[W04] RETROFITTING retrofit_start
    t=8->9: loco[L1] MOVING WS2->parking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING parking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED
    t=17: wagon[W02] RETROFITTED
    t=17->18: loco[L1] MOVING retrofitted->parking
    t=18: wagon[W03] RETROFITTED retrofit_end
    t=18: wagon[W04] RETROFITTED retrofit_end
    t=18->19: loco[L1] MOVING parking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20: wagon[W05] RETROFITTING retrofit_start
    t=20: wagon[W06] RETROFITTING retrofit_start
    t=20->21: loco[L1] MOVING WS1->parking
    t=21->22: loco[L1] MOVING parking->WS2
    t=22->23: loco[L1] MOVING WS2->retrofitted
    t=23: wagon[W03] RETROFITTED
    t=23: wagon[W04] RETROFITTED
    t=23->24: loco[L1] MOVING retrofitted->parking
    t=30: wagon[W05] RETROFITTED retrofit_end
    t=30: wagon[W06] RETROFITTED retrofit_end
    t=30->31: loco[L1] MOVING parking->WS1
    t=31->32: loco[L1] MOVING WS1->retrofitted
    t=32: wagon[W05] RETROFITTED
    t=32: wagon[W06] RETROFITTED
    t=32->33: loco[L1] MOVING retrofitted->parking
    t=33->34: loco[L1] MOVING parking->retrofit
    t=34->35: loco[L1] MOVING retrofit->WS1
    t=35: wagon[W07] RETROFITTING retrofit_start
    t=35->36: loco[L1] MOVING WS1->parking
    t=45: wagon[W07] RETROFITTED retrofit_end
    """
    scenario = create_minimal_scenario_with_dtos(num_wagons=7, num_stations=2, retrofit_time=10.0, num_workshops=2)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = WorkshopOrchestrator(sim, scenario)
    popup_sim.run(until=100.0)

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
