"""Demonstration of track capacity management in PopUpSim.

This script shows two scenarios:
1. Wagons within capacity - all wagons accepted
2. Wagons exceeding capacity - some wagons rejected
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import UTC
from datetime import datetime

from models.locomotive import Locomotive
from models.process_times import ProcessTimes
from models.route import Route
from models.scenario import Scenario
from models.topology import Topology
from models.track import Track
from models.track import TrackType
from models.train import Train
from models.wagon import Wagon
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter


def create_simple_topology() -> dict:
    """Create simple topology with one collection track of 100m."""
    return {'edges': [{'id': 'edge_1', 'length': 100.0}]}


def scenario_within_capacity() -> None:
    """Scenario 1: Wagons stay within 75% capacity (75m of 100m track)."""
    print('\n' + '=' * 60)
    print('SCENARIO 1: Within Capacity')
    print('=' * 60)
    print('Track length: 100m')
    print('Capacity (75%): 75m')
    print('Wagons: 3 wagons × 20m = 60m total')
    print('-' * 60)

    topology = Topology(create_simple_topology())
    wagons = [Wagon(wagon_id=f'W{i}', length=20.0, is_loaded=False, needs_retrofit=True) for i in range(1, 4)]
    train = Train(train_id='T1', arrival_time=datetime(2031, 7, 4, 8, 0, 0, tzinfo=UTC), wagons=wagons)
    
    tracks = [
        Track(id='parking', type=TrackType.PARKING, edges=['edge_1']),
        Track(id='collection_1', type=TrackType.COLLECTION, edges=['edge_1']),
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['edge_1']),
    ]
    
    loco = Locomotive(locomotive_id='L1', name='Loco 1',
                     start_date=datetime(2031, 7, 4, 0, 0, 0, tzinfo=UTC),
                     end_date=datetime(2031, 7, 5, 0, 0, 0, tzinfo=UTC), track_id='parking')
    
    routes = [
        Route(route_id='parking_to_collection', path=['parking', 'collection_1'], duration=1.0),
        Route(route_id='collection_to_retrofitted', path=['collection_1', 'retrofitted'], duration=1.0),
    ]
    
    scenario = Scenario(
        scenario_id='within_capacity', start_date=datetime(2031, 7, 4, 0, 0, 0, tzinfo=UTC),
        end_date=datetime(2031, 7, 5, 0, 0, 0, tzinfo=UTC), trains=[train], tracks=tracks,
        locomotives=[loco], workshops=[], topology=topology, routes=routes,
        process_times=ProcessTimes(train_to_hump_delay=5.0, wagon_hump_interval=1.0))

    # Run simulation
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)

    print(f'\nInitial capacity: {popup_sim.track_capacity.track_capacities["collection_1"]:.1f}m')
    print(f'Current usage: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m')

    # Simulate adding wagons
    for wagon in wagons:
        can_add = popup_sim.track_capacity.can_add_wagon('collection_1', wagon.length)
        if can_add:
            popup_sim.track_capacity.add_wagon('collection_1', wagon.length)
            print(
                f'[+] Added {wagon.wagon_id} ({wagon.length}m) - Usage: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m'
            )
        else:
            print(f'[-] Rejected {wagon.wagon_id} ({wagon.length}m) - Capacity exceeded!')

    print(
        f'\nFinal usage: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m / {popup_sim.track_capacity.track_capacities["collection_1"]:.1f}m'
    )
    print('Result: [+] All wagons accepted')


def scenario_exceeds_capacity() -> None:
    """Scenario 2: Wagons exceed 75% capacity."""
    print('\n' + '=' * 60)
    print('SCENARIO 2: Exceeds Capacity')
    print('=' * 60)
    print('Track length: 100m')
    print('Capacity (75%): 75m')
    print('Wagons: 5 wagons × 20m = 100m total')
    print('-' * 60)

    topology = Topology(create_simple_topology())
    wagons = [Wagon(wagon_id=f'W{i}', length=20.0, is_loaded=False, needs_retrofit=True) for i in range(1, 6)]
    train = Train(train_id='T1', arrival_time=datetime(2031, 7, 4, 8, 0, 0, tzinfo=UTC), wagons=wagons)
    
    tracks = [
        Track(id='parking', type=TrackType.PARKING, edges=['edge_1']),
        Track(id='collection_1', type=TrackType.COLLECTION, edges=['edge_1']),
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['edge_1']),
    ]
    
    loco = Locomotive(locomotive_id='L1', name='Loco 1',
                     start_date=datetime(2031, 7, 4, 0, 0, 0, tzinfo=UTC),
                     end_date=datetime(2031, 7, 5, 0, 0, 0, tzinfo=UTC), track_id='parking')
    
    routes = [
        Route(route_id='parking_to_collection', path=['parking', 'collection_1'], duration=1.0),
        Route(route_id='collection_to_retrofitted', path=['collection_1', 'retrofitted'], duration=1.0),
    ]
    
    scenario = Scenario(
        scenario_id='exceeds_capacity', start_date=datetime(2031, 7, 4, 0, 0, 0, tzinfo=UTC),
        end_date=datetime(2031, 7, 5, 0, 0, 0, tzinfo=UTC), trains=[train], tracks=tracks,
        locomotives=[loco], workshops=[], topology=topology, routes=routes,
        process_times=ProcessTimes(train_to_hump_delay=5.0, wagon_hump_interval=1.0))

    # Run simulation
    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)

    print(f'\nInitial capacity: {popup_sim.track_capacity.track_capacities["collection_1"]:.1f}m')
    print(f'Current usage: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m')

    # Simulate adding wagons
    accepted = 0
    rejected = 0
    for wagon in wagons:
        can_add = popup_sim.track_capacity.can_add_wagon('collection_1', wagon.length)
        if can_add:
            popup_sim.track_capacity.add_wagon('collection_1', wagon.length)
            accepted += 1
            print(
                f'[+] Added {wagon.wagon_id} ({wagon.length}m) - Usage: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m'
            )
        else:
            rejected += 1
            print(f'[-] Rejected {wagon.wagon_id} ({wagon.length}m) - Capacity exceeded!')

    print(
        f'\nFinal usage: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m / {popup_sim.track_capacity.track_capacities["collection_1"]:.1f}m'
    )
    print(f'Result: [+] {accepted} accepted, [-] {rejected} rejected')


if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('PopUpSim Track Capacity Management Demo')
    print('=' * 60)

    scenario_within_capacity()
    scenario_exceeds_capacity()

    print('\n' + '=' * 60)
    print('Demo Complete')
    print('=' * 60 + '\n')
