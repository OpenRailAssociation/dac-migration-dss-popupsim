# PopUpSim MVP - Data Flow

## Übersicht

Diese Datei beschreibt den Datenfluss durch die 3 MVP Bounded Contexts: Configuration, Workshop, und Simulation Control.

---

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
│                     2. WORKSHOP CONTEXT                         │
└─────────────────────────────────────────────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  Workshop       │
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
│                  3. SIMULATION CONTROL CONTEXT                  │
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
                          CSV + Charts + JSON
                                   │
                                   ▼
                          results/ Directory
```

---

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
class ConfigurationService:
    def load_scenario(self, config_path: Path) -> ScenarioConfig:
        # 1. Lade scenario.json
        scenario_data = self._load_json(config_path / "scenario.json")

        # 2. Lade workshop_tracks.csv
        tracks_data = self._load_csv(config_path / "workshop_tracks.csv")

        # 3. Lade train_schedule.csv
        trains_data = self._load_csv(config_path / "train_schedule.csv")

        # 4. Validiere und erstelle Pydantic Models
        config = ScenarioConfig(
            duration_hours=scenario_data["duration_hours"],
            random_seed=scenario_data["random_seed"],
            workshop=WorkshopConfig(
                tracks=[
                    WorkshopTrackConfig(**track)
                    for track in tracks_data
                ]
            ),
            trains=TrainConfig(**trains_data)
        )

        # 5. Validiere Business Rules
        self._validate_config(config)

        return config
```

### Output: ScenarioConfig
```python
ScenarioConfig(
    duration_hours=8,
    random_seed=42,
    workshop=WorkshopConfig(
        tracks=[
            WorkshopTrackConfig(
                id="TRACK01",
                capacity=5,
                retrofit_time_min=30
            ),
            WorkshopTrackConfig(
                id="TRACK02",
                capacity=3,
                retrofit_time_min=45
            )
        ]
    ),
    trains=TrainConfig(
        arrival_interval_minutes=60,
        wagons_per_train=10
    )
)
```

---

## Phase 2: Workshop Setup

### Input: ScenarioConfig

### Process: Workshop Service

```python
class WorkshopService:
    def setup_workshop(
        self,
        config: WorkshopConfig,
        env: SimPyEnvironmentAdapter
    ) -> Workshop:
        # 1. Erstelle Tracks aus Config
        tracks = []
        for track_config in config.tracks:
            track = WorkshopTrack(
                id=track_config.id,
                capacity=track_config.capacity,
                retrofit_time_min=track_config.retrofit_time_min,
                current_wagons=0,
                resource=None  # Wird von Adapter gesetzt
            )
            tracks.append(track)

        # 2. Erstelle Workshop
        workshop = Workshop(
            id="workshop_001",
            tracks=tracks
        )

        return workshop
```

### Output: Workshop Domain Model
```python
Workshop(
    id="workshop_001",
    tracks=[
        WorkshopTrack(
            id="TRACK01",
            capacity=5,
            retrofit_time_min=30,
            current_wagons=0,
            resource=None
        ),
        WorkshopTrack(
            id="TRACK02",
            capacity=3,
            retrofit_time_min=45,
            current_wagons=0,
            resource=None
        )
    ]
)
```

---

## Phase 3: Simulation Execution

### Input: Workshop + ScenarioConfig

### Process: SimPy Adapter

```python
class WorkshopSimPyAdapter:
    def __init__(self, workshop: Workshop, env: SimPyEnvironmentAdapter):
        self.workshop = workshop
        self.env = env
        self.event_logger = EventLogger()
        self.all_wagons: List[Wagon] = []

        # Initialisiere SimPy Resources
        for track in self.workshop.tracks:
            track.resource = simpy.Resource(
                self.env.simpy_env,
                capacity=track.capacity
            )

    def train_arrival_process(self, train_schedule: List[TrainArrival]):
        """Verarbeitet explizite Zugankünfte aus Fahrplan"""
        # Sortiere Züge nach Ankunftszeit
        sorted_trains = sorted(
            train_schedule,
            key=lambda t: datetime.combine(t.arrival_date, t.arrival_time)
        )

        for train_arrival in sorted_trains:
            # Berechne Wartezeit bis Ankunft
            arrival_datetime = datetime.combine(
                train_arrival.arrival_date,
                train_arrival.arrival_time
            )
            wait_minutes = (arrival_datetime - self.env.start_datetime).total_seconds() / 60

            if wait_minutes > 0:
                yield self.env.timeout(wait_minutes)

            # Erstelle Train mit Wagons aus Fahrplan
            train = Train(
                id=train_arrival.train_id,
                arrival_time=self.env.now,
                wagons=[
                    Wagon(
                        id=wagon_info.wagon_id,
                        train_id=train_arrival.train_id,
                        length=wagon_info.length,
                        is_loaded=wagon_info.is_loaded,
                        needs_retrofit=wagon_info.needs_retrofit
                    )
                    for wagon_info in train_arrival.wagons
                ]
            )

            # Log Event
            self.event_logger.log_train_arrival(self.env, train)

            # Starte Retrofit nur für Wagons die es brauchen
            for wagon in train.wagons:
                self.all_wagons.append(wagon)
                if wagon.needs_retrofit:
                    self.env.process(self.retrofit_process(wagon))

    def retrofit_process(self, wagon: Wagon):
        wagon.arrival_time = self.env.now

        # Wähle Track
        track = self._select_track()

        # Fordere Resource an
        with track.resource.request() as req:
            yield req

            # Start Retrofit
            wagon.retrofit_start_time = self.env.now
            wagon.track_id = track.id
            track.current_wagons += 1
            self.event_logger.log_retrofit_start(self.env, wagon, track)

            # Retrofit Duration
            yield self.env.timeout(track.retrofit_time_min)

            # Complete Retrofit
            wagon.retrofit_end_time = self.env.now
            wagon.needs_retrofit = False
            track.current_wagons -= 1
            self.event_logger.log_retrofit_complete(self.env, wagon, track)
```

### Output: Events + Wagons

**Events:**
```python
[
    TrainArrivalEvent(timestamp=60.0, train_id="TRAIN0001", wagon_count=10),
    RetrofitStartEvent(timestamp=60.0, wagon_id="WAGON0001_00", track_id="TRACK01", waiting_time=0.0),
    RetrofitCompleteEvent(timestamp=90.0, wagon_id="WAGON0001_00", track_id="TRACK01", retrofit_duration=30.0),
    ...
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
    ...
]
```

---

## Phase 4: KPI Calculation

### Input: Events + Wagons

### Process: KPI Service

```python
class KPIService:
    def calculate_kpis(
        self,
        wagons: List[Wagon],
        events: List[SimulationEvent],
        duration_hours: float
    ) -> SimulationResults:

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

        # 4. Calculate utilization from events
        utilization = self._calculate_utilization(events, duration_hours)

        # 5. Calculate queue metrics
        queue_metrics = self._calculate_queue_metrics(events)

        # 6. Create results
        return SimulationResults(
            scenario_id="scenario_001",
            duration_hours=duration_hours,
            total_wagons_processed=len(processed),
            throughput_per_hour=throughput,
            average_waiting_time=statistics.mean(waiting_times) if waiting_times else 0,
            max_waiting_time=max(waiting_times) if waiting_times else 0,
            min_waiting_time=min(waiting_times) if waiting_times else 0,
            track_utilization=utilization,
            average_queue_length=queue_metrics["avg"],
            max_queue_length=queue_metrics["max"],
            simulation_start=datetime.now(),
            simulation_end=datetime.now()
        )

    def _calculate_utilization(
        self,
        events: List[SimulationEvent],
        duration_hours: float
    ) -> float:
        """Berechne durchschnittliche Track-Auslastung"""
        # Track occupancy over time
        occupancy_timeline = []

        for event in events:
            if isinstance(event, TrackOccupiedEvent):
                occupancy_timeline.append((event.timestamp, event.current_occupancy))
            elif isinstance(event, TrackFreeEvent):
                occupancy_timeline.append((event.timestamp, event.current_occupancy))

        # Calculate weighted average
        if not occupancy_timeline:
            return 0.0

        total_capacity_time = 0.0
        for i in range(len(occupancy_timeline) - 1):
            time_delta = occupancy_timeline[i+1][0] - occupancy_timeline[i][0]
            occupancy = occupancy_timeline[i][1]
            total_capacity_time += occupancy * time_delta

        return total_capacity_time / (duration_hours * 60)  # Normalize

    def _calculate_queue_metrics(
        self,
        events: List[SimulationEvent]
    ) -> dict:
        """Berechne Queue-Metriken"""
        queue_lengths = []
        current_queue = 0

        for event in events:
            if isinstance(event, WagonQueuedEvent):
                current_queue += 1
            elif isinstance(event, RetrofitStartEvent):
                current_queue = max(0, current_queue - 1)

            queue_lengths.append(current_queue)

        return {
            "avg": statistics.mean(queue_lengths) if queue_lengths else 0,
            "max": max(queue_lengths) if queue_lengths else 0
        }
```

### Output: SimulationResults

```python
SimulationResults(
    scenario_id="scenario_001",
    duration_hours=8.0,
    total_wagons_processed=75,
    throughput_per_hour=9.375,
    average_waiting_time=12.5,
    max_waiting_time=45.0,
    min_waiting_time=0.0,
    track_utilization=0.78,
    average_queue_length=3.2,
    max_queue_length=12,
    simulation_start=datetime(2024, 1, 15, 10, 0, 0),
    simulation_end=datetime(2024, 1, 15, 10, 5, 30)
)
```

---

## Phase 5: Output Generation

### Input: SimulationResults + Events + Wagons

### Process: Output Service

```python
class OutputService:
    def export_results(
        self,
        results: SimulationResults,
        wagons: List[Wagon],
        events: List[SimulationEvent],
        output_path: Path
    ):
        # 1. CSV Exports
        self._export_summary_csv(results, output_path / "summary.csv")
        self._export_wagons_csv(wagons, output_path / "wagons.csv")
        self._export_events_csv(events, output_path / "events.csv")

        # 2. JSON Export
        self._export_json(results, output_path / "results.json")

        # 3. Charts
        self._generate_charts(results, wagons, events, output_path / "charts")

    def _export_summary_csv(self, results: SimulationResults, path: Path):
        import csv

        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Wagons Processed', results.total_wagons_processed])
            writer.writerow(['Throughput (wagons/hour)', results.throughput_per_hour])
            writer.writerow(['Avg Waiting Time (min)', results.average_waiting_time])
            writer.writerow(['Track Utilization', results.track_utilization])
            writer.writerow(['Avg Queue Length', results.average_queue_length])

    def _export_wagons_csv(self, wagons: List[Wagon], path: Path):
        import csv

        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'wagon_id', 'train_id', 'track_id',
                'arrival_time', 'retrofit_start_time', 'retrofit_end_time',
                'waiting_time', 'retrofit_duration'
            ])

            for wagon in wagons:
                writer.writerow([
                    wagon.id,
                    wagon.train_id,
                    wagon.track_id,
                    wagon.arrival_time,
                    wagon.retrofit_start_time,
                    wagon.retrofit_end_time,
                    wagon.waiting_time,
                    wagon.retrofit_duration
                ])

    def _generate_charts(
        self,
        results: SimulationResults,
        wagons: List[Wagon],
        events: List[SimulationEvent],
        output_path: Path
    ):
        import matplotlib.pyplot as plt

        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Throughput over time
        self._plot_throughput(wagons, output_path / "throughput.png")

        # 2. Waiting time distribution
        self._plot_waiting_times(wagons, output_path / "waiting_times.png")

        # 3. Track utilization
        self._plot_utilization(events, output_path / "utilization.png")
```

### Output: Files

```
results/
├── summary.csv
├── wagons.csv
├── events.csv
├── results.json
└── charts/
    ├── throughput.png
    ├── waiting_times.png
    └── utilization.png
```

---

## Data Transformations Summary

| Phase | Input | Transformation | Output |
|-------|-------|----------------|--------|
| **1. Config** | JSON/CSV Files | Parse + Validate | `ScenarioConfig` |
| **2. Setup** | `ScenarioConfig` | Create Domain Models | `Workshop` |
| **3. Simulation** | `Workshop` + Config | SimPy Processes | `Events` + `Wagons` |
| **4. KPIs** | `Events` + `Wagons` | Aggregate + Calculate | `SimulationResults` |
| **5. Output** | `SimulationResults` | Format + Visualize | CSV + Charts + JSON |

---

## Error Handling Flow

```python
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

---

## Performance Considerations

### Memory Management
```python
# Streaming für große Datenmengen
class StreamingOutputService:
    def export_wagons_streaming(self, wagons: Iterator[Wagon], path: Path):
        """Schreibe Wagons direkt ohne alles im Memory zu halten"""
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['wagon_id', 'train_id', ...])

            for wagon in wagons:
                writer.writerow([wagon.id, wagon.train_id, ...])
```

### Batch Processing
```python
# Verarbeite Events in Batches
class BatchKPIService:
    def calculate_kpis_batched(
        self,
        events: List[SimulationEvent],
        batch_size: int = 1000
    ):
        for i in range(0, len(events), batch_size):
            batch = events[i:i+batch_size]
            self._process_batch(batch)
```

---

**Navigation:** [← 4 Simpy integration](04-mvp-simpy-integration.md) | [Technology stack →](06-mvp-technology-stack.md)
