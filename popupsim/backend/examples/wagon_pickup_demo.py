"""Demonstration of wagon pickup process from collection to retrofit tracks."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import UTC
from datetime import datetime

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
from models.wagon import WagonStatus
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter


def create_demo_scenario() -> Scenario:
    """Create scenario with collection, retrofit, and parking tracks."""
    # Topology: parking -> collection -> retrofit
    topology = Topology(
        {
            'edges': [
                {'edge_id': 'e_parking', 'from_node': 'n1', 'to_node': 'n2', 'length': 100.0},
                {'edge_id': 'e_collection', 'from_node': 'n3', 'to_node': 'n4', 'length': 200.0},
                {'edge_id': 'e_retrofit', 'from_node': 'n5', 'to_node': 'n6', 'length': 150.0},
            ]
        }
    )

    # Tracks
    parking_track = Track(id='parking_1', name='Resource Parking', type=TrackType.PARKING, edges=['e_parking'])

    collection_track = Track(
        id='collection_1', name='Collection Track 1', type=TrackType.COLLECTION, edges=['e_collection']
    )

    retrofit_track = Track(id='retrofit_1', name='Retrofit Track', type=TrackType.RETROFIT, edges=['e_retrofit'])

    # Routes
    routes = [
        Route(route_id='parking_to_collection', path=['parking_1', 'collection_1'], duration=5.0),
        Route(route_id='collection_to_retrofit', path=['collection_1', 'retrofit_1'], duration=3.0),
        Route(route_id='retrofit_to_parking', path=['retrofit_1', 'parking_1'], duration=5.0),
    ]

    # Locomotive at parking
    loco = Locomotive(
        locomotive_id='L1',
        name='Loco 1',
        start_date=datetime(2031, 7, 4, 0, 0, tzinfo=UTC),
        end_date=datetime(2031, 7, 5, 0, 0, tzinfo=UTC),
        track_id='parking_1',
    )

    # Workshop
    workshop = Workshop(
        workshop_id='WS1', start_date='2031-07-04T00:00:00Z', end_date='2031-07-05T00:00:00Z', track_id='retrofit_1'
    )

    # Train with 3 wagons
    wagons = [Wagon(wagon_id=f'W{i}', length=20.0, is_loaded=False, needs_retrofit=True) for i in range(1, 4)]

    train = Train(
        train_id='T1',
        arrival_time=datetime(2031, 7, 4, 0, 5, tzinfo=UTC),  # 5 minutes after start
        wagons=wagons,
    )

    # Process times
    process_times = ProcessTimes(
        train_to_hump_delay=5.0, wagon_hump_interval=1.0, wagon_coupling_time=2.0, wagon_decoupling_time=2.0
    )

    return Scenario(
        scenario_id='wagon_pickup_demo',
        start_date=datetime(2031, 7, 4, 0, 0, tzinfo=UTC),
        end_date=datetime(2031, 7, 5, 0, 0, tzinfo=UTC),
        trains=[train],
        tracks=[parking_track, collection_track, retrofit_track],
        locomotives=[loco],
        workshops=[workshop],
        routes=routes,
        topology=topology,
        process_times=process_times,
        track_selection_strategy=TrackSelectionStrategy.FIRST_AVAILABLE,
    )


def print_simulation_state(popup_sim: PopupSim, time: float) -> None:
    """Print current simulation state."""
    print(f'\n{"=" * 60}')
    print(f'Simulation Time: {time:.1f} minutes')
    print(f'{"=" * 60}')

    # Wagon states
    print('\nWagon Status:')
    for wagon in popup_sim.wagons_queue:
        print(f'  {wagon.wagon_id}: {wagon.status.value:15s} on track {wagon.track_id}')

    # Track occupancy
    print('\nTrack Occupancy:')
    for track_id, capacity in popup_sim.track_capacity.track_capacities.items():
        usage = popup_sim.track_capacity.current_occupancy.get(track_id, 0)
        print(f'  {track_id:15s}: {usage:5.1f}m / {capacity:5.1f}m ({usage / capacity * 100:.0f}%)')

    # Locomotive status
    print('\nLocomotive Status:')
    for loco in popup_sim.scenario.locomotives:
        print(f'  {loco.locomotive_id}: {loco.status.value:12s} at {loco.track_id}')


if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('Wagon Pickup Process Demonstration')
    print('=' * 60)
    print('\nScenario:')
    print('  - 1 train with 3 wagons (20m each)')
    print('  - Collection track capacity: 150m (75% of 200m)')
    print('  - Retrofit track capacity: 112.5m (75% of 150m)')
    print('  - 1 locomotive at parking track')
    print('\nProcess:')
    print('  1. Train arrives, wagons selected to collection track')
    print('  2. Loco travels: parking -> collection (5 min)')
    print('  3. Loco couples 3 wagons (6 min)')
    print('  4. Loco travels: collection -> retrofit (3 min)')
    print('  5. Loco decouples 3 wagons (6 min)')
    print('  6. Loco returns: retrofit -> parking (5 min)')

    scenario = create_demo_scenario()
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)

    print('\n' + '=' * 60)
    print('Running Simulation...')
    print('=' * 60)

    # Enable debug logging
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # Run simulation
    popup_sim.run(until=60.0)  # Run for 60 minutes

    print(f'\nTotal wagons in queue: {len(popup_sim.wagons_queue)}')
    print(f'Train wagons: {len(scenario.trains[0].wagons)}')

    # Print final state
    print_simulation_state(popup_sim, 50.0)

    # Summary
    print('\n' + '=' * 60)
    print('Summary')
    print('=' * 60)

    print('\nAll wagons from train:')
    for wagon in scenario.trains[0].wagons:
        print(f'  {wagon.wagon_id}: {wagon.status.value} on {wagon.track_id}')

    retrofitting = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.RETROFITTING]
    moving = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.MOVING]
    selected = [w for w in popup_sim.wagons_queue if w.status == WagonStatus.SELECTED]

    print(f'\nWagons on collection track: {len(selected)}')
    print(f'Wagons being moved: {len(moving)}')
    print(f'Wagons on retrofit track: {len(retrofitting)}')

    loco = scenario.locomotives[0]
    print('\nLocomotive final state:')
    print(f'  Status: {loco.status.value}')
    print(f'  Location: {loco.track_id}')

    print('\n' + '=' * 60)
    print('Demo Complete')
    print('=' * 60 + '\n')
