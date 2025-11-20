"""Test scenario with 1 train, 20 wagons, 1 loco."""

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Topology
topology_data = {
    'edges': [
        {'id': 'parking_1_edge', 'length': 50.0},
        {'id': 'collection_1_edge', 'length': 500.0},
        {'id': 'retrofit_1_edge', 'length': 500.0},
        {'id': 'retrofitted_edge', 'length': 500.0},
    ]
}

# Tracks
parking_1 = Track(id='parking_1', type=TrackType.PARKING, edges=['parking_1_edge'])
collection_1 = Track(id='collection_1', type=TrackType.COLLECTION, edges=['collection_1_edge'])
retrofit_1 = Track(id='retrofit_1', type=TrackType.RETROFIT, edges=['retrofit_1_edge'])
retrofitted_track = Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['retrofitted_edge'])

tracks = [parking_1, collection_1, retrofit_1, retrofitted_track]

# Routes
routes = [
    Route(route_id='parking1_to_col1', path=['parking_1', 'collection_1'], duration=2),
    Route(route_id='col1_to_ret1', path=['collection_1', 'retrofit_1'], duration=3),
    Route(route_id='ret1_to_retrofitted', path=['retrofit_1', 'retrofitted'], duration=2),
    Route(route_id='retrofitted_to_parking1', path=['retrofitted', 'parking_1'], duration=3),
    Route(route_id='ret1_to_parking1', path=['retrofit_1', 'parking_1'], duration=3),
    Route(route_id='ret1_to_ws1', path=['retrofit_1', 'WS1'], duration=2.0),
    Route(route_id='ws1_to_ret1', path=['WS1', 'retrofit_1'], duration=2.0),
]

# Start time
start_time = datetime(2025, 1, 1, 8, 0, 0, tzinfo=UTC)

# One locomotive
locos = [
    Locomotive(
        locomotive_id='loco_1',
        name='Loco 1',
        start_date=start_time,
        end_date=start_time + timedelta(hours=12),
        track_id='parking_1',
    ),
]

# Process times (DAC coupling is faster than screw coupling)
process_times = ProcessTimes(
    train_to_hump_delay=5.0,
    wagon_hump_interval=1.0,
    wagon_coupling_time=2.0,  # Screw coupler (slow)
    wagon_decoupling_time=0.5,
    wagon_move_to_next_station=1.0,
    wagon_coupling_retrofitted_time=0.5,  # DAC coupler (fast)
    wagon_retrofit_time=30.0,
)

# Train 1 with 20 wagons (20m each = 400m total)
wagons_1 = [
    Wagon(wagon_id=f'W{i:02d}', length=20.0, needs_retrofit=True, is_loaded=False)
    for i in range(1, 21)
]
train_1 = Train(train_id='train_001', arrival_time=start_time, wagons=wagons_1)

# Workshop with 4 retrofit stations
workshops = [
    Workshop(
        workshop_id='WS1',
        start_date='2025-01-01 08:00:00',
        end_date='2025-01-02 08:00:00',
        track_id='retrofit_1',
        retrofit_stations=4,
    ),
]

# Scenario
scenario = Scenario(
    scenario_id='test_20_wagons',
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
sim = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim, scenario)
popup_sim.run(until=400.0)

# Print results
print('\n=== WORKSHOP STATION HISTORY ===')
for track_id in ['retrofit_1']:
    print(f'\n{track_id}:')
    stations = popup_sim.workshop_capacity.stations.get(track_id, [])
    for station in stations:
        print(f'  {station.station_id}: {station.wagons_completed} wagons completed')
        for start_time, end_time, wagon_id in station.history:
            duration = end_time - start_time
            print(f'    t={start_time:5.1f}-{end_time:5.1f}min ({duration:4.1f}min): {wagon_id}')
        if station.is_occupied and station.current_wagon_id:
            print(f'    t={station.last_occupied_time:5.1f}-???     (WORKING): {station.current_wagon_id}')

print('\n=== WAGON STATUS SUMMARY ===')
status_counts = {}
for wagon in train_1.wagons:
    status = wagon.status.value
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in sorted(status_counts.items()):
    print(f'  {status}: {count} wagons')

print(f'\nSimulation time: {sim.current_time():.1f} minutes')
print(f'Total wagons processed: {sum(s.wagons_completed for s in popup_sim.workshop_capacity.stations["retrofit_1"])}')

print('\n=== DETAILED WAGON STATUS ===')
for wagon in train_1.wagons:
    print(f'{wagon.wagon_id}: {wagon.status.value:20s} track={wagon.track_id or "None":15s} '
          f'coupler={wagon.coupler_type.value}')
