"""Timeline validation scenarios for new architecture."""

from application.simulation_service import SimulationApplicationService
from contexts.configuration.application.dtos.route_input_dto import RouteInputDTO
from contexts.configuration.application.dtos.track_input_dto import TrackInputDTO
import pytest

from .scenario_builder import create_minimal_scenario
from .timeline_validator import validate_timeline_from_docstring


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_single_wagon_single_station() -> None:
    """Test 1 wagon, 1 station - validates state at each timestep.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18->19: loco[L1] MOVING locoparking->retrofitted
    t=19->20: loco[L1] MOVING retrofitted->parking
    t=20: wagon[W01] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_single_wagon_single_station, analytics_context)
    assert result.success


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_two_wagons_one_station() -> None:
    """Test 2 wagons, 1 station - sequential processing.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] DISTRIBUTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18->19: loco[L1] MOVING locoparking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20: wagon[W02] RETROFITTING retrofit_start
    t=20->21: loco[L1] MOVING WS1->locoparking
    t=21->22: loco[L1] MOVING locoparking->retrofitted
    t=22->23: loco[L1] MOVING retrofitted->parking
    t=23: wagon[W01] PARKING track=parking
    t=30: wagon[W02] RETROFITTED retrofit_end
    t=30->31: loco[L1] MOVING locoparking->WS1
    t=31->32: loco[L1] MOVING WS1->retrofitted
    t=32: wagon[W02] DISTRIBUTED track=retrofitted
    t=32->33: loco[L1] MOVING retrofitted->locoparking
    t=33->34: loco[L1] MOVING locoparking->retrofitted
    t=34->35: loco[L1] MOVING retrofitted->parking
    t=35: wagon[W02] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_two_wagons_one_station, analytics_context)
    assert result.success


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_two_wagons_two_stations() -> None:
    """Test 2 wagons, 2 stations - parallel processing.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17: wagon[W02] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18->19: loco[L1] MOVING locoparking->retrofitted
    t=19->20: loco[L1] MOVING retrofitted->parking
    t=20: wagon[W01] PARKING track=parking
    t=20: wagon[W02] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=2, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_two_wagons_two_stations, analytics_context)
    assert result.success


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_four_wagons_two_stations() -> None:
    """Test 4 wagons, 2 stations.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] DISTRIBUTED track=retrofitted
    t=17: wagon[W02] DISTRIBUTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18->19: loco[L1] MOVING locoparking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20: wagon[W03] RETROFITTING retrofit_start
    t=20: wagon[W04] RETROFITTING retrofit_start
    t=20->21: loco[L1] MOVING WS1->locoparking
    t=21->22: loco[L1] MOVING locoparking->retrofitted
    t=22->23: loco[L1] MOVING retrofitted->parking
    t=23: wagon[W01] PARKING track=parking
    t=23: wagon[W02] PARKING track=parking
    t=23->24: loco[L1] MOVING parking->locoparking
    t=30: wagon[W03] RETROFITTED retrofit_end
    t=30: wagon[W04] RETROFITTED retrofit_end
    t=30->31: loco[L1] MOVING locoparking->WS1
    t=31->32: loco[L1] MOVING WS1->retrofitted
    t=32: wagon[W03] DISTRIBUTED track=retrofitted
    t=32: wagon[W04] DISTRIBUTED track=retrofitted
    t=32->33: loco[L1] MOVING retrofitted->locoparking
    t=33->34: loco[L1] MOVING locoparking->retrofitted
    t=34->35: loco[L1] MOVING retrofitted->parking
    t=35: wagon[W03] PARKING track=parking
    t=35: wagon[W04] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=4, num_stations=2, retrofit_time=10.0)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_four_wagons_two_stations, analytics_context)
    assert result.success


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_six_wagons_two_workshops() -> None:
    """Test 6 wagons, 2 workshops - load balancing.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=6->7: loco[L1] MOVING locoparking->retrofit
    t=7->8: loco[L1] MOVING retrofit->WS2
    t=8: wagon[W03] RETROFITTING retrofit_start
    t=8: wagon[W04] RETROFITTING retrofit_start
    t=8->9: loco[L1] MOVING WS2->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS2
    t=16->17: loco[L1] MOVING WS2->retrofitted
    t=17: wagon[W01] DISTRIBUTED track=retrofitted
    t=17: wagon[W02] DISTRIBUTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18: wagon[W03] RETROFITTED retrofit_end
    t=18: wagon[W04] RETROFITTED retrofit_end
    t=18->19: loco[L1] MOVING locoparking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20->21: loco[L1] MOVING WS1->locoparking
    t=21->22: loco[L1] MOVING locoparking->retrofitted
    t=22->23: loco[L1] MOVING retrofitted->parking
    t=23: wagon[W01] PARKING track=parking
    t=23: wagon[W02] PARKING track=parking
    t=23->24: loco[L1] MOVING parking->locoparking
    t=24->25: loco[L1] MOVING locoparking->WS1
    t=25->26: loco[L1] MOVING WS1->retrofitted
    t=26: wagon[W03] DISTRIBUTED track=retrofitted
    t=26: wagon[W04] DISTRIBUTED track=retrofitted
    t=26: wagon[W05] RETROFITTING retrofit_start
    t=26: wagon[W06] RETROFITTING retrofit_start
    t=26->27: loco[L1] MOVING retrofitted->locoparking
    t=27->28: loco[L1] MOVING locoparking->retrofitted
    t=28->29: loco[L1] MOVING retrofitted->parking
    t=29: wagon[W03] PARKING track=parking
    t=29: wagon[W04] PARKING track=parking
    t=29->30: loco[L1] MOVING parking->locoparking
    t=36: wagon[W05] RETROFITTED retrofit_end
    t=36: wagon[W06] RETROFITTED retrofit_end
    t=36->37: loco[L1] MOVING locoparking->WS1
    t=37->38: loco[L1] MOVING WS1->retrofitted
    t=38: wagon[W05] DISTRIBUTED track=retrofitted
    t=38: wagon[W06] DISTRIBUTED track=retrofitted
    t=38->39: loco[L1] MOVING retrofitted->locoparking
    t=39->40: loco[L1] MOVING locoparking->retrofitted
    t=40->41: loco[L1] MOVING retrofitted->parking
    t=41: wagon[W05] PARKING track=parking
    t=41: wagon[W06] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=6, num_stations=2, retrofit_time=10.0, num_workshops=2)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=60.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_six_wagons_two_workshops, analytics_context)
    assert result.success


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_seven_wagons_two_workshops() -> None:
    """Test 7 wagons, 2 workshops - partial batch handling.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=6->7: loco[L1] MOVING locoparking->retrofit
    t=7->8: loco[L1] MOVING retrofit->WS2
    t=8: wagon[W03] RETROFITTING retrofit_start
    t=8: wagon[W04] RETROFITTING retrofit_start
    t=8->9: loco[L1] MOVING WS2->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS2
    t=16->17: loco[L1] MOVING WS2->retrofitted
    t=17: wagon[W01] DISTRIBUTED track=retrofitted
    t=17: wagon[W02] DISTRIBUTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18: wagon[W03] RETROFITTED retrofit_end
    t=18: wagon[W04] RETROFITTED retrofit_end
    t=18->19: loco[L1] MOVING locoparking->retrofit
    t=19->20: loco[L1] MOVING retrofit->WS1
    t=20->21: loco[L1] MOVING WS1->locoparking
    t=21->22: loco[L1] MOVING locoparking->retrofitted
    t=22->23: loco[L1] MOVING retrofitted->parking
    t=23: wagon[W01] PARKING track=parking
    t=23: wagon[W02] PARKING track=parking
    t=23->24: loco[L1] MOVING parking->locoparking
    t=24->25: loco[L1] MOVING locoparking->WS1
    t=25->26: loco[L1] MOVING WS1->retrofitted
    t=26: wagon[W03] DISTRIBUTED track=retrofitted
    t=26: wagon[W04] DISTRIBUTED track=retrofitted
    t=26: wagon[W05] RETROFITTING retrofit_start
    t=26: wagon[W06] RETROFITTING retrofit_start
    t=26->27: loco[L1] MOVING retrofitted->locoparking
    t=27->28: loco[L1] MOVING locoparking->retrofit
    t=28->29: loco[L1] MOVING retrofit->WS1
    t=29: wagon[W07] RETROFITTING retrofit_start
    t=29->30: loco[L1] MOVING WS1->locoparking
    t=30->31: loco[L1] MOVING locoparking->retrofitted
    t=31->32: loco[L1] MOVING retrofitted->parking
    t=32: wagon[W03] PARKING track=parking
    t=32: wagon[W04] PARKING track=parking
    t=32->33: loco[L1] MOVING parking->locoparking
    t=36: wagon[W05] RETROFITTED retrofit_end
    t=36: wagon[W06] RETROFITTED retrofit_end
    t=36->37: loco[L1] MOVING locoparking->WS1
    t=37->38: loco[L1] MOVING WS1->retrofitted
    t=38: wagon[W05] DISTRIBUTED track=retrofitted
    t=38: wagon[W06] DISTRIBUTED track=retrofitted
    t=38->39: loco[L1] MOVING retrofitted->locoparking
    t=39: wagon[W07] RETROFITTED retrofit_end
    t=39->40: loco[L1] MOVING locoparking->retrofitted
    t=40->41: loco[L1] MOVING retrofitted->parking
    t=41: wagon[W05] PARKING track=parking
    t=41: wagon[W06] PARKING track=parking
    t=41->42: loco[L1] MOVING parking->locoparking
    t=42->43: loco[L1] MOVING locoparking->WS2
    t=43->44: loco[L1] MOVING WS2->retrofitted
    t=44: wagon[W07] DISTRIBUTED track=retrofitted
    t=44->45: loco[L1] MOVING retrofitted->locoparking
    t=45->46: loco[L1] MOVING locoparking->retrofitted
    t=46->47: loco[L1] MOVING retrofitted->parking
    t=47: wagon[W07] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=7, num_stations=2, retrofit_time=10.0, num_workshops=2)
    service = SimulationApplicationService(scenario)
    result = service.execute(until=100.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_seven_wagons_two_workshops, analytics_context)
    assert result.success


@pytest.mark.xfail(reason='Old architecture tests - need update for unified operations')
def test_four_wagons_four_stations_two_collection_tracks() -> None:
    """Test 1 train (4 wagons) with 2 collection tracks - verify all 4 picked up together.

    TIMELINE:
    t=0->1: loco[L1] MOVING locoparking->collection
    t=1->2: loco[L1] MOVING collection->retrofit
    t=2->3: loco[L1] MOVING retrofit->locoparking
    t=3->4: loco[L1] MOVING locoparking->retrofit
    t=4->5: loco[L1] MOVING retrofit->WS1
    t=5: wagon[W01] RETROFITTING retrofit_start
    t=5: wagon[W02] RETROFITTING retrofit_start
    t=5: wagon[W03] RETROFITTING retrofit_start
    t=5: wagon[W04] RETROFITTING retrofit_start
    t=5->6: loco[L1] MOVING WS1->locoparking
    t=15: wagon[W01] RETROFITTED retrofit_end
    t=15: wagon[W02] RETROFITTED retrofit_end
    t=15: wagon[W03] RETROFITTED retrofit_end
    t=15: wagon[W04] RETROFITTED retrofit_end
    t=15->16: loco[L1] MOVING locoparking->WS1
    t=16->17: loco[L1] MOVING WS1->retrofitted
    t=17: wagon[W01] RETROFITTED track=retrofitted
    t=17: wagon[W02] RETROFITTED track=retrofitted
    t=17: wagon[W03] RETROFITTED track=retrofitted
    t=17: wagon[W04] RETROFITTED track=retrofitted
    t=17->18: loco[L1] MOVING retrofitted->locoparking
    t=18->19: loco[L1] MOVING locoparking->retrofitted
    t=19->20: loco[L1] MOVING retrofitted->parking
    t=20: wagon[W01] PARKING track=parking
    t=20: wagon[W02] PARKING track=parking
    t=20: wagon[W03] PARKING track=parking
    t=20: wagon[W04] PARKING track=parking
    """
    scenario = create_minimal_scenario(num_wagons=4, num_stations=4, retrofit_time=10.0)

    # Add second collection track (available but won't be used by single train)
    tracks_list = list(scenario.tracks)
    tracks_list.append(TrackInputDTO(id='collection2', edges=['collection2'], type='collection', length=300.0))
    scenario.tracks = tracks_list
    scenario.topology.edges['collection2'] = {'nodes': [1, 2], 'length': 300.0}
    scenario.routes.extend(
        [
            RouteInputDTO(id='collection_collection2', path=['collection', 'collection2'], duration=1.0),
            RouteInputDTO(id='collection2_retrofit', path=['collection2', 'retrofit'], duration=1.0),
        ]
    )

    service = SimulationApplicationService(scenario)
    result = service.execute(until=50.0)

    analytics_context = service.contexts.get('analytics')
    validate_timeline_from_docstring(result, test_four_wagons_four_stations_two_collection_tracks, analytics_context)
    assert result.success
