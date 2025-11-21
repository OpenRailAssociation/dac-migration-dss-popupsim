# Examples Status Report

## Fixed Examples

All examples in `popupsim/backend/examples/` have been updated to work with the current PopupSim API after refactoring.

### Changes Made

1. **Updated Topology Format**: Changed from verbose format with `edge_id`, `from_node`, `to_node` to simplified format with just `id` and `length`
   - Old: `{'edge_id': 'e1', 'from_node': 'n1', 'to_node': 'n2', 'length': 100.0}`
   - New: `{'id': 'e1', 'length': 100.0}`

2. **Added Required Tracks**: All scenarios now include required track types:
   - `parking` (PARKING) - for locomotives
   - `collection` (COLLECTION) - for incoming wagons
   - `retrofit` (RETROFIT) - for wagons waiting for workshop
   - `WS1` (WORKSHOP) - workshop track with stations
   - `retrofitted` (RETROFITTED) - for completed wagons

3. **Added Routes**: All scenarios now include routes between tracks for locomotive movement

4. **Removed Strategy Parameters**: Removed explicit `track_selection_strategy` and `retrofit_selection_strategy` parameters where not needed (they have defaults)

5. **Fixed Workshop Configuration**: Workshops now reference WORKSHOP type tracks, not RETROFIT tracks

## Working Examples

### ✅ capacity_demo.py
**Status**: WORKING  
**Purpose**: Demonstrates track capacity management (within/exceeds capacity scenarios)  
**Output**: Shows wagon acceptance/rejection based on 75% capacity rule

### ✅ track_selection_demo.py
**Status**: WORKING  
**Purpose**: Compares all 4 track selection strategies (ROUND_ROBIN, LEAST_OCCUPIED, FIRST_AVAILABLE, RANDOM)  
**Output**: Shows how wagons are distributed across 2 collection tracks with each strategy

### ⚠️ simple_test_demo.py
**Status**: PARTIALLY WORKING  
**Purpose**: Simple scenario with 4 wagons, 1 workshop with 4 stations  
**Issue**: Only 3 of 4 wagons are being picked up from collection track. Wagons reach retrofit track but don't enter workshop stations for retrofitting.  
**Next Steps**: Need to investigate why 4th wagon is not picked up and why wagons don't move to workshop stations

### ⚠️ wagon_pickup_demo.py
**Status**: NEEDS TESTING  
**Purpose**: Demonstrates wagon pickup process from collection to retrofit tracks  
**Next Steps**: Run and verify output

### ✅ multi_track_demo.py
**Status**: WORKING  
**Purpose**: Complex scenario with 3 collection tracks, 2 retrofit tracks, 2 workshops, 2 locomotives  
**Output**: Shows multi-track capacity management, locomotive utilization, and workshop station history

## Running Examples

```bash
# From project root
cd popupsim/backend

# Run individual examples
uv run python examples/capacity_demo.py
uv run python examples/track_selection_demo.py
uv run python examples/simple_test_demo.py
uv run python examples/wagon_pickup_demo.py
uv run python examples/multi_track_demo.py
```

## Known Issues

1. **simple_test_demo.py**: 
   - Only 3/4 wagons picked up from collection
   - Wagons don't move from retrofit track to workshop stations
   - Simulation time may be too short (50 minutes)

2. **General**: Examples may need longer simulation times to see full wagon flow through the system

## API Reference for Examples

### Minimal Scenario Structure
```python
from datetime import datetime, timedelta, UTC
from models.locomotive import Locomotive
from models.process_times import ProcessTimes
from models.route import Route
from models.scenario import Scenario
from models.topology import Topology
from models.track import Track, TrackType
from models.train import Train
from models.wagon import Wagon
from models.workshop import Workshop
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter

start_time = datetime(2025, 1, 1, 8, 0, 0, tzinfo=UTC)

topology = Topology({'edges': [{'id': 'e1', 'length': 100.0}]})

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
    # ... add all necessary routes
]

locos = [Locomotive(locomotive_id='L1', name='Loco 1', 
                   start_date=start_time, end_date=start_time + timedelta(hours=2),
                   track_id='parking')]

process_times = ProcessTimes(
    train_to_hump_delay=0.0, wagon_hump_interval=0.0,
    wagon_coupling_time=0.0, wagon_decoupling_time=0.0,
    wagon_move_to_next_station=0.0, wagon_coupling_retrofitted_time=0.0,
    wagon_retrofit_time=10.0)

wagons = [Wagon(wagon_id=f'W{i}', length=20.0, needs_retrofit=True, is_loaded=False) 
          for i in range(1, 5)]
train = Train(train_id='T1', arrival_time=start_time, wagons=wagons)

workshops = [Workshop(workshop_id='WS1', start_date='2025-01-01 08:00:00',
                     end_date='2025-01-02 08:00:00', track_id='WS1',
                     retrofit_stations=4)]

scenario = Scenario(
    scenario_id='test', start_date=start_time, end_date=start_time + timedelta(days=1),
    locomotives=locos, process_times=process_times, routes=routes,
    topology=topology, trains=[train], tracks=tracks, workshops=workshops)

sim = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim, scenario)
popup_sim.run(until=50.0)
```
