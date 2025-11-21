"""Simple test scenario with 1 train, 4 wagons, 1 loco."""

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

start_time = datetime(2025, 1, 1, 8, 0, 0, tzinfo=UTC)

topology_data = {'edges': [{'id': 'e1', 'length': 100.0}]}

tracks = [
    Track(id='parking', type=TrackType.PARKING, edges=['e1']),
    Track(id='collection', type=TrackType.COLLECTION, edges=['e1']),
    Track(id='retrofit', type=TrackType.RETROFIT, edges=['e1']),
    Track(id='WS1', type=TrackType.WORKSHOP, edges=['e1']),
    Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['e1']),
]

routes = [
    Route(route_id='parking_to_collection', path=['parking', 'collection'], duration=1.0),
    Route(route_id='collection_to_retrofit', path=['collection', 'retrofit'], duration=1.0),
    Route(route_id='retrofit_to_parking', path=['retrofit', 'parking'], duration=1.0),
    Route(route_id='parking_to_retrofit', path=['parking', 'retrofit'], duration=1.0),
    Route(route_id='retrofit_to_WS1', path=['retrofit', 'WS1'], duration=1.0),
    Route(route_id='WS1_to_parking', path=['WS1', 'parking'], duration=1.0),
    Route(route_id='parking_to_WS1', path=['parking', 'WS1'], duration=1.0),
    Route(route_id='WS1_to_retrofitted', path=['WS1', 'retrofitted'], duration=1.0),
    Route(route_id='retrofitted_to_parking', path=['retrofitted', 'parking'], duration=1.0),
]

locos = [Locomotive(locomotive_id='L1', name='Loco 1', start_date=start_time,
                    end_date=start_time + timedelta(hours=2), track_id='parking')]

process_times = ProcessTimes(
    train_to_hump_delay=0.0, wagon_hump_interval=0.0, wagon_coupling_time=0.0,
    wagon_decoupling_time=0.0, wagon_move_to_next_station=0.0,
    wagon_coupling_retrofitted_time=0.0, wagon_retrofit_time=10.0)

wagons = [Wagon(wagon_id=f'W0{i}', length=20.0, needs_retrofit=True, is_loaded=False) for i in range(1, 5)]
train = Train(train_id='T1', arrival_time=start_time, wagons=wagons)

workshops = [Workshop(workshop_id='WS1', start_date='2025-01-01 08:00:00',
                     end_date='2025-01-02 08:00:00', track_id='WS1', retrofit_stations=4)]

scenario = Scenario(
    scenario_id='simple_test', start_date=start_time, end_date=start_time + timedelta(days=1),
    locomotives=locos, process_times=process_times, routes=routes,
    topology=Topology(topology_data), trains=[train], tracks=tracks, workshops=workshops)

sim = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim, scenario)
popup_sim.run(until=50.0)

print('\n=== WORKSHOP STATION HISTORY ===')
stations = popup_sim.workshop_capacity.stations.get('WS1', [])
for station in stations:
    print(f'{station.station_id}: {station.wagons_completed} wagons')
    for start, end, wid in station.history:
        print(f'  t={start:.1f}-{end:.1f} ({end-start:.1f}min): {wid}')

print('\n=== WAGON STATUS ===')
for wagon in popup_sim.wagons_queue:
    print(f'{wagon.wagon_id}: {wagon.status.value} on {wagon.track_id}')
