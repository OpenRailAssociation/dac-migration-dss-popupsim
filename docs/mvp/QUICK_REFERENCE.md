# PopUpSim MVP - Quick Reference Guide

## Architecture at a Glance

### 3 Bounded Contexts

```
Configuration Context → Workshop Operations Context → Analysis & Reporting Context
     (Builders)              (5 Coordinators)              (KPI Calculation)
```

## Key Components by Context

### 1. Configuration Context

**Purpose:** Load and validate scenario configuration

**Main Components:**
- `ScenarioBuilder` - Orchestrates loading of 7 files
- `TrainListBuilder` - Parse CSV train schedules
- `TrackListBuilder` - Parse JSON track configs
- Pydantic models in `models/`

**Entry Point:**
```python
from builders.scenario_builder import ScenarioBuilder
scenario = ScenarioBuilder(scenario_path).build()
```

**Files Loaded:**
1. `scenario.json` - Main configuration
2. `trains.csv` - Train schedules
3. `tracks.json` - Track configurations
4. `workshops.json` - Workshop setups
5. `locomotives.json` - Locomotive fleet
6. `routes.json` - Route definitions
7. `topology.json` - Network topology
8. `process_times.json` - Timing parameters

### 2. Workshop Operations Context

**Purpose:** Execute discrete event simulation

**Main Components:**
- `PopupSim` - Main orchestrator
- 5 Process Coordinators (see below)
- `ResourcePool` - Generic resource management
- `TrackCapacityManager` - Track capacity with 4 strategies
- `WorkshopCapacityManager` - Workshop station capacity
- Domain Services in `domain/` (no SimPy deps)
- Metrics Collectors in `analytics/collectors/`

**Entry Point:**
```python
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter

sim_adapter = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim_adapter, scenario)
popup_sim.run()
metrics = popup_sim.get_metrics()
```

**5 Process Coordinators:**
1. `process_train_arrivals` - Process trains at hump, select wagons
2. `pickup_wagons_to_retrofit` - Pickup from collection, deliver to retrofit
3. `move_wagons_to_stations` - Batch delivery to workshop, spawn retrofit processes
4. `pickup_retrofitted_wagons` - Pickup completed wagons in batches
5. `move_to_parking` - Move to parking tracks

### 3. Analysis & Reporting Context

**Purpose:** Calculate KPIs and generate output

**Main Components:**
- `main.py` - Typer CLI orchestrator
- `KPICalculator` - Calculate throughput, utilization, bottlenecks
- `CSVExporter` - Export to CSV
- `Visualizer` - Generate Matplotlib charts
- `StatisticsCalculator` - Pandas/NumPy analysis

**Entry Point:**
```python
from analytics.kpi import KPICalculator

kpi_calculator = KPICalculator()
kpi_result = kpi_calculator.calculate_from_simulation(
    metrics, scenario, wagons, rejected_wagons, workshops
)
```

## Key Patterns

### Track Selection Strategies
- `LEAST_OCCUPIED` - Select track with lowest occupancy (default)
- `ROUND_ROBIN` - Cycle through tracks
- `FIRST_AVAILABLE` - First track with capacity
- `RANDOM` - Random selection

### Locomotive Delivery Strategies
- `RETURN_TO_PARKING` - Return after each delivery (default)
- `STAY_AT_WORKSHOP` - Stay at workshop track

### Wagon States
```
ARRIVING → SELECTING → SELECTED → MOVING → ON_RETROFIT_TRACK → 
MOVING → RETROFITTING → RETROFITTED → MOVING → PARKING
```

## File Structure

```
popupsim/backend/src/
├── main.py                      # CLI entry point
├── builders/                    # Configuration loading
│   ├── scenario_builder.py
│   ├── train_list_builder.py
│   └── tracks_builder.py
├── models/                      # Pydantic domain models
│   ├── scenario.py
│   ├── train.py, wagon.py
│   ├── track.py, workshop.py
│   └── locomotive.py, routes.py, topology.py, process_times.py
├── validators/
│   └── scenario_validation.py
├── simulation/                  # SimPy integration
│   ├── popupsim.py             # Main orchestrator
│   ├── sim_adapter.py          # SimPy abstraction
│   ├── resource_pool.py
│   ├── track_capacity.py
│   ├── workshop_capacity.py
│   ├── services.py             # LocomotiveService
│   └── route_finder.py, jobs.py
├── domain/                      # Domain logic (no SimPy)
│   ├── wagon_operations.py
│   ├── locomotive_operations.py
│   └── workshop_operations.py
└── analytics/
    ├── collectors/              # Real-time metrics
    │   ├── base.py, metrics.py
    │   └── wagon.py, locomotive.py, workshop.py
    ├── kpi/
    │   └── calculator.py
    ├── models/
    │   └── kpi_result.py
    └── reporting/
        ├── csv_exporter.py
        ├── visualizer.py
        └── statistics.py
```

## Common Tasks

### Run Simulation
```bash
uv run python popupsim/backend/src/main.py \
  --scenarioPath Data/examples/small_scenario/scenario.json \
  --outputPath output/
```

### Load Scenario
```python
from builders.scenario_builder import ScenarioBuilder
scenario = ScenarioBuilder("path/to/scenario.json").build()
```

### Run Simulation Programmatically
```python
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter

sim = SimPyAdapter.create_simpy_adapter()
popup_sim = PopupSim(sim, scenario)
popup_sim.run()
```

### Get Metrics
```python
metrics = popup_sim.get_metrics()
# Returns: dict[str, list[dict[str, Any]]]
# Categories: 'wagon', 'locomotive', 'workshop'
```

### Calculate KPIs
```python
from analytics.kpi import KPICalculator

calc = KPICalculator()
kpis = calc.calculate_from_simulation(
    metrics, scenario, 
    popup_sim.wagons_queue,
    popup_sim.rejected_wagons_queue,
    popup_sim.workshops_queue
)
```

### Export Results
```python
from analytics.reporting import CSVExporter, Visualizer

# CSV export
exporter = CSVExporter()
csv_files = exporter.export_all(kpis, output_path)

# Charts
visualizer = Visualizer()
charts = visualizer.generate_all_charts(kpis, output_path)
```

## Key Classes

### Domain Models (Pydantic)
- `Scenario` - Main configuration
- `Train` - Train with wagons list
- `Wagon` - Individual wagon with status
- `Track` - Track with type enum
- `Workshop` - Workshop with retrofit_stations
- `Locomotive` - Locomotive resource
- `Routes` - Route definitions
- `Topology` - Network topology
- `ProcessTimes` - Timing parameters

### Resource Management
- `ResourcePool` - Generic pool with tracking
- `TrackCapacityManager` - Track capacity management
- `WorkshopCapacityManager` - Workshop station capacity

### Domain Services (No SimPy)
- `WagonSelector` - Select wagons for retrofit
- `WagonStateManager` - Manage wagon states
- `LocomotiveStateManager` - Manage locomotive states
- `WorkshopDistributor` - Distribute wagons to workshops

### Metrics
- `MetricCollector` - Base class
- `WagonCollector` - Wagon flow times
- `LocomotiveCollector` - Locomotive utilization
- `WorkshopCollector` - Station occupancy

### KPIs
- `ThroughputKPI` - Wagons processed, per hour, per day
- `UtilizationKPI` - Workshop utilization, peak, idle
- `BottleneckInfo` - Location, type, severity, impact

## Configuration Example

**scenario.json:**
```json
{
  "scenario_id": "small_scenario",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-02T00:00:00",
  "track_selection_strategy": "least_occupied",
  "retrofit_selection_strategy": "least_occupied",
  "loco_delivery_strategy": "return_to_parking",
  "references": {
    "trains": "trains.csv",
    "tracks": "tracks.json",
    "workshops": "workshops.json",
    "locomotives": "locomotives.json",
    "routes": "routes.json",
    "topology": "topology.json",
    "process_times": "process_times.json"
  }
}
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run simulation
uv run python popupsim/backend/src/main.py --scenarioPath <path> --outputPath <path>

# Run all quality checks
uv run ruff format . && uv run ruff check . && uv run mypy popupsim/backend/src/ && uv run pylint popupsim/backend/src/ && uv run pytest

# Individual checks
uv run pytest                          # Tests
uv run ruff format .                   # Format
uv run ruff check .                    # Lint
uv run mypy popupsim/backend/src/      # Type check
uv run pylint popupsim/backend/src/    # Code quality
```

## Documentation

- **Architecture:** `docs/mvp/architecture/`
  - `05-building-blocks.md` - Level 2 architecture
  - `05a-level3-implementation.md` - Level 3 details
- **Development:** `docs/mvp/development/`
  - `02-mvp-contexts.md` - Context implementation
- **Examples:** `Data/examples/`
  - `small_scenario/` - 2 trains, 20 wagons
  - `medium_scenario/` - 4 trains, 160 wagons
  - `large_scenario/` - 10 trains, 500 wagons

## Quick Debugging

### Enable Debug Logging
```bash
uv run python popupsim/backend/src/main.py \
  --scenarioPath <path> \
  --outputPath <path> \
  --debug DEBUG
```

### Check Wagon States
```python
for wagon in popup_sim.wagons_queue:
    print(f"{wagon.wagon_id}: {wagon.status} at {wagon.track_id}")
```

### Check Resource Utilization
```python
utilization = popup_sim.locomotives.get_utilization(total_time)
for loco_id, util_pct in utilization.items():
    print(f"{loco_id}: {util_pct:.1f}%")
```

### Check Track Capacity
```python
for track_id in popup_sim.track_capacity.track_capacities:
    available = popup_sim.track_capacity.get_available_capacity(track_id)
    total = popup_sim.track_capacity.get_total_capacity(track_id)
    print(f"{track_id}: {available:.1f}/{total:.1f}m")
```

## Common Issues

### Issue: "Scenario must have trains configured"
**Solution:** Ensure trains.csv is referenced and contains valid data

### Issue: "No route found from X to Y"
**Solution:** Check routes.json contains route between tracks

### Issue: High wagon rejection rate
**Solution:** Increase collection track capacity or add more tracks

### Issue: Low workshop utilization
**Solution:** Reduce retrofit_stations or increase train frequency

## Performance Tips

1. **Batch Size:** Set workshop.retrofit_stations to match typical batch size
2. **Track Strategy:** Use LEAST_OCCUPIED for balanced load
3. **Loco Strategy:** Use RETURN_TO_PARKING for realistic simulation
4. **Fill Factor:** Adjust track fill_factor (default 0.75) for capacity tuning

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest popupsim/backend/tests/unit/test_scenario_builder.py

# Run with coverage
uv run pytest --cov=popupsim/backend/src
```

## Type Checking

All code must have type hints:
```python
def function_name(param: ParamType) -> ReturnType:
    """Docstring."""
    pass
```

MyPy enforces `disallow_untyped_defs = true`.

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following code quality standards
3. Run all quality checks
4. Commit with descriptive message
5. Push and create Pull Request

## Support

- **GitHub Issues:** Report bugs or request features
- **Documentation:** `docs/mvp/architecture/` and `docs/mvp/development/`
- **Examples:** `Data/examples/`
