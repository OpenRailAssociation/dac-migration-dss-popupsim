# 5a. Level 3 Implementation Details

## Overview

This document provides Level 3 architectural details for the actual MVP implementation with 4 bounded contexts: Configuration, Retrofit Workflow, Railway Infrastructure, and External Trains.

## 5a.1 Configuration Context - Level 3

### Component Diagram

```mermaid
graph TB
    subgraph "Configuration Context - Level 3"
        Builder["ConfigurationBuilder<br/>Load from files"]
        Loader["FileLoader<br/>Parse JSON/CSV"]
        
        subgraph "Domain Models (Pydantic)"
            Scenario[Scenario]
            Train[Train]
            Wagon[Wagon]
            Track[Track]
            Workshop[Workshop]
            Locomotive[Locomotive]
            Routes[Routes]
            ProcessTimes[ProcessTimes]
        end
    end
    
    Files[JSON/CSV Files] --> Builder
    Builder --> Loader
    Loader --> Scenario
    Loader --> Train
    Loader --> Wagon
    Loader --> Track
    Loader --> Workshop
    Loader --> Locomotive
    Loader --> Routes
    Loader --> ProcessTimes

    classDef builder fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef model fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
    
    class Builder,Loader builder
    class Scenario,Train,Wagon,Track,Workshop,Locomotive,Routes,ProcessTimes model
```

### Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **ConfigurationBuilder** | `configuration_builder.py` | Load scenario from file path |
| **FileLoader** | `file_loader.py` | Parse JSON/CSV files, handle references |
| **Scenario** | `scenario.py` | Root configuration model with validation |
| **ProcessTimes** | `process_times.py` | Timing configuration for operations |
| **DTOs** | `dtos/` | Input data transfer objects |

### Code Example

```python
from pathlib import Path
from contexts.configuration.domain.configuration_builder import ConfigurationBuilder

# Load scenario
scenario = ConfigurationBuilder(Path("scenario_dir")).build()

# Access configuration
print(f"Scenario: {scenario.id}")
print(f"Workshops: {len(scenario.workshops)}")
print(f"Trains: {len(scenario.trains)}")
```

---

## 5a.2 Retrofit Workflow Context - Level 3

### Component Diagram

```mermaid
graph TB
    subgraph "Retrofit Workflow Context - Level 3"
        Context["RetrofitWorkflowContext<br/>Initialization & orchestration"]
        
        subgraph "Coordinators (Application Layer)"
            Arrival["ArrivalCoordinator<br/>Process train arrivals"]
            Collection["CollectionCoordinator<br/>Move to retrofit track"]
            Workshop["WorkshopCoordinator<br/>Retrofit operations"]
            Parking["ParkingCoordinator<br/>Move to parking"]
        end
        
        subgraph "Domain Services (No SimPy)"
            Batch["BatchFormationService"]
            Rake["RakeFormationService"]
            TrainForm["TrainFormationService"]
            Schedule["WorkshopSchedulingService"]
            Coupling["CouplingService"]
            Route["RouteService"]
        end
        
        subgraph "Resource Managers (Infrastructure)"
            LocoMgr["LocomotiveResourceManager"]
            TrackMgr["TrackCapacityManager"]
            WorkshopMgr["WorkshopResourceManager"]
        end
        
        subgraph "Metrics Collection"
            Metrics["SimulationMetrics"]
            WagonCol["WagonCollector"]
            LocoCol["LocomotiveCollector"]
            WorkshopCol["WorkshopCollector"]
        end
    end
    
    Context --> Arrival
    Context --> Collection
    Context --> Workshop
    Context --> Parking
    
    Arrival --> Batch
    Collection --> Rake
    Workshop --> Schedule
    Parking --> TrainForm
    
    Arrival --> LocoMgr
    Collection --> TrackMgr
    Workshop --> WorkshopMgr
    
    Context --> Metrics
    Metrics --> WagonCol
    Metrics --> LocoCol
    Metrics --> WorkshopCol
    
    classDef coord fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef domain fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
    classDef resource fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef metrics fill:#ffccbc,stroke:#bf360c,stroke-width:2px
    
    class Context,Arrival,Collection,Workshop,Parking coord
    class Batch,Rake,TrainForm,Schedule,Coupling,Route domain
    class LocoMgr,TrackMgr,WorkshopMgr resource
    class Metrics,WagonCol,LocoCol,WorkshopCol metrics
```

### Coordinators (Application Layer)

| Coordinator | Responsibility | SimPy Process |
|-------------|----------------|---------------|
| **ArrivalCoordinator** | Receive trains, classify wagons, distribute to collection tracks | Yes |
| **CollectionCoordinator** | Form batches, allocate locomotive, transport to retrofit track | Yes |
| **WorkshopCoordinator** | Assign wagons to workshops, execute retrofit, return to retrofitted track | Yes |
| **ParkingCoordinator** | Transport completed wagons to parking tracks | Yes |

### Domain Services (No SimPy Dependencies)

| Service | Responsibility |
|---------|----------------|
| **BatchFormationService** | Create wagon batches based on capacity constraints |
| **RakeFormationService** | Form and dissolve wagon rakes with coupling logic |
| **TrainFormationService** | Assemble trains (locomotive + rake) with preparation times |
| **WorkshopSchedulingService** | Schedule wagon batches to available workshops |
| **CouplingService** | Calculate coupling/decoupling times |
| **RouteService** | Provide route durations between tracks |

### Resource Managers (Infrastructure Layer)

| Manager | Responsibility |
|---------|----------------|
| **LocomotiveResourceManager** | Allocate and release locomotives (SimPy Resource) |
| **TrackCapacityManager** | Manage track capacity and wagon placement |
| **WorkshopResourceManager** | Manage workshop station availability (SimPy Resource) |

### Workflow Sequence

```mermaid
sequenceDiagram
    participant Train
    participant Arrival
    participant Collection
    participant Workshop
    participant Parking
    
    Train->>Arrival: TrainArrivedEvent
    Arrival->>Arrival: Classify wagons
    Arrival->>Collection: Add to collection queue
    Collection->>Collection: Form batch
    Collection->>Collection: Allocate locomotive
    Collection->>Workshop: Transport to retrofit track
    Workshop->>Workshop: Select workshop
    Workshop->>Workshop: Allocate stations
    Workshop->>Workshop: Execute retrofit
    Workshop->>Parking: Move to retrofitted track
    Parking->>Parking: Form batch
    Parking->>Parking: Transport to parking
```

---

## 5a.3 Railway Infrastructure Context - Level 3

### Component Diagram

```mermaid
graph TB
    subgraph "Railway Infrastructure Context - Level 3"
        Context["RailwayContext<br/>Track building & services"]
        
        subgraph "Aggregates"
            TrackGroup["TrackGroup<br/>Group tracks by type"]
            Track["Track<br/>Individual track entity"]
            Occupancy["TrackOccupancy<br/>Wagon placement logic"]
        end
        
        subgraph "Services"
            Selector["TrackSelector<br/>Selection strategies"]
            Capacity["CapacityService<br/>Capacity queries"]
        end
    end
    
    Context --> TrackGroup
    TrackGroup --> Track
    Track --> Occupancy
    Context --> Selector
    Context --> Capacity
    Selector --> TrackGroup
    Capacity --> Track
    
    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    
    class Context,TrackGroup,Track,Occupancy,Selector,Capacity component
```

### Components

| Component | Responsibility | Pattern |
|-----------|----------------|---------|
| **RailwayContext** | Build tracks from scenario, provide services | Context |
| **TrackGroup** | Group tracks by type (collection, retrofit, parking, workshop) | Aggregate |
| **Track** | Individual track with capacity and fill factor | Entity |
| **TrackOccupancy** | Manage wagon placement and capacity | Aggregate |
| **TrackSelector** | Select tracks based on strategies | Service |
| **CapacityService** | Query track capacity and availability | Service |

### Track Selection Strategies

- **LEAST_OCCUPIED**: Select track with lowest occupancy ratio
- **ROUND_ROBIN**: Cycle through available tracks
- **FIRST_AVAILABLE**: Select first track with capacity
- **RANDOM**: Random selection from available tracks

---

## 5a.4 External Trains Context - Level 3

### Component Diagram

```mermaid
graph TB
    subgraph "External Trains Context - Level 3"
        Context["ExternalTrainsContext<br/>Train arrival management"]
        
        subgraph "Components"
            Publisher["EventPublisher<br/>Publish train arrivals"]
            Factory["WagonFactory<br/>Create wagon entities"]
        end
        
        subgraph "Events"
            TrainEvent["TrainArrivedEvent<br/>Train + wagons"]
        end
    end
    
    Context --> Publisher
    Context --> Factory
    Publisher --> TrainEvent
    Factory --> TrainEvent
    
    classDef component fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    
    class Context,Publisher,Factory,TrainEvent component
```

### Components

| Component | Responsibility |
|-----------|----------------|
| **ExternalTrainsContext** | Initialize train arrivals from scenario |
| **EventPublisher** | Publish TrainArrivedEvent to event bus |
| **WagonFactory** | Create wagon entities from train data |

### Train Arrival Flow

```mermaid
sequenceDiagram
    participant Scenario
    participant ExternalTrains
    participant EventBus
    participant RetrofitWorkflow
    
    Scenario->>ExternalTrains: Initialize with trains
    ExternalTrains->>ExternalTrains: Schedule arrivals
    loop For each train
        ExternalTrains->>EventBus: Publish TrainArrivedEvent
        EventBus->>RetrofitWorkflow: Deliver event
        RetrofitWorkflow->>RetrofitWorkflow: Process wagons
    end
```

---

## 5a.5 Integration Patterns

### Event Bus Communication

```python
from contexts.shared.domain.events import EventBus, TrainArrivedEvent

# External Trains publishes event
event_bus.publish(TrainArrivedEvent(
    train_id="T001",
    wagons=[wagon1, wagon2, wagon3],
    arrival_time=100.0
))

# Retrofit Workflow subscribes
event_bus.subscribe(TrainArrivedEvent, arrival_coordinator.handle_train_arrival)
```

### Track Capacity Queries

```python
from contexts.railway_infrastructure.application.railway_context import RailwayContext

# Query track capacity
railway = RailwayContext(scenario)
track = railway.track_selector.select_track_with_capacity('collection', required_length=50.0)

# Place wagons on track
railway.place_wagons_on_track(track.id, wagons)
```

### Resource Allocation

```python
from contexts.retrofit_workflow.infrastructure.resource_managers import LocomotiveResourceManager

# Allocate locomotive
loco_manager = LocomotiveResourceManager(env, locomotives)
locomotive = yield loco_manager.allocate()

# Use locomotive
yield from transport_wagons(locomotive, wagons, destination)

# Release locomotive
loco_manager.release(locomotive)
```

---

## 5a.6 File Organization

```
popupsim/backend/src/
├── main.py                                    # CLI entry point
├── application/
│   └── simulation_service.py                  # Orchestrates all contexts
├── contexts/
│   ├── configuration/                         # Configuration Context
│   │   ├── domain/
│   │   │   ├── configuration_builder.py       # Load from files
│   │   │   └── models/
│   │   │       ├── scenario.py
│   │   │       ├── process_times.py
│   │   │       └── ...
│   │   └── infrastructure/
│   │       └── file_loader.py                 # Parse JSON/CSV
│   ├── retrofit_workflow/                     # Retrofit Workflow Context
│   │   ├── application/
│   │   │   ├── retrofit_workflow_context.py   # Main context
│   │   │   └── coordinators/
│   │   │       ├── arrival_coordinator.py
│   │   │       ├── collection_coordinator.py
│   │   │       ├── workshop_coordinator.py
│   │   │       └── parking_coordinator.py
│   │   ├── domain/
│   │   │   └── services/
│   │   │       ├── batch_formation_service.py
│   │   │       ├── rake_formation_service.py
│   │   │       ├── train_formation_service.py
│   │   │       ├── workshop_scheduling_service.py
│   │   │       ├── coupling_service.py
│   │   │       └── route_service.py
│   │   └── infrastructure/
│   │       ├── resource_managers/
│   │       │   ├── locomotive_resource_manager.py
│   │       │   ├── track_capacity_manager.py
│   │       │   └── workshop_resource_manager.py
│   │       └── metrics/
│   │           ├── simulation_metrics.py
│   │           ├── wagon_collector.py
│   │           ├── locomotive_collector.py
│   │           └── workshop_collector.py
│   ├── railway_infrastructure/                # Railway Infrastructure Context
│   │   ├── application/
│   │   │   └── railway_context.py             # Track building & services
│   │   ├── domain/
│   │   │   ├── aggregates/
│   │   │   │   ├── track_group.py
│   │   │   │   ├── track.py
│   │   │   │   └── track_occupancy.py
│   │   │   └── services/
│   │   │       ├── track_selector.py
│   │   │       └── capacity_service.py
│   │   └── infrastructure/
│   │       └── track_repository.py
│   ├── external_trains/                       # External Trains Context
│   │   ├── application/
│   │   │   └── external_trains_context.py     # Train arrival management
│   │   ├── domain/
│   │   │   ├── wagon_factory.py
│   │   │   └── events/
│   │   │       └── train_arrived_event.py
│   │   └── infrastructure/
│   │       └── event_publisher.py
│   └── shared/                                # Shared Kernel
│       ├── domain/
│       │   ├── events/
│       │   │   └── event_bus.py
│       │   └── value_objects/
│       └── infrastructure/
│           └── simpy_adapter.py
└── tests/
    └── unit/
        ├── configuration/
        ├── retrofit_workflow/
        ├── railway_infrastructure/
        └── external_trains/
```

---

## 5a.7 Wagon State Machine

```mermaid
stateDiagram-v2
    [*] --> ARRIVING: Train arrives
    ARRIVING --> SELECTING: At hump
    SELECTING --> SELECTED: Needs retrofit + capacity available
    SELECTING --> REJECTED: No capacity
    SELECTED --> MOVING_TO_COLLECTION: Locomotive pickup
    MOVING_TO_COLLECTION --> ON_COLLECTION_TRACK: Delivered
    ON_COLLECTION_TRACK --> MOVING_TO_RETROFIT: Batch formed
    MOVING_TO_RETROFIT --> ON_RETROFIT_TRACK: At retrofit track
    ON_RETROFIT_TRACK --> MOVING_TO_WORKSHOP: Workshop ready
    MOVING_TO_WORKSHOP --> RETROFITTING: At station
    RETROFITTING --> RETROFITTED: Retrofit complete
    RETROFITTED --> MOVING_TO_RETROFITTED: Pickup batch
    MOVING_TO_RETROFITTED --> ON_RETROFITTED_TRACK: At retrofitted track
    ON_RETROFITTED_TRACK --> MOVING_TO_PARKING: To parking
    MOVING_TO_PARKING --> PARKING: At parking track
    REJECTED --> [*]
    PARKING --> [*]
```

---

## 5a.8 Technology Integration

### SimPy Integration

**SimPyAdapter** provides abstraction:
```python
class SimPyAdapter:
    def delay(self, duration: float) -> Generator
    def run_process(self, process: Callable, *args) -> None
    def create_store(self, capacity: int) -> Any
    def create_event(self) -> Any
    def current_time(self) -> float
    def run(self, until: float) -> None
```

### Pydantic Integration

All domain models use Pydantic for:
- Type safety
- Automatic validation
- JSON serialization
- Field constraints
- Custom validators

### Event Bus Integration

```python
from contexts.shared.domain.events import EventBus

# Initialize event bus
event_bus = EventBus()

# Subscribe to events
event_bus.subscribe(TrainArrivedEvent, handler)

# Publish events
event_bus.publish(TrainArrivedEvent(...))
```

---
