"""Test metrics output from simulation."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from models.locomotive import Locomotive
from models.process_times import ProcessTimes
from models.route import Route
from models.scenario import Scenario
from models.scenario import TrackSelectionStrategy
from models.topology import Topology
from models.track import Track
from models.track import TrackType
from models.train import Train
from models.wagon import Wagon
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter


def test_metrics_output() -> None:
    """Test that simulation produces metrics output."""
    start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)

    tracks = [
        Track(id='parking', type=TrackType.PARKING, edges=['e1']),
        Track(id='collection', type=TrackType.COLLECTION, edges=['e2']),
        Track(id='retrofit', type=TrackType.RETROFIT, edges=['e3']),
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['e4']),
        Track(id='WS1', type=TrackType.WORKSHOP, edges=['e5']),
    ]

    routes = [
        Route(route_id='r1', path=['parking', 'collection'], duration=1.0),
        Route(route_id='r2', path=['collection', 'retrofit'], duration=1.0),
        Route(route_id='r3', path=['retrofit', 'retrofitted'], duration=1.0),
        Route(route_id='r4', path=['retrofitted', 'parking'], duration=1.0),
        Route(route_id='r5', path=['retrofit', 'parking'], duration=1.0),
        Route(route_id='r6', path=['retrofit', 'WS1'], duration=1.0),
    ]

    wagons = [Wagon(wagon_id=f'W{i:02d}', length=10.0, needs_retrofit=True, is_loaded=False) for i in range(1, 5)]
    train = Train(train_id='T1', arrival_time=start_time, wagons=wagons)

    scenario = Scenario(
        scenario_id='metrics_test',
        start_date=start_time,
        end_date=start_time + timedelta(days=1),
        track_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
        retrofit_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
        locomotives=[
            Locomotive(
                locomotive_id='L1',
                name='L1',
                start_date=start_time,
                end_date=start_time + timedelta(days=1),
                track_id='parking',
            )
        ],
        process_times=ProcessTimes(
            train_to_hump_delay=0.0,
            wagon_hump_interval=0.0,
            wagon_coupling_time=0.0,
            wagon_decoupling_time=0.0,
            wagon_move_to_next_station=0.0,
            wagon_coupling_retrofitted_time=0.0,
            wagon_retrofit_time=10.0,
        ),
        routes=routes,
        topology=Topology(
            {
                'edges': [
                    {'id': 'e1', 'length': 100.0},
                    {'id': 'e2', 'length': 100.0},
                    {'id': 'e3', 'length': 100.0},
                    {'id': 'e4', 'length': 100.0},
                    {'id': 'e5', 'length': 100.0},
                ]
            }
        ),
        trains=[train],
        tracks=tracks,
        workshops=[
            Workshop(
                workshop_id='WS1',
                start_date='2025-01-01 00:00:00',
                end_date='2025-01-02 00:00:00',
                track_id='WS1',
                retrofit_stations=2,
            )
        ],
    )

    sim = SimPyAdapter.create_simpy_adapter()
    popupsim = PopupSim(sim, scenario)
    popupsim.run(until=100.0)

    metrics = popupsim.get_metrics()

    # Verify structure
    assert isinstance(metrics, dict)
    assert 'wagon_flow' in metrics

    # Verify wagon flow metrics
    wagon_flow = metrics['wagon_flow']
    assert len(wagon_flow) == 4  # 4 metrics expected

    metric_names = {m['name'] for m in wagon_flow}
    assert 'wagons_delivered' in metric_names
    assert 'wagons_retrofitted' in metric_names
    assert 'wagons_rejected' in metric_names
    assert 'avg_flow_time' in metric_names

    # Verify values
    delivered = next(m for m in wagon_flow if m['name'] == 'wagons_delivered')
    retrofitted = next(m for m in wagon_flow if m['name'] == 'wagons_retrofitted')

    assert delivered['value'] > 0
    assert retrofitted['value'] > 0
    assert delivered['unit'] == 'wagons'
    assert retrofitted['unit'] == 'wagons'

    # Print for manual inspection
    print('\n=== Simulation Metrics ===')
    for category, category_metrics in metrics.items():
        print(f'\n{category.upper()}:')
        for metric in category_metrics:
            print(f'  {metric["name"]}: {metric["value"]} {metric["unit"]}')
