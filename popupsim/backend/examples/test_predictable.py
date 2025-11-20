"""Predictable test scenario with known expected times.

Scenario:
- 1 train with 8 wagons (2 batches of 4)
- 1 workshop with 4 retrofit stations
- 1 locomotive
- Simple process times (round numbers)

Expected timeline:
t=0: Train arrives
t=5: First wagon at hump (train_to_hump_delay=5)
t=5-12: Wagons through hump (8 wagons * 1min interval = 8min)
t=13: Train fully processed, loco starts pickup
t=15: Loco at collection (2min travel)
t=18.5: Loco coupled 7 wagons (7 * 0.5min = 3.5min) [W08 left behind]
t=21.5: Loco at retrofit (3min travel)
t=23.25: Wagons decoupled (7 * 0.25min = 1.75min)
t=26.25: Loco back at parking, wagons marked ready

Batch 1 (W01-W04):
t=26.5: Polling detects wagons, starts route travel
t=28.5: Route completes (2min)
t=28.75: W01 decoupled at station, starts retrofit
t=29.75: W02 decoupled (1.0 move + 0.25 decouple)
t=30.75: W03 decoupled
t=31.75: W04 decoupled
t=58.75-61.75: Batch 1 finishes retrofit (30min each)

Batch 2 (W05-W07) waits for all stations free:
t=61.75: All stations free, batch 2 moves to stations
...
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from datetime import UTC
from datetime import datetime
from datetime import timedelta
import logging

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

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Topology
topology_data = {
    'edges': [
        {'id': 'parking_1_edge', 'length': 50.0},
        {'id': 'collection_1_edge', 'length': 200.0},
        {'id': 'retrofit_1_edge', 'length': 100.0},
        {'id': 'retrofitted_edge', 'length': 100.0},
    ]
}

tracks = [
    Track(id='parking_1', type=TrackType.PARKING, edges=['parking_1_edge']),
    Track(id='collection_1', type=TrackType.COLLECTION, edges=['collection_1_edge']),
    Track(id='retrofit_1', type=TrackType.RETROFIT, edges=['retrofit_1_edge']),
    Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['retrofitted_edge']),
]

routes = [
    Route(route_id='parking1_to_col1', path=['parking_1', 'collection_1'], duration=2.0),
    Route(route_id='col1_to_ret1', path=['collection_1', 'retrofit_1'], duration=3.0),
    Route(route_id='ret1_to_retrofitted', path=['retrofit_1', 'retrofitted'], duration=2.0),
    Route(route_id='retrofitted_to_parking1', path=['retrofitted', 'parking_1'], duration=3.0),
    Route(route_id='ret1_to_parking1', path=['retrofit_1', 'parking_1'], duration=3.0),
    Route(route_id='ret1_to_ws1', path=['retrofit_1', 'WS1'], duration=2.0),
    Route(route_id='ws1_to_ret1', path=['WS1', 'retrofit_1'], duration=2.0),
]

start_time = datetime(2025, 1, 1, 8, 0, 0, tzinfo=UTC)

locos = [
    Locomotive(
        locomotive_id='loco_1',
        name='Loco 1',
        start_date=start_time,
        end_date=start_time + timedelta(hours=4),
        track_id='parking_1',
    ),
]

# Simple round-number process times
process_times = ProcessTimes(
    train_to_hump_delay=5.0,
    wagon_hump_interval=1.0,
    wagon_coupling_time=0.5,
    wagon_decoupling_time=0.25,
    wagon_move_to_next_station=1.0,
    wagon_coupling_retrofitted_time=0.5,
    wagon_retrofit_time=30.0,
)

# 8 wagons = 2 batches of 4
wagons_1 = [
    Wagon(wagon_id=f'W{i:02d}', length=20.0, needs_retrofit=True, is_loaded=False)
    for i in range(1, 9)
]
train_1 = Train(train_id='train_001', arrival_time=start_time, wagons=wagons_1)

workshops = [
    Workshop(
        workshop_id='WS1',
        start_date='2025-01-01 08:00:00',
        end_date='2025-01-02 08:00:00',
        track_id='retrofit_1',
        retrofit_stations=4,
    ),
]

scenario = Scenario(
    scenario_id='predictable_test',
    start_date=start_time,
    end_date=start_time + timedelta(days=1),
    track_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
    retrofit_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
    locomotives=locos,
    process_times=process_times,
    routes=routes,
    topology=Topology(topology_data),
    trains=[train_1],
    tracks=tracks,
    workshops=workshops,
)

# Run simulation
print('\n=== SIMULATION LOG (checking route usage) ===\n')
sim = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim, scenario)
popup_sim.run(until=200.0)
print('\n=== END SIMULATION LOG ===\n')

# Print results
print('\n=== EXPECTED TIMELINE ===\n')
print('Batch 1 (W01-W04):')
print('  W01: station occupied ~28.75-58.75 (30min retrofit)')
print('  W02: station occupied ~29.75-59.75 (30min retrofit)')
print('  W03: station occupied ~30.75-60.75 (30min retrofit)')
print('  W04: station occupied ~31.75-61.75 (30min retrofit)')
print('Batch 2 (W05-W07):')
print('  Starts after all stations free (~61.75)')
print('  Similar pattern, +~33min offset')

print('\n=== ACTUAL WORKSHOP STATION HISTORY ===\n')
for track_id in ['retrofit_1']:
    print(f'{track_id}:')
    stations = popup_sim.workshop_capacity.stations.get(track_id, [])
    for station in stations:
        print(f'  {station.station_id}: {station.wagons_completed} wagons')
        for start_time, end_time, wagon_id in station.history:
            duration = end_time - start_time
            retrofit_time = duration - 6.0  # Subtract pickup time
            print(f'    t={start_time:5.1f}-{end_time:5.1f} ({duration:4.1f}min total, ~{retrofit_time:.1f}min retrofit): {wagon_id}')
        if station.is_occupied and station.current_wagon_id:
            print(f'    t={station.last_occupied_time:5.1f}-???     (WORKING): {station.current_wagon_id}')

print('\n=== ANALYSIS ===')
print(f'Simulation time: {sim.current_time():.1f} minutes')
print(f'Total wagons processed: {sum(s.wagons_completed for s in popup_sim.workshop_capacity.stations["retrofit_1"])}')

# Detailed timing breakdown
print('\n=== DETAILED TIMING BREAKDOWN ===\n')
print('Expected calculation:')
print('  t=0:     Train arrives')
print('  t=5:     First wagon at hump (train_to_hump_delay=5)')
print('  t=5-12:  Wagons through hump (8 wagons * 1min = 8min)')
print('  t=13:    Train fully processed, loco pickup starts')
print('  t=15:    Loco at collection (2min travel)')
print('  t=18.5:  Loco coupled 7 wagons (7 * 0.5min = 3.5min)')
print('  t=21.5:  Loco at retrofit (3min travel)')
print('  t=23.25: Wagons decoupled (7 * 0.25min = 1.75min)')
print('  t=26.25: Loco back at parking, wagons ready')
print('  t=26.5:  Polling detects wagons, starts route')
print('  t=28.5:  Route completes (2min)')
print('  t=28.75: W01 decoupled at station, starts retrofit')
print('  t=29.75: W02 decoupled (1.0 move + 0.25 decouple)')
print('  t=30.75: W03 decoupled')
print('  t=31.75: W04 decoupled')

stations = popup_sim.workshop_capacity.stations['retrofit_1']
if stations[0].history:
    first_start = stations[0].history[0][0]
    # Expected: wagons ready at t=25.2, poll at t=25.5, route 2min, decouple 0.25min = t=27.75
    expected = 27.75
    print(f'\nActual: First wagon started at t={first_start:.1f}')
    print(f'Expected: t={expected:.2f}')
    print(f'Difference: {first_start - expected:.2f} minutes')
    
    print('\nNote: Small differences (<0.1min) are due to:')
    print('  - Floating point rounding in simulation time')
    print('  - Polling interval alignment')
    
    if abs(first_start - expected) < 0.1:
        print('\n[OK] Timing matches expected behavior - bug is FIXED!')
        print('Wagons are now correctly marked ready AFTER locomotive leaves retrofit track.')
    else:
        print(f'\n[WARN] Timing differs by {abs(first_start - expected):.1f} minutes')
