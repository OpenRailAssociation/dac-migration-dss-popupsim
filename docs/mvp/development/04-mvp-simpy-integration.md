# 4. MVP SimPy Integration

## Overview

**Note:** See [Architecture Section 4.2](../architecture/04-solution-strategy.md#42-technology-decisions) for SimPy decision rationale.

This document describes SimPy integration as discrete event simulation engine for MVP. Focus is on **thin adapter pattern** to decouple domain logic from SimPy and enable future replaceability.

## Architecture Principle: Thin Adapter

```
┌─────────────────────────────────────────┐
│     Domain Logic (Framework-free)      │
│  Workshop, Wagon, Train, Track          │
└─────────────────┬───────────────────────┘
                  │
                  │ Interface
                  │
┌─────────────────▼───────────────────────┐
│      SimPy Adapter (Thin Layer)         │
│  - SimPy Environment Wrapper            │
│  - Process Generators                   │
│  - Resource Management                  │
└─────────────────┬───────────────────────┘
                  │
                  │
┌─────────────────▼───────────────────────┐
│         SimPy Framework                 │
│  Environment, Resource, Process         │
└─────────────────────────────────────────┘
```

**Goal:** Domain logic can be tested without SimPy, SimPy can be replaced later.

## SimPy Core Concepts

### Environment
```python
import simpy

# SimPy Environment = Simulation clock
env = simpy.Environment()

# Time in minutes (MVP convention)
env.run(until=480)  # 8 hours = 480 minutes
```

### Resource
```python
# Resource = Limited capacity (e.g. workshop track)
track_resource = simpy.Resource(env, capacity=5)

# Request = Request resource
with track_resource.request() as req:
    yield req  # Wait until available
    # Resource is now occupied
    yield env.timeout(30)  # Work for 30 minutes
    # Resource is automatically released
```

### Process
```python
# Process = Generator function
def train_arrival_process(env: simpy.Environment) -> Generator:
    while True:
        yield env.timeout(60)  # Every 60 minutes
        print(f"Train arrives at t={env.now}")

# Register process
env.process(train_arrival_process(env))
```

## MVP SimPy Adapter

### 1. Environment Wrapper

```python
from typing import Protocol, Generator, Any
import simpy

class SimulationEnvironment(Protocol):
    """Interface for simulation environment (SimPy-independent)"""

    @property
    def now(self) -> float:
        """Current simulation time"""
        ...

    def timeout(self, delay: float) -> Any:
        """Wait for delay time units"""
        ...

    def process(self, generator: Generator) -> Any:
        """Register a process"""
        ...

    def run(self, until: float) -> None:
        """Run simulation until time 'until'"""
        ...


class SimPyEnvironmentAdapter:
    """Thin adapter for SimPy environment"""

    def __init__(self) -> None:
        self._env = simpy.Environment()

    @property
    def now(self) -> float:
        return self._env.now

    def timeout(self, delay: float) -> Any:
        return self._env.timeout(delay)

    def process(self, generator: Generator) -> Any:
        return self._env.process(generator)

    def run(self, until: float) -> None:
        self._env.run(until=until)

    @property
    def simpy_env(self) -> simpy.Environment:
        """Access to native SimPy environment (for resources)"""
        return self._env
```

### 2. Workshop SimPy Adapter

```python
from dataclasses import dataclass
from typing import Generator

@dataclass
class WorkshopSimPyAdapter:
    """Adapter between workshop domain and SimPy"""

    workshop: Workshop
    env: SimPyEnvironmentAdapter

    def __post_init__(self) -> None:
        """Initialize SimPy resources for all tracks"""
        for track in self.workshop.tracks:
            track.resource = simpy.Resource(
                self.env.simpy_env,
                capacity=track.capacity
            )

    def train_arrival_process(
        self,
        interval_minutes: int,
        wagons_per_train: int
    ) -> Generator:
        """SimPy process: Trains arrive"""
        train_counter = 0

        while True:
            # Wait for next train
            yield self.env.timeout(interval_minutes)

            # Create train with wagons
            train_counter += 1
            train = Train(
                id=f"TRAIN{train_counter:04d}",
                arrival_time=self.env.now,
                wagons=[
                    Wagon(
                        id=f"WAGON{train_counter:04d}_{i:02d}",
                        train_id=f"TRAIN{train_counter:04d}",
                        needs_retrofit=True
                    )
                    for i in range(wagons_per_train)
                ]
            )

            # Start retrofit for all wagons
            for wagon in train.wagons:
                self.env.process(self.retrofit_process(wagon))

    def retrofit_process(self, wagon: Wagon) -> Generator:
        """SimPy process: Wagon is retrofitted"""
        wagon.arrival_time = self.env.now

        # Select track (MVP: Simple strategy - first available)
        track = self._select_track()

        # Request track resource
        with track.resource.request() as req:
            yield req  # Wait until track available

            # Retrofit starts
            wagon.retrofit_start_time = self.env.now
            wagon.track_id = track.id
            track.current_wagons += 1

            # Perform retrofit
            yield self.env.timeout(track.retrofit_time_min)

            # Retrofit completed
            wagon.retrofit_end_time = self.env.now
            wagon.needs_retrofit = False
            track.current_wagons -= 1

    def _select_track(self) -> WorkshopTrack:
        """Select available track (MVP: Round-robin)"""
        # MVP: Simply first available track
        for track in self.workshop.tracks:
            if track.is_available():
                return track
        # Fallback: First track (will wait)
        return self.workshop.tracks[0]
```

### 3. Event Logging Adapter

```python
class EventLogger:
    """Logs simulation events for later analysis"""

    def __init__(self) -> None:
        self.events: list[SimulationEvent] = []

    def log_train_arrival(
        self, 
        env: SimulationEnvironment, 
        train: Train
    ) -> None:
        event = TrainArrivalEvent(
            timestamp=env.now,
            train_id=train.id,
            wagon_count=len(train.wagons)
        )
        self.events.append(event)

    def log_retrofit_start(
        self,
        env: SimulationEnvironment,
        wagon: Wagon,
        track: WorkshopTrack
    ) -> None:
        event = RetrofitStartEvent(
            timestamp=env.now,
            wagon_id=wagon.id,
            track_id=track.id
        )
        self.events.append(event)

    def log_retrofit_complete(
        self,
        env: SimulationEnvironment,
        wagon: Wagon,
        track: WorkshopTrack
    ) -> None:
        event = RetrofitCompleteEvent(
            timestamp=env.now,
            wagon_id=wagon.id,
            track_id=track.id
        )
        self.events.append(event)
```

## Simulation Orchestration

```python
class SimulationService:
    """Orchestrates complete simulation"""

    def __init__(self, config: ScenarioConfig) -> None:
        self.config = config
        self.env = SimPyEnvironmentAdapter()
        self.event_logger = EventLogger()

    def run(self) -> SimulationResults:
        """Run simulation"""

        # 1. Setup workshop
        workshop = self._setup_workshop()

        # 2. Create adapter
        adapter = WorkshopSimPyAdapter(
            workshop=workshop,
            env=self.env,
            event_logger=self.event_logger
        )

        # 3. Register processes
        self.env.process(
            adapter.train_arrival_process(
                interval_minutes=self.config.trains.arrival_interval_minutes,
                wagons_per_train=self.config.trains.wagons_per_train
            )
        )

        # 4. Run simulation
        duration_minutes = self.config.duration_hours * 60
        self.env.run(until=duration_minutes)

        # 5. Collect results
        return self._collect_results(workshop)

    def _setup_workshop(self) -> Workshop:
        """Create workshop from config"""
        tracks = [
            WorkshopTrack(
                id=track_config.id,
                capacity=track_config.capacity,
                retrofit_time_min=track_config.retrofit_time_min,
                current_wagons=0,
                resource=None  # Set by adapter
            )
            for track_config in self.config.workshop.tracks
        ]
        return Workshop(id="workshop_001", tracks=tracks)

    def _collect_results(self, workshop: Workshop) -> SimulationResults:
        """Collect results from events and wagons"""
        # Implementation see KPI service
        pass
```

## Testing Strategy

### Unit Tests (without SimPy)

```python
# Domain logic can be tested without SimPy
def test_wagon_waiting_time() -> None:
    wagon = Wagon(
        id="W001",
        train_id="T001",
        arrival_time=10.0,
        retrofit_start_time=15.0
    )
    assert wagon.waiting_time == 5.0

def test_track_availability() -> None:
    track = WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=3
    )
    assert track.is_available() == True

    track.current_wagons = 5
    assert track.is_available() == False
```

### Integration Tests (with SimPy)

```python
def test_simple_simulation() -> None:
    """Test with SimPy environment"""
    env = SimPyEnvironmentAdapter()

    workshop = Workshop(
        id="test_workshop",
        tracks=[
            WorkshopTrack(
                id="TRACK01",
                capacity=2,
                retrofit_time_min=30,
                resource=simpy.Resource(env.simpy_env, capacity=2)
            )
        ]
    )

    adapter = WorkshopSimPyAdapter(
        workshop=workshop,
        env=env,
        event_logger=EventLogger()
    )

    # Create test wagon
    wagon = Wagon(id="W001", train_id="T001")

    # Start retrofit process
    env.process(adapter.retrofit_process(wagon))

    # Run simulation
    env.run(until=60)

    # Assertions
    assert wagon.retrofit_end_time is not None
    assert wagon.needs_retrofit == False
```

## Best Practices

### ✅ Do's
- Domain logic in separate classes (without SimPy imports)
- Use thin adapter pattern
- Log events for traceability
- Keep generator functions small
- Type hints for better IDE support

### ❌ Don'ts
- Don't import SimPy directly in domain logic
- No complex logic in generator functions
- No global SimPy resources
- No direct `yield` statements in domain models

## Migration Path (Post-MVP)

### Full Version: Replace SimPy

```python
# Alternative: Salabim
class SalabimEnvironmentAdapter(SimulationEnvironment):
    def __init__(self) -> None:
        import salabim as sim
        self._env = sim.Environment()

    # Implement same interface
    ...

# Alternative: Custom discrete event engine
class CustomDESAdapter(SimulationEnvironment):
    def __init__(self) -> None:
        self._event_queue: PriorityQueue = PriorityQueue()
        self._current_time: float = 0.0

    # Implement same interface
    ...
```

**Effort:** Estimated 2-3 days (to be validated), as domain logic remains unchanged.
