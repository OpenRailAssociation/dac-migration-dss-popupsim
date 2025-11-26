# 5. Building Block View (MVP)

**Note:** For complete Level 3 implementation details including all components, see [Section 5a: Level 3 Implementation Details](05a-level3-implementation.md).

## 5.1 Level 1: System Whitebox

**PopUpSim MVP** consists of 3 bounded contexts that work together to provide simulation capabilities.

```mermaid
graph TB
    subgraph "PopUpSim MVP System"
        CC["<b>Configuration Context</b><br/>Input validation & parsing<br/>Pydantic + Pandas"]
        SD["<b>Workshop Operations Context</b><br/>Simulation execution & analysis<br/>SimPy + Analysis Engine"]
        SC["<b>Analysis & Reporting Context</b><br/>Orchestration & output<br/>Matplotlib + CSV export"]
    end

    subgraph "External"
        Files["Configuration Files<br/>JSON/CSV"]
        Results["Result Files<br/>CSV/PNG/JSON"]
    end

    Files -->|"Read"| CC
    CC -->|"Validated config"| SD
    SD -->|"Simulation results"| SC
    SC -->|"Write"| Results

    classDef context fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class CC,SD,SC context
    class Files,Results external
```

### Contained Building Blocks

| Building Block | Responsibility | Reference |
|----------------|----------------|----------|
| **Configuration Context** | Parse and validate input files (JSON/CSV) | [Section 5.2](#52-level-2-configuration-context) |
| **Workshop Operations Context** | Execute discrete event simulation with SimPy and real-time analysis | [Section 5.3](#53-level-2-workshop-operations-context) |
| **Analysis & Reporting Context** | Orchestrate simulation execution and generate aggregated output | [Section 5.4](#54-level-2-analysis--reporting-context) |

### Important Interfaces

| Interface | Source | Target | Description |
|-----------|--------|--------|-------------|
| **Validated Configuration** | Configuration Context | Workshop Operations Context | Pydantic-validated domain objects (scenario, workshop, topology, routes, schedules) |
| **Simulation Results** | Workshop Operations Context | Analysis & Reporting Context | Simulation events and KPI data from analysis engine |
| **File I/O** | All Contexts | File System | JSON/CSV read/write operations |

---

## 5.2 Level 2: Configuration Context

### Whitebox: Configuration Context

**Responsibility:** Load, parse, validate, and build complete scenario configuration.

**Architecture Note:** Components follow layered architecture pattern (see [Section 8.1](08-concepts.md#81-layered-architecture)).

```mermaid
graph TB
    subgraph "Configuration Context"
        Builder["ScenarioBuilder<br/>Main orchestrator"]
        TrainBuilder["TrainListBuilder<br/>CSV parsing"]
        TrackBuilder["TrackListBuilder<br/>JSON parsing"]
        Validator["ScenarioValidator<br/>Cross-validation"]
        Models["Domain Models<br/>Pydantic models"]
    end

    Files[JSON/CSV Files] --> Builder
    Builder --> TrainBuilder
    Builder --> TrackBuilder
    Builder --> Validator
    TrainBuilder --> Models
    TrackBuilder --> Models
    Validator --> Models
    Models --> Output[Validated Scenario]

    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Builder,TrainBuilder,TrackBuilder,Validator,Models component
    class Files,Output external
```

### Contained Building Blocks

| Component | Responsibility | Layer | Implementation |
|-----------|----------------|-------|----------------|
| **ScenarioBuilder** | Main builder, orchestrates loading of all referenced files | Business Logic | `builders/scenario_builder.py` |
| **TrainListBuilder** | Parse train schedules from CSV | Business Logic | `builders/train_list_builder.py` |
| **TrackListBuilder** | Parse track configurations from JSON | Business Logic | `builders/tracks_builder.py` |
| **ScenarioValidator** | Cross-validate scenario consistency | Business Logic | `validators/scenario_validation.py` |
| **Domain Models** | Type-safe Pydantic models (Scenario, Train, Wagon, Workshop, etc.) | Domain | `models/` |

### Level 3: Builder Pattern Implementation

**ScenarioBuilder orchestrates loading of 7 referenced files:**

```mermaid
graph TB
    Scenario[scenario.json] --> Builder[ScenarioBuilder]
    Builder --> Trains[trains.csv]
    Builder --> Tracks[tracks.json]
    Builder --> Workshops[workshops.json]
    Builder --> Locomotives[locomotives.json]
    Builder --> Routes[routes.json]
    Builder --> Topology[topology.json]
    Builder --> ProcessTimes[process_times.json]

    Trains --> TrainList[TrainListBuilder]
    Tracks --> TrackList[TrackListBuilder]
    
    TrainList --> Complete[Complete Scenario]
    TrackList --> Complete
    Workshops --> Complete
    Locomotives --> Complete
    Routes --> Complete
    Topology --> Complete
    ProcessTimes --> Complete

    classDef file fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef builder fill:#e1f5fe,stroke:#01579b,stroke-width:2px

    class Scenario,Trains,Tracks,Workshops,Locomotives,Routes,Topology,ProcessTimes file
    class Builder,TrainList,TrackList,Complete builder
```

### Code Example: Actual ScenarioBuilder

**File:** `popupsim/backend/src/builders/scenario_builder.py`

```python
from pathlib import Path
from builders.tracks_builder import TrackListBuilder
from builders.train_list_builder import TrainListBuilder
from models.scenario import Scenario
from validators.scenario_validation import ScenarioValidator

class BuilderError(Exception):
    """Custom exception for configuration-related errors."""

class ScenarioBuilder:
    """Service for loading and validating configuration files."""

    def __init__(self, scenario_path: Path):
        self.scenario_path = scenario_path
        self.scenario: Scenario | None = None
        self.references: dict = {}
        self.validator = ScenarioValidator()

    def build(self) -> Scenario:
        """Build and return the scenario configuration."""
        path = Path(self.scenario_path)
        self.__find_scenario_in_path(path)
        self.__load_scenario()  # Load scenario.json
        
        if isinstance(self.scenario, Scenario):
            # Load all referenced files
            self.__load_locomotives()
            self.__load_tracks()
            self.__load_trains()
            self.__load_routes()
            self.__load_topology()
            self.__load_process_times()
            self.__load_workshops()
            
            # Validate complete scenario
            self.scenario.validate_simulation_requirements()
        else:
            raise BuilderError('Scenario could not be loaded properly.')
        
        return self.scenario

    def __load_scenario(self) -> None:
        """Load scenario configuration from JSON file."""
        with open(self.scenario_path, encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['scenario_id', 'start_date', 'end_date', 'references']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BuilderError(f'Missing required fields: {", ".join(missing_fields)}')
        
        self.scenario = Scenario(**data)
        self.references = data.get('references', {})

    def __load_trains(self) -> None:
        """Load trains from CSV file referenced in scenario configuration."""
        trains_file = self.references.get('trains')
        if not trains_file:
            raise BuilderError('Missing trains file reference')
        
        scenario_dir = Path(self.scenario_path).parent
        trains_path = scenario_dir / trains_file
        
        if isinstance(self.scenario, Scenario):
            self.scenario.trains = TrainListBuilder(trains_path).build()

    def __load_workshops(self) -> None:
        """Load workshops from JSON file."""
        workshops_file = self.references.get('workshops')
        if not workshops_file:
            raise BuilderError('Missing workshops file reference')
        
        scenario_dir = Path(self.scenario_path).parent
        workshops_path = scenario_dir / workshops_file
        
        if isinstance(self.scenario, Scenario):
            with open(workshops_path, encoding='utf-8') as f:
                workshops_data = json.load(f)
            
            workshops_list = workshops_data['workshops']
            self.scenario.workshops = [Workshop(**data) for data in workshops_list]
```

### Code Example: Pydantic Domain Models

**File:** `popupsim/backend/src/models/scenario.py`

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class TrackSelectionStrategy(str, Enum):
    """Strategy for selecting tracks."""
    ROUND_ROBIN = 'round_robin'
    LEAST_OCCUPIED = 'least_occupied'
    FIRST_AVAILABLE = 'first_available'
    RANDOM = 'random'

class LocoDeliveryStrategy(str, Enum):
    """Strategy for locomotive delivery."""
    RETURN_TO_PARKING = 'return_to_parking'
    STAY_AT_WORKSHOP = 'stay_at_workshop'

class Scenario(BaseModel):
    """Complete scenario configuration."""
    scenario_id: str
    start_date: datetime
    end_date: datetime
    
    # Optional components loaded from referenced files
    trains: list[Train] | None = None
    tracks: list[Track] | None = None
    workshops: list[Workshop] | None = None
    locomotives: list[Locomotive] | None = None
    routes: list[Route] | None = None
    topology: Topology | None = None
    process_times: ProcessTimes | None = None
    
    # Strategy configurations
    track_selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED
    retrofit_selection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED
    loco_delivery_strategy: LocoDeliveryStrategy = LocoDeliveryStrategy.RETURN_TO_PARKING

    def validate_simulation_requirements(self) -> None:
        """Validate that all required components are loaded."""
        if not self.trains:
            raise ValueError('Scenario must have trains configured')
        if not self.workshops:
            raise ValueError('Scenario must have workshops configured')
        if not self.routes:
            raise ValueError('Scenario must have routes configured')
```

**File:** `popupsim/backend/src/models/workshop.py`

```python
from pydantic import BaseModel, Field

class Workshop(BaseModel):
    """Workshop configuration."""
    workshop_id: str
    track_id: str
    retrofit_stations: int = Field(gt=0, description="Number of parallel retrofit stations")
    
    # Optional fields
    name: str | None = None
    description: str | None = None
```

**Key aspects:**
- Builder pattern orchestrates complex multi-file loading
- Pydantic enforces type safety and validation rules
- References in scenario.json point to external files
- Comprehensive error handling with BuilderError
- Cross-validation after all files loaded
- Strategy pattern for configurable behaviors

---

## 5.3 Level 2: Workshop Operations Context

### Whitebox: Workshop Operations Context

**Responsibility:** Execute discrete event simulation with real-time metrics collection.

**Architecture Note:** Components follow layered architecture pattern (see [Section 8.1](08-concepts.md#81-layered-architecture)).

```mermaid
graph TB
    subgraph "Workshop Operations Context"
        Orchestrator["PopupSim Orchestrator<br/>Main simulation coordinator"]
        Coordinators["Process Coordinators<br/>5 specialized coordinators"]
        Domain["Domain Services<br/>State managers & selectors"]
        Resources["Resource Management<br/>Pools & capacity managers"]
        SimAdapter["SimPy Adapter<br/>Simulation abstraction"]
        Collectors["Metrics Collectors<br/>Real-time data collection"]
    end

    Config[Validated Config] --> Orchestrator
    Orchestrator --> Coordinators
    Coordinators --> Domain
    Coordinators --> Resources
    Coordinators --> SimAdapter
    SimAdapter --> SimPy[SimPy Framework]
    Coordinators --> Collectors
    Collectors --> Results[Simulation Events & Metrics]

    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Orchestrator,Coordinators,Domain,Resources,SimAdapter,Collectors component
    class Config,Results,SimPy external
```

### Contained Building Blocks

| Component | Responsibility | Layer | Implementation |
|-----------|----------------|-------|----------------|
| **PopupSim Orchestrator** | Main simulation coordinator, spawns processes | Business Logic | `simulation/popupsim.py` |
| **Process Coordinators** | 5 specialized coordinators for wagon flow | Business Logic | `simulation/coordinators/` |
| **Domain Services** | State managers, selectors, distributors (no SimPy deps) | Domain | `domain/` |
| **Resource Management** | ResourcePool, TrackCapacityManager, WorkshopCapacityManager | Business Logic | `simulation/resource_pool.py`, `simulation/track_capacity.py`, `simulation/workshop_capacity.py` |
| **SimPy Adapter** | Abstraction layer for SimPy operations | Infrastructure | `simulation/sim_adapter.py` |
| **Metrics Collectors** | Real-time event collection during simulation | Business Logic | `analytics/collectors/` |
| **SimPy Framework** | Discrete event simulation engine | Infrastructure | SimPy library |

### Level 3: Process Coordinators

**5 specialized coordinators orchestrate wagon flow:**

```mermaid
graph LR
    Train[Train Arrival<br/>Coordinator] --> Pickup[Wagon Pickup<br/>Coordinator]
    Pickup --> Workshop[Workshop<br/>Coordinator]
    Workshop --> Retrofitted[Retrofitted Pickup<br/>Coordinator]
    Retrofitted --> Parking[Parking<br/>Coordinator]

    classDef coord fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    class Train,Pickup,Workshop,Retrofitted,Parking coord
```

| Coordinator | Process Function | Responsibility |
|-------------|------------------|----------------|
| **Train Arrival** | `process_train_arrivals()` | Process arriving trains, select wagons at hump, assign to collection tracks |
| **Wagon Pickup** | `pickup_wagons_to_retrofit()` | Allocate locomotive, pickup wagons from collection, deliver to retrofit tracks |
| **Workshop** | `move_wagons_to_stations()` | Move wagon batches to workshop, decouple sequentially, spawn retrofit processes |
| **Retrofitted Pickup** | `pickup_retrofitted_wagons()` | Pickup completed wagons in batches, move to retrofitted track |
| **Parking** | `move_to_parking()` | Move retrofitted wagons to parking tracks (sequential fill strategy) |

### Code Example: Actual PopupSim Orchestrator

**File:** `popupsim/backend/src/simulation/popupsim.py`

```python
class PopupSim:
    """High-level simulation orchestrator for PopUp-Sim."""

    def __init__(
        self, sim: SimulationAdapter, scenario: Scenario, 
        locomotive_service: LocomotiveService | None = None
    ) -> None:
        self.sim: SimulationAdapter = sim
        self.scenario: Scenario = scenario
        self.locomotive_service = locomotive_service or DefaultLocomotiveService()

        # Resource pools
        self.locomotives = ResourcePool(self.sim, self.locomotives_queue, 'Locomotives')
        
        # Capacity managers
        self.track_capacity = TrackCapacityManager(
            scenario.tracks or [],
            scenario.topology,
            collection_strategy=scenario.track_selection_strategy,
            retrofit_strategy=scenario.retrofit_selection_strategy,
        )
        self.workshop_capacity = WorkshopCapacityManager(sim, self.workshops_queue)

        # Domain services (no SimPy dependencies)
        self.wagon_selector = WagonSelector()
        self.wagon_state = WagonStateManager()
        self.loco_state = LocomotiveStateManager()
        self.workshop_distributor = WorkshopDistributor()

        # Metrics collection
        self.metrics = SimulationMetrics()
        self.metrics.register(WagonCollector())

    def run(self, until: float | None = None) -> None:
        """Run simulation by spawning 5 coordinator processes."""
        self.sim.run_process(process_train_arrivals, self)
        self.sim.run_process(pickup_wagons_to_retrofit, self)
        self.sim.run_process(move_wagons_to_stations, self)
        self.sim.run_process(pickup_retrofitted_wagons, self)
        self.sim.run_process(move_to_parking, self)
        self.sim.run(until)
```

### Code Example: Workshop Coordinator with Batch Processing

**File:** `popupsim/backend/src/simulation/popupsim.py`

```python
def move_wagons_to_stations(popupsim: PopupSim) -> Generator[Any]:
    """Move wagon batches from retrofit track to stations.
    
    Blocks until batch delivered, travels via route, decouples sequentially,
    then spawns independent process for each wagon.
    """
    for track_id in popupsim.wagons_ready_for_stations:
        popupsim.sim.run_process(_process_track_batches, popupsim, track_id)

def _process_track_batches(popupsim: PopupSim, workshop_track_id: str) -> Generator[Any]:
    """Process wagon batches for a single workshop track."""
    workshop = popupsim.workshop_capacity.workshops_by_track[workshop_track_id]
    batch_size = workshop.retrofit_stations

    while True:
        # Collect batch up to batch_size
        batch_wagons, retrofit_track_id = yield from _collect_wagon_batch(
            popupsim, workshop_track_id, batch_size
        )
        
        # Wait until workshop ready (track and stations empty)
        yield from _wait_for_workshop_ready(popupsim, workshop_track_id, workshop)
        
        # Allocate locomotive and deliver batch
        loco = yield from popupsim.locomotive_service.allocate(popupsim)
        yield from _deliver_batch_to_workshop(
            popupsim, loco, batch_wagons, retrofit_track_id, workshop.workshop_id
        )
        
        # Sequentially decouple and spawn processing for each wagon
        yield from _decouple_and_process_wagons(popupsim, batch_wagons, workshop_track_id)
        
        # Return locomotive to parking
        yield from _return_loco_to_parking(popupsim, loco)
        yield from popupsim.locomotive_service.release(popupsim, loco)

def process_single_wagon(popupsim: PopupSim, wagon: Wagon, track_id: str) -> Generator[Any]:
    """Process single wagon at workshop station using SimPy Resource."""
    workshop_resource = popupsim.workshop_capacity.get_resource(track_id)
    process_times = popupsim.scenario.process_times

    with workshop_resource.request() as station_req:
        yield station_req  # Block until station available
        
        # Station acquired - start retrofit
        wagon.status = WagonStatus.RETROFITTING
        wagon.retrofit_start_time = popupsim.sim.current_time()
        
        # Perform retrofit work
        yield popupsim.sim.delay(process_times.wagon_retrofit_time)
        
        # Retrofit complete
        wagon.status = WagonStatus.RETROFITTED
        wagon.coupler_type = CouplerType.DAC
        popupsim.metrics.record_event('wagon_retrofitted', {
            'wagon_id': wagon.wagon_id, 
            'time': popupsim.sim.current_time()
        })
        
        # Signal completion
        yield popupsim.wagons_completed[track_id].put(wagon)
```

**Key aspects:**
- 5 independent coordinator processes run concurrently
- Batch processing for efficient locomotive utilization
- Sequential coupling/decoupling with timing
- SimPy Resources for workshop station capacity
- Real-time metrics collection during simulation
- Domain services isolated from SimPy dependencies

---

## 5.4 Level 2: Analysis & Reporting Context

### Whitebox: Analysis & Reporting Context

**Responsibility:** Orchestrate simulation execution and generate comprehensive output.

**Architecture Note:** Components follow layered architecture pattern (see [Section 8.1](08-concepts.md#81-layered-architecture)).

```mermaid
graph TB
    subgraph "Analysis & Reporting Context"
        Main["Main Orchestrator<br/>CLI entry point"]
        KPICalc["KPI Calculator<br/>Compute performance metrics"]
        Collectors["Metrics Collectors<br/>Wagon, Locomotive, Workshop"]
        Statistics["Statistics Calculator<br/>Pandas/NumPy analysis"]
        CSVExport["CSV Exporter<br/>Structured data export"]
        Visualizer["Visualizer<br/>Chart generation"]
    end

    Metrics[Raw Simulation Metrics] --> KPICalc
    Metrics --> Statistics
    KPICalc --> CSVExport
    KPICalc --> Visualizer
    Statistics --> CSVExport
    CSVExport --> CSV[CSV Files]
    Visualizer --> Charts[PNG Charts]

    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Main,KPICalc,Collectors,Statistics,CSVExport,Visualizer component
    class Metrics,CSV,Charts external
```

### Contained Building Blocks

| Component | Responsibility | Layer | Implementation |
|-----------|----------------|-------|----------------|
| **Main Orchestrator** | CLI entry point, coordinates full pipeline | Presentation | `main.py` (Typer CLI) |
| **KPI Calculator** | Calculate throughput, utilization, bottlenecks | Business Logic | `analytics/kpi/calculator.py` |
| **Metrics Collectors** | Real-time event collection (wagon, locomotive, workshop) | Business Logic | `analytics/collectors/` |
| **Statistics Calculator** | Pandas/NumPy statistical analysis | Business Logic | `analytics/reporting/statistics.py` |
| **CSV Exporter** | Export KPIs and metrics to CSV | Presentation | `analytics/reporting/csv_exporter.py` |
| **Visualizer** | Generate Matplotlib charts | Presentation | `analytics/reporting/visualizer.py` |

### Level 3: Metrics Collection Architecture

**Real-time collectors observe simulation events:**

```mermaid
graph TB
    subgraph "Metrics Collection"
        Base["MetricCollector<br/>(Abstract Base)"]
        Wagon["WagonCollector<br/>Flow times, waiting"]
        Loco["LocomotiveCollector<br/>Utilization, trips"]
        Workshop["WorkshopCollector<br/>Station occupancy"]
        TimeSeries["TimeSeriesCollector<br/>Time-based metrics"]
    end

    Base --> Wagon
    Base --> Loco
    Base --> Workshop
    Base --> TimeSeries

    SimEvents[Simulation Events] --> Wagon
    SimEvents --> Loco
    SimEvents --> Workshop
    SimEvents --> TimeSeries

    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Base,Wagon,Loco,Workshop,TimeSeries component
    class SimEvents external
```

### Code Example: Actual Main Orchestrator

**File:** `popupsim/backend/src/main.py`

```python
from analytics.kpi import KPICalculator
from analytics.reporting import CSVExporter, Visualizer
from builders.scenario_builder import ScenarioBuilder
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter
import typer

app = typer.Typer(name='popupsim')

@app.command()
def main(
    scenario_path: Path | None = None,
    output_path: Path | None = None,
    verbose: bool = False,
    debug: str = 'INFO',
) -> None:
    """Main entry point for PopUpSim application."""
    # 1. Configuration Context - Load and validate
    scenario = ScenarioBuilder(scenario_path).build()
    typer.echo(f'Scenario loaded: {scenario.scenario_id}')
    
    # 2. Workshop Operations Context - Run simulation
    typer.echo('Starting simulation...')
    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim_adapter, scenario)
    popup_sim.run()
    
    # Get raw metrics from collectors
    metrics = popup_sim.get_metrics()
    
    # 3. Analysis & Reporting Context - Calculate KPIs
    typer.echo('Calculating KPIs...')
    kpi_calculator = KPICalculator()
    kpi_result = kpi_calculator.calculate_from_simulation(
        metrics,
        scenario,
        popup_sim.wagons_queue,
        popup_sim.rejected_wagons_queue,
        popup_sim.workshops_queue,
    )
    
    # Display KPIs to console
    typer.echo(f'Throughput: {kpi_result.throughput.wagons_per_hour:.2f} wagons/hour')
    
    # Export results to CSV
    csv_exporter = CSVExporter()
    csv_files = csv_exporter.export_all(kpi_result, output_path)
    typer.echo(f'CSV files saved: {len(csv_files)}')
    
    # Generate visualization charts
    visualizer = Visualizer()
    chart_paths = visualizer.generate_all_charts(kpi_result, output_path)
    typer.echo(f'Charts saved: {len(chart_paths)}')
```

### Code Example: KPI Calculator

**File:** `popupsim/backend/src/analytics/kpi/calculator.py`

```python
from analytics.models.kpi_result import KPIResult, ThroughputKPI, UtilizationKPI

class KPICalculator:
    """Calculate KPIs from simulation results."""

    def calculate_from_simulation(
        self,
        metrics: dict[str, list[dict[str, Any]]],
        scenario: Scenario,
        wagons: list[Wagon],
        rejected_wagons: list[Wagon],
        workshops: list[Workshop],
    ) -> KPIResult:
        """Calculate all KPIs from simulation results."""
        throughput = self._calculate_throughput(scenario, wagons, rejected_wagons)
        utilization = self._calculate_utilization(workshops, wagons)
        bottlenecks = self._identify_bottlenecks(throughput, utilization)
        avg_flow_time = self._calculate_avg_flow_time(metrics)
        avg_waiting_time = self._calculate_avg_waiting_time(wagons)

        return KPIResult(
            scenario_id=scenario.scenario_id,
            throughput=throughput,
            utilization=utilization,
            bottlenecks=bottlenecks,
            avg_flow_time_minutes=avg_flow_time,
            avg_waiting_time_minutes=avg_waiting_time,
        )

    def _calculate_throughput(
        self, scenario: Scenario, wagons: list[Wagon], rejected_wagons: list[Wagon]
    ) -> ThroughputKPI:
        """Calculate throughput metrics."""
        duration_hours = (scenario.end_date - scenario.start_date).total_seconds() / 3600.0
        retrofitted = sum(1 for w in wagons if w.status == WagonStatus.RETROFITTED)
        wagons_per_hour = retrofitted / duration_hours if duration_hours > 0 else 0.0

        return ThroughputKPI(
            total_wagons_processed=len(wagons),
            total_wagons_retrofitted=retrofitted,
            total_wagons_rejected=len(rejected_wagons),
            simulation_duration_hours=duration_hours,
            wagons_per_hour=round(wagons_per_hour, 2),
            wagons_per_day=round(wagons_per_hour * 24.0, 2),
        )
```

### Code Example: Metrics Collector Base Class

**File:** `popupsim/backend/src/analytics/collectors/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class MetricResult:
    """Single metric result."""
    name: str
    value: float | int | str
    unit: str
    category: str

class MetricCollector(ABC):
    """Base class for metric collectors."""

    @abstractmethod
    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an event for metric computation."""
        raise NotImplementedError

    @abstractmethod
    def get_results(self) -> list[MetricResult]:
        """Get computed metrics."""
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset collector state."""
        raise NotImplementedError
```

**Key aspects:**
- Direct method calls between contexts (MVP simplification)
- Clear pipeline: Configuration → Simulation → KPI Calculation → Export
- Real-time metrics collection during simulation
- Post-simulation KPI aggregation and analysis
- Multiple output formats (console, CSV, PNG charts)
- Typer CLI for user-friendly command-line interface

---
