"""Validation scenarios with precomputed expected results.

These scenarios have simple, predictable configurations where we can
manually calculate expected outcomes to validate simulation correctness.
"""

from datetime import UTC, datetime, timedelta
import pytest

from models.locomotive import Locomotive
from models.process_times import ProcessTimes
from models.route import Route
from models.scenario import Scenario, TrackSelectionStrategy
from models.topology import Topology
from models.track import Track, TrackType
from models.train import Train
from models.wagon import Wagon, WagonStatus
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter
from .timeline_validator import validate_loco_timeline


def create_minimal_scenario(
    num_wagons: int,
    num_stations: int,
    retrofit_time: float = 10.0,
) -> Scenario:
    """Create minimal scenario with predictable timing."""
    start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)

    tracks = [
        Track(id='parking', type=TrackType.PARKING, edges=['e1']),
        Track(id='collection', type=TrackType.COLLECTION, edges=['e2']),
        Track(id='retrofit', type=TrackType.RETROFIT, edges=['e3']),
        Track(id='WS1', type=TrackType.WORKSHOP, edges=['e5']),
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['e4']),
    ]

    routes = [
        Route(route_id='r1', path=['parking', 'collection'], duration=1.0),
        Route(route_id='r2', path=['collection', 'retrofit'], duration=1.0),
        Route(route_id='r3', path=['retrofit', 'parking'], duration=1.0),
        Route(route_id='r4', path=['retrofit', 'WS1'], duration=1.0),
        Route(route_id='r5', path=['parking', 'WS1'], duration=1.0),
        Route(route_id='r6', path=['WS1', 'retrofitted'], duration=1.0),
        Route(route_id='r7', path=['retrofitted', 'parking'], duration=1.0),
        Route(route_id='r8', path=['parking', 'retrofit'], duration=1.0),
    ]

    wagons = [
        Wagon(wagon_id=f'W{i:02d}', length=10.0, needs_retrofit=True, is_loaded=False)
        for i in range(1, num_wagons + 1)
    ]
    train = Train(train_id='T1', arrival_time=start_time, wagons=wagons)

    return Scenario(
        scenario_id='validation',
        start_date=start_time,
        end_date=start_time + timedelta(days=1),
        track_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
        retrofit_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
        locomotives=[Locomotive(locomotive_id='L1', name='L1', start_date=start_time,
                               end_date=start_time + timedelta(days=1), track_id='parking')],
        process_times=ProcessTimes(
            train_to_hump_delay=0.0,
            wagon_hump_interval=0.0,
            wagon_coupling_time=0.0,
            wagon_decoupling_time=0.0,
            wagon_move_to_next_station=0.0,
            wagon_coupling_retrofitted_time=0.0,
            wagon_retrofit_time=retrofit_time,
        ),
        routes=routes,
        topology=Topology({'edges': [
            {'id': 'e1', 'length': 100.0}, {'id': 'e2', 'length': 100.0},
            {'id': 'e3', 'length': 100.0}, {'id': 'e4', 'length': 100.0},
            {'id': 'e5', 'length': 100.0}
        ]}),
        trains=[train],
        tracks=tracks,
        workshops=[Workshop(workshop_id='WS1', start_date='2025-01-01 00:00:00',
                           end_date='2025-01-02 00:00:00', track_id='WS1',
                           retrofit_stations=num_stations)],
    )


def test_single_wagon_single_station() -> None:
    """Test 1 wagon, 1 station - validates state at each timestep.

    Expected timeline:
    Delivery to yard:
    t=0: Train arrives, wagon to collection (instant)
    t=0->1: Loco parking->collection (1min)
    t=1->2: Loco collection->retrofit (1min)
    t=2->3: Loco retrofit->parking (1min)

    Delivery to station:
    t=3->4: Loco parking->retrofit (1min)
    t=4: Loco at retrofit
    t=4->5: Loco + Wagon retrofit->WS1 (1min)
    t=5: Loco + Wagon at WS1 station
    t=5->6: Loco WS1->parking (1min)

    Retrofit:
    t=5->15: Wagon retrofitting (10min)
    t=15: Retrofit complete

    Pickup from station:
    t=15->16: Loco parking->WS1 (1min)
    t=16: Loco at WS1
    t=16->17: Loco + Wagon WS1->retrofitted (1min)
    t=17: Loco + Wagon at retrofitted
    t=17->18: Loco retrofitted->parking (1min)
    t=18: Loco at parking
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)

    # Run full simulation
    popup_sim.run(until=50.0)
    loco = popup_sim.locomotives_queue[0]
    wagon = popup_sim.wagons_queue[0]

    # Verify final state
    assert wagon.status == WagonStatus.RETROFITTED
    assert wagon.needs_retrofit is False
    assert wagon.coupler_type.value == 'dac'
    assert wagon.track_id == 'retrofitted'

    # Verify timing
    assert wagon.retrofit_start_time == 5.0
    assert wagon.retrofit_end_time == 15.0

    # Verify locomotive state transitions
    validate_loco_timeline(loco, """
        t=0: PARKING Initial state
        t=0: MOVING parking→collection
        t=1: COUPLING at collection
        t=1: MOVING collection→retrofit
        t=2: DECOUPLING at retrofit
        t=2: MOVING retrofit→parking
        t=3: PARKING back at parking
        t=3: MOVING parking→retrofit
        t=4: MOVING retrofit→WS1
        t=5: MOVING WS1→parking
        t=15: MOVING parking→WS1
        t=16: MOVING WS1→retrofitted
        t=17: DECOUPLING at retrofitted
        t=17: MOVING retrofitted→parking
        t=18: PARKING final state
    """)

    # Verify workshop and metrics
    stations = popup_sim.workshop_capacity.stations['WS1']
    assert stations[0].wagons_completed == 1
    metrics = popup_sim.get_metrics()
    wagon_flow = metrics['wagon_flow']
    assert any(m['name'] == 'wagons_delivered' and m['value'] == 1 for m in wagon_flow)
    assert any(m['name'] == 'wagons_retrofitted' and m['value'] == 1 for m in wagon_flow)


def test_two_wagons_one_station() -> None:
    """Test 2 wagons, 1 station - sequential processing.

    Expected timeline:
    Delivery to yard:
    t=0: Train arrives, wagons to collection (instant)
    t=0->1: Loco parking->collection (1min)
    t=1->2: Loco collection->retrofit (1min)
    t=2->3: Loco retrofit->parking (1min)

    Delivery to station:
    t=3->4: Loco parking->retrofit (1min)
    t=4: Loco at retrofit
    t=4->5: Loco + Wagon retrofit->WS1 (1min)
    t=5: Loco + Wagon at WS1 station
    t=5->6: Loco WS1->parking (1min)

    Retrofit:
    t=5->15: Wagon retrofitting (10min)
    t=15: Retrofit complete

    Pickup from station:
    t=15->16: Loco parking->WS1 (1min)
    t=16: Loco at WS1
    t=16->17: Loco + Wagon WS1->retrofitted (1min)
    t=17: Loco + Wagons at retrofitted
    t=17->18: Loco retrofitted->parking (1min)
    t=18: Loco at parking

    Delivery to station:
    t=18->19: Loco parking->retrofit (1min)
    t=19: Loco at retrofit
    t=19->20: Loco + Wagon retrofit->WS1 (1min)
    t=20: Loco + Wagon at WS1 station
    t=20->21: Loco WS1->parking (1min)

    Retrofit:
    t=20->30: Wagon retrofitting (10min)
    t=30: Retrofit complete

    Pickup from station:
    t=30->31: Loco parking->WS1 (1min)
    t=31: Loco at WS1
    t=31->32: Loco + Wagon WS1->retrofitted (1min)
    t=32: Loco + Wagons at retrofitted
    t=32->33: Loco retrofitted->parking (1min)
    t=33: Loco at parking

    Expected: W1 retrofit_end=15, W2 retrofit_end=30
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)

    assert len(popup_sim.wagons_queue) == 2
    w1, w2 = popup_sim.wagons_queue
    
    # Verify wagon timing
    assert w1.retrofit_start_time == 5.0
    assert w1.retrofit_end_time == 15.0
    assert w2.retrofit_start_time == 20.0
    assert w2.retrofit_end_time == 30.0
    
    # Verify locomotive state transitions
    loco = popup_sim.locomotives_queue[0]
    validate_loco_timeline(loco, """
        t=0: PARKING Initial state
        t=0: MOVING parking→collection
        t=1: COUPLING at collection
        t=1: MOVING collection→retrofit
        t=2: DECOUPLING at retrofit
        t=2: MOVING retrofit→parking
        t=3: PARKING back at parking
        t=3: MOVING parking→retrofit
        t=4: MOVING retrofit→WS1
        t=5: MOVING WS1→parking
        t=15: MOVING parking→WS1
        t=16: MOVING WS1→retrofitted
        t=17: DECOUPLING at retrofitted
        t=17: MOVING retrofitted→parking
        t=18: PARKING at parking
        t=18: MOVING parking→retrofit
        t=19: MOVING retrofit→WS1
        t=20: MOVING WS1→parking
        t=30: MOVING parking→WS1
        t=31: MOVING WS1→retrofitted
        t=32: DECOUPLING at retrofitted
        t=32: MOVING retrofitted→parking
        t=33: PARKING final state
    """)


def test_two_wagons_two_stations() -> None:
    """Test 2 wagons, 2 stations - parallel processing.

    Expected timeline:
    DELIVERY: t=0->6
    t=6->16: Both wagons retrofit (parallel, 10min)
    PICKUP: Batch pickup at t=16

    Expected: Both retrofit_end=16
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)

    assert len(popup_sim.wagons_queue) == 2
    w1, w2 = popup_sim.wagons_queue
    assert w1.retrofit_start_time == 5.0
    assert w1.retrofit_end_time == 15.0
    assert w2.retrofit_start_time == 5.0
    assert w2.retrofit_end_time == 15.0


def test_four_wagons_two_stations() -> None:
    """Test 4 wagons, 2 stations - two batches.

    Expected timeline:
    Batch 1 delivery: t=3->5 (2 wagons to workshop)
    Batch 1 retrofit: t=5->15 (parallel)
    Batch 1 pickup: t=15->18 (wagons leave workshop track)
    Batch 2 delivery: t=18->20 (can only start when track empty)
    Batch 2 retrofit: t=20->30 (parallel)
    Batch 2 pickup: t=30->33

    Expected: Batch1 retrofit_end=15, Batch2 retrofit_end=30
    """
    scenario = create_minimal_scenario(num_wagons=4, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)

    assert len(popup_sim.wagons_queue) == 4

    batch1 = [w for w in popup_sim.wagons_queue if w.wagon_id in ['W01', 'W02']]
    for wagon in batch1:
        assert wagon.retrofit_start_time == 5.0
        assert wagon.retrofit_end_time == 15.0

    batch2 = [w for w in popup_sim.wagons_queue if w.wagon_id in ['W03', 'W04']]
    for wagon in batch2:
        assert wagon.retrofit_start_time == 20.0
        assert wagon.retrofit_end_time == 30.0


def test_station_utilization() -> None:
    """Test station utilization metrics are tracked correctly.

    With 2 wagons and 2 stations, each station should process 1 wagon.
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)

    stations = popup_sim.workshop_capacity.stations['WS1']
    assert len(stations) == 2

    # Each station should have processed 1 wagon
    total_processed = sum(s.wagons_completed for s in stations)
    assert total_processed == 2

    # Each station should have history
    for station in stations:
        if station.wagons_completed > 0:
            assert len(station.history) > 0


def test_zero_process_times() -> None:
    """Test with zero process times - validates timing logic.

    With all times = 0, retrofit should start almost immediately.
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=5.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=20.0)

    wagon = popup_sim.wagons_queue[0]
    assert wagon.retrofit_start_time == 5.0
    assert wagon.retrofit_end_time == 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
