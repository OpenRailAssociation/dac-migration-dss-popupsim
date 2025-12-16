"""Timeline validation scenarios for new architecture."""
import pytest

from application.simulation_service import SimulationApplicationService

from .scenario_builder import create_minimal_scenario
from .timeline_validator import validate_timeline_from_docstring


@pytest.mark.xfail
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
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_single_wagon_single_station, analytics_context)
    assert result.success


@pytest.mark.xfail
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
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_two_wagons_one_station, analytics_context)
    assert result.success


@pytest.mark.xfail
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
    scenario = create_minimal_scenario(num_wagons=2, num_stations=2, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_two_wagons_two_stations, analytics_context)
    assert result.success


@pytest.mark.xfail
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
    scenario = create_minimal_scenario(num_wagons=4, num_stations=2, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_four_wagons_two_stations, analytics_context)
    assert result.success


@pytest.mark.xfail
def test_six_wagons_two_workshops() -> None:
    """Test 6 wagons, 2 workshops - load balancing.

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
    scenario = create_minimal_scenario(num_wagons=6, num_stations=2, retrofit_time=10.0, num_workshops=2)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=60.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_six_wagons_two_workshops, analytics_context)
    assert result.success


@pytest.mark.xfail
def test_seven_wagons_two_workshops() -> None:
    """Test 7 wagons, 2 workshops - partial batch handling.

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
    scenario = create_minimal_scenario(num_wagons=7, num_stations=2, retrofit_time=10.0, num_workshops=2)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=100.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_seven_wagons_two_workshops, analytics_context)
    assert result.success
