"""Demonstration of multi-track scenario with 3 collection tracks, 2 retrofit tracks, 2 locos."""

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

from models.topology import Topology
from models.track import Track
from models.track import TrackType
from models.train import Train
from models.wagon import Wagon
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Track capacity events
capacity_events = []

# Topology with track lengths
topology_data = {
    'edges': [
        {'id': 'parking_1_edge', 'length': 50.0},
        {'id': 'parking_2_edge', 'length': 60.0},
        {'id': 'collection_1_edge', 'length': 100.0},
        {'id': 'collection_2_edge', 'length': 120.0},
        {'id': 'collection_3_edge', 'length': 80.0},
        {'id': 'retrofit_1_edge', 'length': 150.0},
        {'id': 'retrofit_2_edge', 'length': 130.0},
        {'id': 'retrofitted_edge', 'length': 200.0},
    ]
}

# Tracks
parking_1 = Track(id='parking_1', type=TrackType.PARKING, edges=['parking_1_edge'])
parking_2 = Track(id='parking_2', type=TrackType.PARKING, edges=['parking_2_edge'])
collection_1 = Track(id='collection_1', type=TrackType.COLLECTION, edges=['collection_1_edge'])
collection_2 = Track(id='collection_2', type=TrackType.COLLECTION, edges=['collection_2_edge'])
collection_3 = Track(id='collection_3', type=TrackType.COLLECTION, edges=['collection_3_edge'])
retrofit_1 = Track(id='retrofit_1', type=TrackType.RETROFIT, edges=['retrofit_1_edge'])
retrofit_2 = Track(id='retrofit_2', type=TrackType.RETROFIT, edges=['retrofit_2_edge'])
retrofitted_track = Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['retrofitted_edge'])

tracks = [parking_1, parking_2, collection_1, collection_2, collection_3, retrofit_1, retrofit_2, retrofitted_track]

# Routes between tracks
routes = [
    Route(route_id='parking1_to_col1', path=['parking_1', 'collection_1'], duration=2),
    Route(route_id='parking1_to_col2', path=['parking_1', 'collection_2'], duration=3),
    Route(route_id='parking1_to_col3', path=['parking_1', 'collection_3'], duration=3),
    Route(route_id='col1_to_ret1', path=['collection_1', 'retrofit_1'], duration=3),
    Route(route_id='col1_to_ret2', path=['collection_1', 'retrofit_2'], duration=4),
    Route(route_id='col2_to_ret1', path=['collection_2', 'retrofit_1'], duration=3),
    Route(route_id='col2_to_ret2', path=['collection_2', 'retrofit_2'], duration=3),
    Route(route_id='col3_to_ret1', path=['collection_3', 'retrofit_1'], duration=4),
    Route(route_id='col3_to_ret2', path=['collection_3', 'retrofit_2'], duration=2),
    Route(route_id='ret1_to_retrofitted', path=['retrofit_1', 'retrofitted'], duration=2),
    Route(route_id='ret2_to_retrofitted', path=['retrofit_2', 'retrofitted'], duration=2),
    Route(route_id='retrofitted_to_parking1', path=['retrofitted', 'parking_1'], duration=3),
    Route(route_id='retrofitted_to_parking2', path=['retrofitted', 'parking_2'], duration=3),
    Route(route_id='ret1_to_parking1', path=['retrofit_1', 'parking_1'], duration=3),
    Route(route_id='ret2_to_parking1', path=['retrofit_2', 'parking_1'], duration=4),
]

# Start time
start_time = datetime(2025, 1, 1, 8, 0, 0, tzinfo=UTC)

# Two locomotives
locos = [
    Locomotive(
        locomotive_id='loco_1',
        name='Loco 1',
        start_date=start_time,
        end_date=start_time + timedelta(hours=10),
        track_id='parking_1',
    ),
    Locomotive(
        locomotive_id='loco_2',
        name='Loco 2',
        start_date=start_time,
        end_date=start_time + timedelta(hours=10),
        track_id='parking_1',
    ),
]

# Process times
process_times = ProcessTimes(
    train_to_hump_delay=5.0,
    wagon_hump_interval=1.0,
    wagon_coupling_time=0.5,
    wagon_decoupling_time=0.5,
    wagon_move_to_next_station=1.0,
    wagon_coupling_retrofitted_time=0.5,
    wagon_retrofit_time=30.0,  # 30 minutes per wagon
)

# Train 1 with 8 wagons (varying lengths: 25m, 15m, 30m, 20m, 25m, 15m, 20m, 30m = 180m total)
wagon_lengths_1 = [25.0, 15.0, 30.0, 20.0, 25.0, 15.0, 20.0, 30.0]
wagons_1 = [
    Wagon(wagon_id=f'T1W{i:02d}', length=wagon_lengths_1[i - 1], needs_retrofit=True, is_loaded=False)
    for i in range(1, 9)
]
train_1 = Train(train_id='train_001', arrival_time=start_time, wagons=wagons_1)

# Train 2 with 6 small wagons (10m each = 60m total) arriving 25 minutes later to fill gaps
wagons_2 = [Wagon(wagon_id=f'T2W{i:02d}', length=10.0, needs_retrofit=True, is_loaded=False) for i in range(1, 7)]
train_2 = Train(train_id='train_002', arrival_time=start_time + timedelta(minutes=25), wagons=wagons_2)

ws1_track = Track(id='WS1', type=TrackType.WORKSHOP, edges=['retrofit_1_edge'])
ws2_track = Track(id='WS2', type=TrackType.WORKSHOP, edges=['retrofit_2_edge'])
tracks.extend([ws1_track, ws2_track])

routes.extend([
    Route(route_id='parking1_to_ws1', path=['parking_1', 'WS1'], duration=2.0),
    Route(route_id='parking1_to_ws2', path=['parking_1', 'WS2'], duration=2.0),
    Route(route_id='ret1_to_ws1', path=['retrofit_1', 'WS1'], duration=2.0),
    Route(route_id='ret1_to_ws2', path=['retrofit_1', 'WS2'], duration=3.0),
    Route(route_id='ret2_to_ws1', path=['retrofit_2', 'WS1'], duration=3.0),
    Route(route_id='ret2_to_ws2', path=['retrofit_2', 'WS2'], duration=2.0),
    Route(route_id='ws1_to_retrofitted', path=['WS1', 'retrofitted'], duration=2.0),
    Route(route_id='ws2_to_retrofitted', path=['WS2', 'retrofitted'], duration=2.0),
])

workshops = [
    Workshop(workshop_id='WS1', start_date='2025-01-01 08:00:00',
            end_date='2025-01-04 08:00:00', track_id='WS1', retrofit_stations=4),
    Workshop(workshop_id='WS2', start_date='2025-01-01 08:00:00',
            end_date='2025-01-04 08:00:00', track_id='WS2', retrofit_stations=3),
]

scenario = Scenario(
    scenario_id='multi_track_demo', start_date=start_time,
    end_date=start_time + timedelta(days=1), locomotives=locos,
    process_times=process_times, routes=routes, topology=Topology(topology_data),
    trains=[train_1, train_2], tracks=tracks, workshops=workshops)

# Run simulation with capacity tracking
sim = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim, scenario)

# Monkey-patch to track capacity changes
original_add = popup_sim.track_capacity.add_wagon
original_remove = popup_sim.track_capacity.remove_wagon


def tracked_add(track_id: str, wagon_length: float) -> bool:
    result = original_add(track_id, wagon_length)
    if result:
        capacity_events.append(
            {
                'time': float(sim.current_time()),
                'action': 'ADD',
                'track': track_id,
                'length': wagon_length,
                'occupancy': popup_sim.track_capacity.current_occupancy[track_id],
                'capacity': popup_sim.track_capacity.track_capacities[track_id],
            }
        )
    return result


def tracked_remove(track_id: str, wagon_length: float) -> None:
    original_remove(track_id, wagon_length)
    if track_id in popup_sim.track_capacity.current_occupancy:
        capacity_events.append({
            'time': float(sim.current_time()), 'action': 'REMOVE', 'track': track_id,
            'length': wagon_length, 'occupancy': popup_sim.track_capacity.current_occupancy[track_id],
            'capacity': popup_sim.track_capacity.track_capacities[track_id]})


popup_sim.track_capacity.add_wagon = tracked_add
popup_sim.track_capacity.remove_wagon = tracked_remove

popup_sim.run(until=1000.0)

# Display metrics
metrics = popup_sim.get_metrics()
print('\n=== SIMULATION METRICS ===')
for category, category_metrics in metrics.items():
    print(f'\n{category.upper().replace("_", " ")}:')
    for metric in category_metrics:
        print(f"  {metric['name'].replace('_', ' ').title()}: {metric['value']} {metric['unit']}")

# Print results
print('\n=== SIMULATION RESULTS ===')
print('\nFinal Collection Track Capacities (75% fill):')
for track_id in ['collection_1', 'collection_2', 'collection_3']:
    capacity = popup_sim.track_capacity.track_capacities[track_id]
    occupancy = popup_sim.track_capacity.current_occupancy[track_id]
    pct = (occupancy / capacity * 100) if capacity > 0 else 0
    wagons_on_track = [w for w in popup_sim.wagons_queue if w.track_id == track_id]
    print(f'  {track_id}: {occupancy:.1f}m / {capacity:.1f}m ({pct:.1f}%) - {len(wagons_on_track)} wagons in queue')

print('\nFinal Retrofit Track Capacities (75% fill):')
for track_id in ['retrofit_1', 'retrofit_2']:
    capacity = popup_sim.track_capacity.track_capacities[track_id]
    occupancy = popup_sim.track_capacity.current_occupancy[track_id]
    pct = (occupancy / capacity * 100) if capacity > 0 else 0
    print(f'  {track_id}: {occupancy:.1f}m / {capacity:.1f}m ({pct:.1f}%)')

print('\nWorkshop Retrofit Stations:')
for track_id in ['WS1', 'WS2']:
    total_stations = popup_sim.workshop_capacity.workshops_by_track[track_id].retrofit_stations
    occupied = sum(1 for s in popup_sim.workshop_capacity.stations[track_id] if s.is_occupied)
    available = total_stations - occupied
    print(f'  {track_id}: {occupied}/{total_stations} stations occupied ({available} available)')

print('\n=== WORKSHOP STATION HISTORY ===')
for track_id in ['WS1', 'WS2']:
    print(f'\n{track_id}:')
    stations = popup_sim.workshop_capacity.stations.get(track_id, [])
    for station in stations:
        print(f'  {station.station_id}: {station.wagons_completed} wagons completed')
        for start_time, end_time, wagon_id in station.history:
            duration = end_time - start_time
            print(f'    t={start_time:5.1f}-{end_time:5.1f}min ({duration:4.1f}min): {wagon_id}')
        if station.is_occupied and station.current_wagon_id:
            print(f'    t={station.last_occupied_time:5.1f}-???     (WORKING): {station.current_wagon_id}')

print('\nFinal Wagon Distribution (from wagons_queue):')
wagons_by_track = {}
for wagon in popup_sim.wagons_queue:
    track = wagon.track_id or 'in_transit'
    if track not in wagons_by_track:
        wagons_by_track[track] = []
    wagons_by_track[track].append(
        (wagon.wagon_id, wagon.status.value, wagon.source_track_id, wagon.destination_track_id)
    )

for track_id, wagon_info in sorted(wagons_by_track.items()):
    print(f'  {track_id}: {len(wagon_info)} wagons')
    for wagon_id, status, source, destination in wagon_info:
        if status == 'moving' and source and destination:
            print(f'    - {wagon_id} (moving: {source} -> {destination})')
        elif status == 'retrofitted':
            print(f'    - {wagon_id} ({status}) [waiting for locomotive pickup]')
        else:
            print(f'    - {wagon_id} ({status})')

print('\nAll Train Wagons Status:')
for train in popup_sim.scenario.trains:
    print(f'  {train.train_id}:')
    for wagon in train.wagons:
        in_queue = 'in queue' if wagon in popup_sim.wagons_queue else 'NOT in queue'
        if wagon.status.value == 'moving' and wagon.source_track_id and wagon.destination_track_id:
            location = f'{wagon.source_track_id} -> {wagon.destination_track_id}'
        else:
            location = wagon.track_id or 'unknown'
        print(f'    - {wagon.wagon_id}: {wagon.status.value} on {location} ({in_queue})')

print('\nLocomotive Status:')
for loco_id, loco in sorted(popup_sim.locomotives.all_resources.items()):
    print(f'  {loco_id}: {loco.status.value} at {loco.track_id}')

print('\n=== LOCOMOTIVE METRICS ===')
total_sim_time = sim.current_time()

print('\nPool Allocation Time (checked out from pool):')
pool_utilization = popup_sim.locomotives.get_utilization(total_sim_time)
for loco_id in sorted(pool_utilization.keys()):
    print(f'  {loco_id}: {pool_utilization[loco_id]:.1f}% allocated')

print('\nOperational Status Time (what locomotive is doing):')
for loco_id, loco in sorted(popup_sim.locomotives.all_resources.items()):
    status_utilization = loco.get_utilization(total_sim_time)
    print(f'  {loco_id}:')
    for status, percentage in sorted(status_utilization.items()):
        print(f'    {status}: {percentage:.1f}%')

print('\n=== RESOURCE TRACKING ===')
print('\nCurrent Locomotive States:')
for loco_id, state in popup_sim.locomotives.get_all_states().items():
    status_str = state["status"].value if hasattr(state["status"], 'value') else str(state["status"])
    print(f'  {loco_id}: {status_str} at {state["location"]} (allocated={state["allocated"]})')

print(f'\nAvailable locomotives: {popup_sim.locomotives.get_available_count()}/{len(popup_sim.locomotives.all_resources)}')

print('\nAllocation History (last 10 events):')
for time, loco_id, action, location in popup_sim.locomotives.allocation_history[-10:]:
    print(f'  t={time:5.1f}min: {loco_id} {action} at {location}')

# Print capacity timeline
print('\n=== CAPACITY TIMELINE ===')

print('\nCollection Tracks:')
col_events = [e for e in capacity_events if e['track'].startswith('collection')]
for event in col_events:
    action_symbol = '+' if event['action'] == 'ADD' else '-'
    pct = (event['occupancy'] / event['capacity'] * 100) if event['capacity'] > 0 else 0
    print(
        f'  t={event["time"]:5.1f}min [{action_symbol}] {event["track"]}: {event["length"]:.0f}m -> {event["occupancy"]:.0f}m/{event["capacity"]:.0f}m ({pct:.0f}%)'
    )

print('\nRetrofit Tracks:')
ret_events = [e for e in capacity_events if e['track'].startswith('retrofit')]
for event in ret_events:
    action_symbol = '+' if event['action'] == 'ADD' else '-'
    pct = (event['occupancy'] / event['capacity'] * 100) if event['capacity'] > 0 else 0
    print(
        f'  t={event["time"]:5.1f}min [{action_symbol}] {event["track"]}: {event["length"]:.0f}m -> {event["occupancy"]:.0f}m/{event["capacity"]:.0f}m ({pct:.0f}%)'
    )

print('\nRetrofitted Track:')
retrofitted_events = [e for e in capacity_events if e['track'] == 'retrofitted']
for event in retrofitted_events:
    action_symbol = '+' if event['action'] == 'ADD' else '-'
    pct = (event['occupancy'] / event['capacity'] * 100) if event['capacity'] > 0 else 0
    print(
        f'  t={event["time"]:5.1f}min [{action_symbol}] {event["track"]}: {event["length"]:.0f}m -> {event["occupancy"]:.0f}m/{event["capacity"]:.0f}m ({pct:.0f}%)'
    )

print('\nParking Tracks:')
parking_events = [e for e in capacity_events if e['track'].startswith('parking')]
for event in parking_events:
    action_symbol = '+' if event['action'] == 'ADD' else '-'
    pct = (event['occupancy'] / event['capacity'] * 100) if event['capacity'] > 0 else 0
    print(
        f'  t={event["time"]:5.1f}min [{action_symbol}] {event["track"]}: {event["length"]:.0f}m -> {event["occupancy"]:.0f}m/{event["capacity"]:.0f}m ({pct:.0f}%)'
    )
