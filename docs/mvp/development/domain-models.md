# Domain Models Reference

## Overview

**Note:** See actual implementation in `popupsim/backend/src/domain/` and `popupsim/backend/src/configuration/`

This document provides a quick reference for all domain models in the MVP.

## Configuration Models

### ScenarioConfig

```python
from pydantic import BaseModel, Field
from datetime import date

class ScenarioConfig(BaseModel):
    """Main scenario models"""
    scenario_id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$', min_length=1, max_length=50)
    start_date: date
    end_date: date
    workshop: Workshop | None = None
    train_schedule_file: str
    routes_file: str | None = None
    workshop_tracks_file: str | None = None
```

### Workshop

```python
class Workshop(BaseModel):
    """Workshop with tracks"""
    tracks: list[WorkshopTrack] = Field(min_length=1)
```

### WorkshopTrack

```python
from enum import Enum

class TrackFunction(str, Enum):
    WERKSTATTGLEIS = "werkstattgleis"
    SAMMELGLEIS = "sammelgleis"
    PARKGLEIS = "parkgleis"
    WERKSTATTZUFUEHRUNG = "werkstattzufuehrung"
    WERKSTATTABFUEHRUNG = "werkstattabfuehrung"
    BAHNHOFSKOPF = "bahnhofskopf"

class WorkshopTrack(BaseModel):
    """Individual workshop track"""
    id: str
    function: TrackFunction
    capacity: int = Field(ge=1)
    retrofit_time_min: int = Field(ge=0)
```

## Domain Entities

### Train

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Train:
    """Train with multiple wagons"""
    id: str
    arrival_time: datetime
    wagons: list[Wagon]
    origin: str
    destination: str

    def get_total_length(self) -> float:
        return sum(wagon.length for wagon in self.wagons)

    def get_retrofit_wagons(self) -> list[Wagon]:
        return [w for w in self.wagons if w.needs_retrofit]
```

### Wagon

```python
@dataclass
class Wagon:
    """Individual freight wagon"""
    id: str
    train_id: str
    length: float
    needs_retrofit: bool
    status: str = "arriving"
    arrival_time: float | None = None
    retrofit_start_time: float | None = None
    retrofit_end_time: float | None = None
    track_id: str | None = None

    @property
    def waiting_time(self) -> float | None:
        if self.arrival_time and self.retrofit_start_time:
            return self.retrofit_start_time - self.arrival_time
        return None

    @property
    def retrofit_duration(self) -> float | None:
        if self.retrofit_start_time and self.retrofit_end_time:
            return self.retrofit_end_time - self.retrofit_start_time
        return None
```

### Track

```python
@dataclass
class Track:
    """Track with capacity management"""
    id: str
    name: str
    length: float
    track_type: str
    capacity: int
    current_occupancy: float = 0.0
    current_wagon_count: int = 0

    def can_accommodate(self, length: float) -> bool:
        return self.current_occupancy + length <= self.length

    def can_accommodate_wagon(self) -> bool:
        return self.current_wagon_count < self.capacity

    def occupy_space(self, length: float) -> None:
        if not self.can_accommodate(length):
            raise InsufficientCapacityError(
                f"Track {self.id} cannot accommodate {length}m"
            )
        self.current_occupancy += length
        self.current_wagon_count += 1

    def free_space(self, length: float) -> None:
        self.current_occupancy = max(0, self.current_occupancy - length)
        self.current_wagon_count = max(0, self.current_wagon_count - 1)

    def get_utilization_percent(self) -> float:
        return (self.current_occupancy / self.length) * 100
```

## Value Objects

### ValidationResult

```python
@dataclass(frozen=True)
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
```

### SimulationResult

```python
@dataclass(frozen=True)
class SimulationResult:
    """Result of simulation"""
    scenario_id: str
    duration_hours: int
    total_trains_processed: int
    total_wagons_processed: int
    average_processing_time_minutes: float
    throughput_per_hour: float
    track_utilization: dict[str, float]
    bottlenecks: list[str]
```

### ThroughputEstimate

```python
@dataclass(frozen=True)
class ThroughputEstimate:
    """Throughput estimation"""
    wagons_per_hour: float
    wagons_per_day: float
    efficiency_factor: float
    bottleneck: str | None = None

    def with_efficiency(self, factor: float) -> 'ThroughputEstimate':
        return ThroughputEstimate(
            wagons_per_hour=self.wagons_per_hour * factor,
            wagons_per_day=self.wagons_per_day * factor,
            efficiency_factor=factor,
            bottleneck=self.bottleneck
        )
```

## Events

### SimulationEvent

```python
@dataclass
class SimulationEvent:
    """Base simulation event"""
    timestamp: float
    event_type: str
```

### TrainArrivalEvent

```python
@dataclass
class TrainArrivalEvent(SimulationEvent):
    """Train arrival event"""
    train_id: str
    wagon_count: int
    event_type: str = "train_arrival"
```

### RetrofitStartEvent

```python
@dataclass
class RetrofitStartEvent(SimulationEvent):
    """Retrofit start event"""
    wagon_id: str
    track_id: str
    waiting_time: float
    event_type: str = "retrofit_start"
```

### RetrofitCompleteEvent

```python
@dataclass
class RetrofitCompleteEvent(SimulationEvent):
    """Retrofit complete event"""
    wagon_id: str
    track_id: str
    retrofit_duration: float
    event_type: str = "retrofit_complete"
```

## Exceptions

```python
class PopUpSimDomainError(Exception):
    """Base domain error"""
    pass

class ValidationError(PopUpSimDomainError):
    """Configuration validation error"""
    pass

class SimulationRuntimeError(PopUpSimDomainError):
    """Simulation runtime error"""
    pass

class InsufficientCapacityError(PopUpSimDomainError):
    """Insufficient track/workshop capacity"""
    pass

class TrackNotFoundError(PopUpSimDomainError):
    """Track not found"""
    pass

class InvalidRouteError(PopUpSimDomainError):
    """Invalid route definition"""
    pass
```

## Type Aliases

```python
from typing import TypeAlias

# Common type aliases
WagonId: TypeAlias = str
TrainId: TypeAlias = str
TrackId: TypeAlias = str
ScenarioId: TypeAlias = str
SimulationTime: TypeAlias = float  # Minutes since start

# Collection types
WagonList: TypeAlias = list[Wagon]
TrackList: TypeAlias = list[Track]
EventList: TypeAlias = list[SimulationEvent]
```

## Model Relationships

```
ScenarioConfig
├── Workshop
│   └── WorkshopTrack[]
└── train_schedule_file → Train[]
                          └── Wagon[]

Simulation Runtime:
Train → Wagon[] → WorkshopTrack → SimulationEvent[]
```

## Usage Examples

### Creating a Scenario

```python
scenario = ScenarioConfig(
    scenario_id="demo",
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
    train_schedule_file="schedule.csv"
)
```

### Processing a Wagon

```python
wagon = Wagon(
    id="W001",
    train_id="T001",
    length=15.5,
    needs_retrofit=True
)

# Wagon arrives
wagon.arrival_time = env.now

# Start retrofit
wagon.retrofit_start_time = env.now
wagon.track_id = "TRACK01"

# Complete retrofit
wagon.retrofit_end_time = env.now
wagon.needs_retrofit = False

# Calculate metrics
print(f"Waiting time: {wagon.waiting_time} minutes")
print(f"Retrofit duration: {wagon.retrofit_duration} minutes")
```

### Calculating Throughput

```python
estimate = ThroughputEstimate(
    wagons_per_hour=10.0,
    wagons_per_day=240.0,
    efficiency_factor=0.85
)

# Adjust for different efficiency
realistic_estimate = estimate.with_efficiency(0.75)
print(f"Realistic throughput: {realistic_estimate.wagons_per_day} wagons/day")
```

## Model Validation

All Pydantic models are automatically validated:

```python
# Valid
track = WorkshopTrack(
    id="TRACK01",
    function=TrackFunction.WERKSTATTGLEIS,
    capacity=5,
    retrofit_time_min=30
)

# Invalid - raises ValidationError
track = WorkshopTrack(
    id="TRACK01",
    function=TrackFunction.WERKSTATTGLEIS,
    capacity=0,  # Must be >= 1
    retrofit_time_min=30
)
```

## Immutability

Value objects are immutable (frozen dataclasses):

```python
result = SimulationResult(
    scenario_id="demo",
    duration_hours=8,
    ...
)

# This raises an error
result.duration_hours = 10  # ❌ FrozenInstanceError
```

## Type Checking

All models include type hints for MyPy:

```bash
# Type check passes
uv run mypy backend/src/

# Type error example
wagon: Wagon = "not a wagon"  # ❌ Type error
```
