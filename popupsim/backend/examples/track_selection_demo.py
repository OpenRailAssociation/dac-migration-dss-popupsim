"""Demo of all four track selection strategies with multiple collection tracks."""

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
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter


def create_topology_with_two_tracks() -> dict:
    """Create topology with two collection tracks."""
    return {'edges': [{'id': 'e1', 'length': 100.0}, {'id': 'e2', 'length': 100.0}]}


def run_strategy_demo(strategy: TrackSelectionStrategy) -> None:
    """Run demo for a specific track selection strategy."""
    print(f'\n{"=" * 60}')
    print(f'Strategy: {strategy.value.upper().replace("_", " ")}')
    print(f'{"=" * 60}')

    topology_data = create_topology_with_two_tracks()
    topology = Topology(topology_data)

    # Create 6 wagons with varying lengths (total = 130m)
    wagon_lengths = [15.0, 25.0, 20.0, 30.0, 20.0, 20.0]
    wagons = [
        Wagon(wagon_id=f'W{i}', length=wagon_lengths[i - 1], is_loaded=False, needs_retrofit=True) for i in range(1, 7)
    ]

    train = Train(train_id='T1', arrival_time=datetime(2031, 7, 4, 8, 0, 0, tzinfo=UTC), wagons=wagons)

    tracks = [
        Track(id='parking', type=TrackType.PARKING, edges=['e1']),
        Track(id='collection_1', type=TrackType.COLLECTION, edges=['e1']),
        Track(id='collection_2', type=TrackType.COLLECTION, edges=['e2']),
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['e1']),
    ]

    loco = Locomotive(locomotive_id='L1', name='Loco 1',
                     start_date=datetime(2031, 7, 4, 0, 0, 0, tzinfo=UTC),
                     end_date=datetime(2031, 7, 5, 0, 0, 0, tzinfo=UTC), track_id='parking')

    routes = [
        Route(route_id='parking_to_col1', path=['parking', 'collection_1'], duration=1.0),
        Route(route_id='parking_to_col2', path=['parking', 'collection_2'], duration=1.0),
    ]

    scenario = Scenario(
        scenario_id=f'demo_{strategy.value}', start_date=datetime(2031, 7, 4, 0, 0, 0, tzinfo=UTC),
        end_date=datetime(2031, 7, 5, 0, 0, 0, tzinfo=UTC), trains=[train], tracks=tracks,
        locomotives=[loco], workshops=[], topology=topology, routes=routes,
        process_times=ProcessTimes(train_to_hump_delay=5.0, wagon_hump_interval=1.0),
        track_selection_strategy=strategy)

    sim = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim, scenario)

    print(f'Track 1 capacity: {popup_sim.track_capacity.track_capacities["collection_1"]:.1f}m')
    print(f'Track 2 capacity: {popup_sim.track_capacity.track_capacities["collection_2"]:.1f}m')
    print('Wagons: 15m, 25m, 20m, 30m, 20m, 20m (total 130m)')
    print('-' * 60)

    # Simulate wagon selection
    for wagon in wagons:
        track_id = popup_sim.track_capacity.select_collection_track(wagon.length)
        if track_id:
            popup_sim.track_capacity.add_wagon(track_id, wagon.length)
            usage = popup_sim.track_capacity.current_occupancy[track_id]
            print(f'[+] {wagon.wagon_id} ({wagon.length}m) -> {track_id}: {usage:.1f}m')
        else:
            print(f'[-] {wagon.wagon_id} ({wagon.length}m) -> REJECTED')

    print('\nFinal distribution:')
    print(f'  Track 1: {popup_sim.track_capacity.current_occupancy["collection_1"]:.1f}m / 75.0m')
    print(f'  Track 2: {popup_sim.track_capacity.current_occupancy["collection_2"]:.1f}m / 75.0m')


if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('Track Selection Strategy Comparison')
    print('=' * 60)
    print('Scenario: 2 tracks (100m each, 75m capacity)')
    print('          6 wagons (varying lengths: 15m, 25m, 20m, 30m, 20m, 20m)')

    for strategy in TrackSelectionStrategy:
        run_strategy_demo(strategy)

    print('\n' + '=' * 60)
    print('Demo Complete')
    print('=' * 60 + '\n')
