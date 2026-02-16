# Domain Models Reference

## Overview

**Location:** `popupsim/backend/src/contexts/`

This document provides a quick reference for domain models across the 4 bounded contexts.

---

## Configuration Context Models

**Location:** `contexts/configuration/domain/models/`

### Scenario

```python
from pydantic import BaseModel
from datetime import datetime

class Scenario(BaseModel):
    """Root configuration model."""
    id: str
    start_date: datetime
    end_date: datetime
    trains: list[Train] | None = None
    tracks: list[Track] | None = None
    workshops: list[Workshop] | None = None
    locomotives: list[Locomotive] | None = None
    routes: list[Route] | None = None
    process_times: ProcessTimes | None = None
```

### Workshop

```python
class Workshop(BaseModel):
    """Workshop configuration."""
    workshop_id: str
    track_id: str
    retrofit_stations: int
    name: str | None = None
```

### Track

```python
class Track(BaseModel):
    """Track configuration."""
    track_id: str
    track_type: str
    length: float
    fill_factor: float = 0.75
```

### ProcessTimes

```python
class ProcessTimes(BaseModel):
    """Timing parameters for all operations."""
    coupling_time: float
    decoupling_time: float
    retrofit_time_per_wagon: float
    train_preparation_time: float
```

---

## Retrofit Workflow Domain Models

**Location:** `contexts/retrofit_workflow/domain/`

### Wagon (Entity)

```python
from dataclasses import dataclass
from enum import Enum

class WagonStatus(str, Enum):
    ARRIVING = "arriving"
    SELECTING = "selecting"
    SELECTED = "selected"
    REJECTED = "rejected"
    MOVING = "moving"
    RETROFITTING = "retrofitting"
    RETROFITTED = "retrofitted"
    PARKING = "parking"

@dataclass
class Wagon:
    """Individual freight wagon."""
    wagon_id: str
    train_id: str
    length: float
    needs_retrofit: bool
    status: WagonStatus
    track_id: str | None = None
```

### Batch (Value Object)

```python
@dataclass(frozen=True)
class Batch:
    """Wagon batch for processing."""
    batch_id: str
    wagons: tuple[Wagon, ...]
    total_length: float
    
    @property
    def size(self) -> int:
        return len(self.wagons)
```

### Rake (Aggregate)

```python
@dataclass
class Rake:
    """Coupled wagon formation."""
    rake_id: str
    wagons: list[Wagon]
    
    def get_total_length(self) -> float:
        return sum(w.length for w in self.wagons)
```

---

## Railway Infrastructure Domain Models

**Location:** `contexts/railway_infrastructure/domain/aggregates/`

### Track (Entity)

```python
@dataclass
class Track:
    """Track with capacity management."""
    track_id: str
    track_type: str
    length: float
    fill_factor: float
    occupancy: TrackOccupancy
    
    def can_accommodate(self, wagon_length: float) -> bool:
        return self.occupancy.can_add(wagon_length, self.length, self.fill_factor)
```

### TrackOccupancy (Aggregate)

```python
@dataclass
class TrackOccupancy:
    """Manages wagon placement on track."""
    current_length: float = 0.0
    wagon_count: int = 0
    
    def can_add(self, wagon_length: float, track_length: float, fill_factor: float) -> bool:
        max_capacity = track_length * fill_factor
        return self.current_length + wagon_length <= max_capacity
    
    def add_wagon(self, wagon_length: float) -> None:
        self.current_length += wagon_length
        self.wagon_count += 1
    
    def remove_wagon(self, wagon_length: float) -> None:
        self.current_length = max(0.0, self.current_length - wagon_length)
        self.wagon_count = max(0, self.wagon_count - 1)
```

### TrackGroup (Aggregate)

```python
@dataclass
class TrackGroup:
    """Group of tracks by type."""
    track_type: str
    tracks: list[Track]
    
    def get_available_tracks(self, required_length: float) -> list[Track]:
        return [t for t in self.tracks if t.can_accommodate(required_length)]
```

---

## External Trains Domain Models

**Location:** `contexts/external_trains/domain/`

### TrainArrivedEvent (Domain Event)

```python
@dataclass(frozen=True)
class TrainArrivedEvent:
    """Train arrival event."""
    train_id: str
    wagons: tuple[Wagon, ...]
    arrival_time: float
```

---

## Shared Domain Models

**Location:** `contexts/shared/domain/`

### Locomotive (Entity)

```python
@dataclass
class Locomotive:
    """Locomotive resource."""
    locomotive_id: str
    status: str
    current_track_id: str | None = None
```

### Route (Value Object)

```python
@dataclass(frozen=True)
class Route:
    """Route between tracks."""
    route_id: str
    from_track_id: str
    to_track_id: str
    duration: float
```

---

## Enums

### TrackSelectionStrategy

```python
class TrackSelectionStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_OCCUPIED = "least_occupied"
    FIRST_AVAILABLE = "first_available"
    RANDOM = "random"
```

### LocoDeliveryStrategy

```python
class LocoDeliveryStrategy(str, Enum):
    RETURN_TO_PARKING = "return_to_parking"
    STAY_AT_WORKSHOP = "stay_at_workshop"
```

---

## Exceptions

```python
class PopUpSimError(Exception):
    """Base exception."""
    pass

class ConfigurationError(PopUpSimError):
    """Configuration error."""
    pass

class SimulationError(PopUpSimError):
    """Simulation runtime error."""
    pass

class InsufficientCapacityError(PopUpSimError):
    """Insufficient capacity."""
    pass
```

---

## Type Aliases

```python
from typing import TypeAlias

WagonId: TypeAlias = str
TrainId: TypeAlias = str
TrackId: TypeAlias = str
LocomotiveId: TypeAlias = str
SimulationTime: TypeAlias = float
```

---

## Model Relationships

```
Scenario (Configuration Context)
├── trains: list[Train]
├── tracks: list[Track]
├── workshops: list[Workshop]
├── locomotives: list[Locomotive]
└── routes: list[Route]

Train (External Trains Context)
└── wagons: list[Wagon]

TrackGroup (Railway Infrastructure Context)
└── tracks: list[Track]
    └── occupancy: TrackOccupancy

Batch (Retrofit Workflow Context)
└── wagons: tuple[Wagon, ...]

Rake (Retrofit Workflow Context)
└── wagons: list[Wagon]
```

---

## Usage Examples

### Loading Configuration

```python
from contexts.configuration.domain.configuration_builder import ConfigurationBuilder
from pathlib import Path

builder = ConfigurationBuilder(Path("scenario_dir"))
scenario = builder.build()
```

### Checking Track Capacity

```python
from contexts.railway_infrastructure.application.railway_context import RailwayContext

railway = RailwayContext(scenario)
track = railway.track_selector.select_track_with_capacity('collection', required_length=50.0)

if track:
    railway.place_wagons_on_track(track.track_id, wagons)
```

### Publishing Train Arrival

```python
from contexts.external_trains.domain.events.train_arrived_event import TrainArrivedEvent
from contexts.shared.domain.events.event_bus import EventBus

event = TrainArrivedEvent(
    train_id="T001",
    wagons=tuple(wagons),
    arrival_time=env.now
)

event_bus.publish(event)
```

### Forming Batch

```python
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService

service = BatchFormationService()
if service.can_form_batch(wagons, min_size=1, max_size=10):
    batch = service.form_batch(wagons, batch_size=5)
```

---

## Validation

All Pydantic models are automatically validated:

```python
# Valid
scenario = Scenario(
    id="test",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 2),
    ...
)

# Invalid - raises ValidationError
scenario = Scenario(
    id="",  # Empty ID not allowed
    ...
)
```

---

## Immutability

Value objects and events are immutable:

```python
# Immutable
event = TrainArrivedEvent(train_id="T001", wagons=(...), arrival_time=100.0)
# event.train_id = "T002"  # ❌ Error: frozen dataclass

# Mutable entities
wagon = Wagon(wagon_id="W001", ...)
wagon.status = WagonStatus.RETROFITTING  # ✅ OK
```

---

## Type Checking

All models include type hints for MyPy:

```bash
# Type check
uv run mypy popupsim/backend/src/
```

---

## Further Reading

- **[Configuration Validation](configuration-validation.md)** - Pydantic validation patterns
- **[Domain Model](03-mvp-domain-model.md)** - Domain model overview
- **[Bounded Contexts](02-mvp-contexts.md)** - Context architecture

---
