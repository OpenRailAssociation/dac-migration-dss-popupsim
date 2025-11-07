# 5. MVP Data Flow

## Overview

**Note:** See [Architecture Section 6](../architecture/06-runtime.md) for runtime scenarios.

This document describes data flow through the 3 MVP bounded contexts: Configuration, Workshop Operations, and Analysis & Reporting.

## End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. CONFIGURATION CONTEXT                     │
└─────────────────────────────────────────────────────────────────┘
                              │
    JSON/CSV Files            │
    ──────────────────────────▼
    scenario.json         ┌─────────────────┐
    workshop_tracks.csv   │ Configuration   │
    train_schedule.csv    │    Service      │
                          └────────┬────────┘
                                   │
                          ScenarioConfig (Pydantic)
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                2. WORKSHOP OPERATIONS CONTEXT                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  Simulation     │
                          │  Service        │
                          └────────┬────────┘
                                   │
                          Workshop + Tracks
                                   │
                          ┌────────▼────────┐
                          │  SimPy Adapter  │
                          │  + Processes    │
                          └────────┬────────┘
                                   │
                          Events + Wagons
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                3. ANALYSIS & REPORTING CONTEXT                  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  KPI Service    │
                          └────────┬────────┘
                                   │
                          SimulationResults
                                   │
                          ┌────────▼────────┐
                          │ Output Service  │
                          └────────┬────────┘
                                   │
                          CSV + Charts
                                   │
                                   ▼
                          results/ Directory
```

## Phase 1: Configuration Loading

### Input: Files
```
config/
├── scenario.json
├── workshop_tracks.csv
└── train_schedule.csv
```

### Process: Configuration Service

```python
from pathlib import Path

class ConfigurationService:
    def load_scenario(self, config_path: Path) -> ScenarioConfig:
        # 1. Load scenario.json
        scenario_data = self._load_json(config_path / "scenario.json")

        # 2. Load workshop_tracks.csv
        tracks_data = self._load_csv(config_path / "workshop_tracks.csv")

        # 3. Load train_schedule.csv
        trains_data = self._load_csv(config_path / "train_schedule.csv")

        # 4. Validate and create Pydantic models
        config = ScenarioConfig(
            scenario_id=scenario_data["scenario_id"],
            start_date=scenario_data["start_date"],
            end_date=scenario_data["end_date"],
            workshop=Workshop(
                tracks=[
                    WorkshopTrack(**track)
                    for track in tracks_data
                ]
            ),
            train_schedule_file=str(config_path / "train_schedule.csv")
        )

        # 5. Validate business rules
        self._validate_config(config)

        return config
```

### Output: ScenarioConfig
```python
ScenarioConfig(
    scenario_id="demo_scenario",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 2),
    workshop=Workshop(
        tracks=[
            WorkshopTrack(
                id="TRACK01",
                function=TrackFunction.WERKSTATTGLEIS,
                capacity=5,
                retrofit_time_min=30
            )
        ]
    ),
    train_schedule_file="config/train_schedule.csv"
)
```

## Phase 2: Simulation Setup

### Input: ScenarioConfig

### Process: Simulation Service

```python
class SimulationService:
    def setup_simulation(
        self,
        config: ScenarioConfig,
        env: SimPyEnvironmentAdapter
    ) -> Workshop:
        # 1. Create tracks from config
        tracks: list[WorkshopTrack] = []
        for track_config in config.workshop.tracks:
            track = WorkshopTrack(
                id=track_config.id,
                function=track_config.function,
                capacity=track_config.capacity,
                retrofit_time_min=track_config.retrofit_time_min,
                current_wagons=0
            )
            tracks.append(track)

        # 2. Create workshop
        workshop = Workshop(tracks=tracks)

        return workshop
```

### Output: Workshop Domain Model
```python
Workshop(
    tracks=[
        WorkshopTrack(
            id="TRACK01",
            function=TrackFunction.WERKSTATTGLEIS,
            capacity=5,
            retrofit_time_min=30,
            current_wagons=0
        )
    ]
)
```

## Phase 3: Simulation Execution

### Input: Workshop + ScenarioConfig

### Process: SimPy Adapter

```python
from typing import Generator

class WorkshopSimPyAdapter:
    def __init__(
        self, 
        workshop: Workshop, 
        env: SimPyEnvironmentAdapter
    ) -> None:
        self.workshop = workshop
        self.env = env
        self.event_logger = EventLogger()
        self.all_wagons: list[Wagon] = []

        # Initialize SimPy resources
        for track in self.workshop.tracks:
            track.resource = simpy.Resource(
                self.env.simpy_env,
                capacity=track.capacity
            )

    def train_arrival_process(
        self, 
        train_schedule: list[TrainArrival]
    ) -> Generator:
        """Process explicit train arrivals from schedule"""
        for train_arrival in train_schedule:
            # Wait until arrival time
            yield self.env.timeout(train_arrival.arrival_minutes)

            # Create train with wagons
            train = Train(
                id=train_arrival.train_id,
                arrival_time=self.env.now,
                wagons=[
                    Wagon(
                        id=wagon_info.wagon_id,
                        train_id=train_arrival.train_id,
                        length=wagon_info.length,
                        needs_retrofit=wagon_info.needs_retrofit
                    )
                    for wagon_info in train_arrival.wagons
                ]
            )

            # Log event
            self.event_logger.log_train_arrival(self.env, train)

            # Start retrofit for wagons needing it
            for wagon in train.wagons:
                self.all_wagons.append(wagon)
                if wagon.needs_retrofit:
                    self.env.process(self.retrofit_process(wagon))

    def retrofit_process(self, wagon: Wagon) -> Generator:
        wagon.arrival_time = self.env.now

        # Select track
        track = self._select_track()

        # Request resource
        with track.resource.request() as req:
            yield req

            # Start retrofit
            wagon.retrofit_start_time = self.env.now
            wagon.track_id = track.id
            track.current_wagons += 1
            self.event_logger.log_retrofit_start(self.env, wagon, track)

            # Retrofit duration
            yield self.env.timeout(track.retrofit_time_min)

            # Complete retrofit
            wagon.retrofit_end_time = self.env.now
            wagon.needs_retrofit = False
            track.current_wagons -= 1
            self.event_logger.log_retrofit_complete(self.env, wagon, track)
```

### Output: Events + Wagons

**Events:**
```python
[
    TrainArrivalEvent(
        timestamp=60.0, 
        train_id="TRAIN0001", 
        wagon_count=10
    ),
    RetrofitStartEvent(
        timestamp=60.0, 
        wagon_id="WAGON0001_00", 
        track_id="TRACK01"
    ),
    RetrofitCompleteEvent(
        timestamp=90.0, 
        wagon_id="WAGON0001_00", 
        track_id="TRACK01"
    ),
]
```

**Wagons:**
```python
[
    Wagon(
        id="WAGON0001_00",
        train_id="TRAIN0001",
        arrival_time=60.0,
        retrofit_start_time=60.0,
        retrofit_end_time=90.0,
        track_id="TRACK01",
        needs_retrofit=False
    ),
]
```

## Phase 4: KPI Calculation

### Input: Events + Wagons

### Process: KPI Service

```python
import statistics

class KPIService:
    def calculate_kpis(
        self,
        wagons: list[Wagon],
        events: list[SimulationEvent],
        duration_hours: float
    ) -> SimulationResult:

        # 1. Filter processed wagons
        processed = [w for w in wagons if w.retrofit_end_time is not None]

        # 2. Calculate waiting times
        waiting_times = [
            w.waiting_time
            for w in processed
            if w.waiting_time is not None
        ]

        # 3. Calculate throughput
        throughput = len(processed) / duration_hours

        # 4. Calculate utilization
        utilization = self._calculate_utilization(events, duration_hours)

        # 5. Create results
        return SimulationResult(
            scenario_id="scenario_001",
            duration_hours=duration_hours,
            total_wagons_processed=len(processed),
            throughput_per_hour=throughput,
            average_waiting_time=statistics.mean(waiting_times) if waiting_times else 0.0,
            track_utilization=utilization
        )

    def _calculate_utilization(
        self,
        events: list[SimulationEvent],
        duration_hours: float
    ) -> float:
        """Calculate average track utilization"""
        # Implementation details
        return 0.78  # Example
```

### Output: SimulationResult

```python
SimulationResult(
    scenario_id="scenario_001",
    duration_hours=8.0,
    total_wagons_processed=75,
    throughput_per_hour=9.375,
    average_waiting_time=12.5,
    track_utilization=0.78
)
```

## Phase 5: Output Generation

### Input: SimulationResult + Events + Wagons

### Process: Output Service

```python
import csv
from pathlib import Path

class OutputService:
    def export_results(
        self,
        results: SimulationResult,
        wagons: list[Wagon],
        events: list[SimulationEvent],
        output_path: Path
    ) -> None:
        # 1. CSV exports
        self._export_summary_csv(results, output_path / "summary.csv")
        self._export_wagons_csv(wagons, output_path / "wagons.csv")
        self._export_events_csv(events, output_path / "events.csv")

        # 2. Charts
        self._generate_charts(results, wagons, output_path / "charts")

    def _export_summary_csv(
        self, 
        results: SimulationResult, 
        path: Path
    ) -> None:
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Wagons', results.total_wagons_processed])
            writer.writerow(['Throughput', results.throughput_per_hour])
            writer.writerow(['Avg Waiting Time', results.average_waiting_time])
            writer.writerow(['Utilization', results.track_utilization])

    def _generate_charts(
        self,
        results: SimulationResult,
        wagons: list[Wagon],
        output_path: Path
    ) -> None:
        import matplotlib.pyplot as plt

        output_path.mkdir(parents=True, exist_ok=True)

        # Generate throughput chart
        self._plot_throughput(wagons, output_path / "throughput.png")

        # Generate waiting time distribution
        self._plot_waiting_times(wagons, output_path / "waiting_times.png")
```

### Output: Files

```
results/
├── summary.csv
├── wagons.csv
├── events.csv
└── charts/
    ├── throughput.png
    └── waiting_times.png
```

## Data Transformations Summary

| Phase | Input | Transformation | Output |
|-------|-------|----------------|--------|
| **1. Config** | JSON/CSV Files | Parse + Validate | `ScenarioConfig` |
| **2. Setup** | `ScenarioConfig` | Create Domain Models | `Workshop` |
| **3. Simulation** | `Workshop` + Config | SimPy Processes | `Events` + `Wagons` |
| **4. KPIs** | `Events` + `Wagons` | Aggregate + Calculate | `SimulationResult` |
| **5. Output** | `SimulationResult` | Format + Visualize | CSV + Charts |

## Error Handling Flow

```python
import sys
import logging

logger = logging.getLogger(__name__)

try:
    # Phase 1: Configuration
    config = config_service.load_scenario(config_path)
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

try:
    # Phase 2-3: Simulation
    results = simulation_service.run(config)
except RuntimeError as e:
    logger.error(f"Simulation error: {e}")
    sys.exit(2)

try:
    # Phase 4-5: Output
    output_service.export_results(results, output_path)
except IOError as e:
    logger.error(f"Output error: {e}")
    sys.exit(3)
```

## Performance Considerations

### Memory Management
```python
from typing import Iterator

class StreamingOutputService:
    def export_wagons_streaming(
        self, 
        wagons: Iterator[Wagon], 
        path: Path
    ) -> None:
        """Write wagons directly without holding all in memory"""
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['wagon_id', 'train_id', 'track_id'])

            for wagon in wagons:
                writer.writerow([wagon.id, wagon.train_id, wagon.track_id])
```

### Batch Processing
```python
class BatchKPIService:
    def calculate_kpis_batched(
        self,
        events: list[SimulationEvent],
        batch_size: int = 1000
    ) -> None:
        for i in range(0, len(events), batch_size):
            batch = events[i:i+batch_size]
            self._process_batch(batch)
```
