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
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['e4']),
    ]
    
    routes = [
        Route(route_id='r1', path=['parking', 'collection'], duration=1.0),
        Route(route_id='r2', path=['collection', 'retrofit'], duration=1.0),
        Route(route_id='r3', path=['retrofit', 'retrofitted'], duration=1.0),
        Route(route_id='r4', path=['retrofitted', 'parking'], duration=1.0),
        Route(route_id='r5', path=['retrofit', 'parking'], duration=1.0),
        Route(route_id='r6', path=['retrofit', 'WS1'], duration=1.0),
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
            {'id': 'e3', 'length': 100.0}, {'id': 'e4', 'length': 100.0}
        ]}),
        trains=[train],
        tracks=tracks,
        workshops=[Workshop(workshop_id='WS1', start_date='2025-01-01 00:00:00',
                           end_date='2025-01-02 00:00:00', track_id='retrofit',
                           retrofit_stations=num_stations)],
    )


def test_single_wagon_single_station() -> None:
    """Test 1 wagon, 1 station - simplest case.
    
    Expected timeline:
    t=0: Train arrives, wagon to collection (instant)
    t=1: Loco to collection (1min)
    t=2: Loco to retrofit (1min)
    t=3: Loco to parking (1min)
    t=4: Wagon travels to station (1min)
    t=4-14: Wagon retrofits (10min)
    t=14: Wagon signals completion
    
    Expected: 1 wagon processed in ~14min
    """
    scenario = create_minimal_scenario(num_wagons=1, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    assert len(popup_sim.wagons_queue) == 1
    wagon = popup_sim.wagons_queue[0]
    assert wagon.status == WagonStatus.RETROFITTED
    assert wagon.retrofit_end_time is not None
    assert 13.0 <= wagon.retrofit_end_time <= 15.0  # Allow small variance


def test_two_wagons_one_station() -> None:
    """Test 2 wagons, 1 station - sequential processing.
    
    Expected timeline:
    t=0-3: Delivery (same as above)
    t=4: W1 starts retrofit
    t=14: W1 completes, W2 starts (blocked until W1 done)
    t=24: W2 completes
    
    Expected: 2 wagons, W2 finishes at ~24min
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=1, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    assert len(popup_sim.wagons_queue) == 2
    w1, w2 = popup_sim.wagons_queue
    assert w1.retrofit_end_time is not None
    assert w2.retrofit_end_time is not None
    assert 13.0 <= w1.retrofit_end_time <= 15.0
    assert 23.0 <= w2.retrofit_end_time <= 25.0


def test_two_wagons_two_stations() -> None:
    """Test 2 wagons, 2 stations - parallel processing.
    
    Expected timeline:
    t=0-3: Delivery
    t=4: Both wagons start retrofit (parallel)
    t=14: Both complete simultaneously
    
    Expected: 2 wagons, both finish at ~14min
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    assert len(popup_sim.wagons_queue) == 2
    w1, w2 = popup_sim.wagons_queue
    assert w1.retrofit_end_time is not None
    assert w2.retrofit_end_time is not None
    # Both should finish around same time (parallel)
    assert 13.0 <= w1.retrofit_end_time <= 15.0
    assert 13.0 <= w2.retrofit_end_time <= 15.0


def test_four_wagons_two_stations() -> None:
    """Test 4 wagons, 2 stations - two batches.
    
    Expected timeline:
    Batch 1 (W1, W2):
    t=4: Start retrofit
    t=14: Complete
    
    Batch 2 (W3, W4):
    t=14: Start retrofit (after batch 1 picked up)
    t=24: Complete
    
    Expected: 4 wagons, last finishes at ~24min
    """
    scenario = create_minimal_scenario(num_wagons=4, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    assert len(popup_sim.wagons_queue) == 4
    
    # First batch should finish around t=14
    batch1 = [w for w in popup_sim.wagons_queue if w.wagon_id in ['W01', 'W02']]
    for wagon in batch1:
        assert wagon.retrofit_end_time is not None
        assert 13.0 <= wagon.retrofit_end_time <= 15.0
    
    # Second batch should finish around t=24
    batch2 = [w for w in popup_sim.wagons_queue if w.wagon_id in ['W03', 'W04']]
    for wagon in batch2:
        assert wagon.retrofit_end_time is not None
        assert 23.0 <= wagon.retrofit_end_time <= 25.0


def test_station_utilization() -> None:
    """Test station utilization metrics are tracked correctly.
    
    With 2 wagons and 2 stations, each station should process 1 wagon.
    """
    scenario = create_minimal_scenario(num_wagons=2, num_stations=2, retrofit_time=10.0)
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)
    popup_sim.run(until=50.0)
    
    stations = popup_sim.workshop_capacity.stations['retrofit']
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
    assert wagon.retrofit_end_time is not None
    # With zero delays, should finish very quickly (just retrofit time + routes)
    assert wagon.retrofit_end_time <= 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
