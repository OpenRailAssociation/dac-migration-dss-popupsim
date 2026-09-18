# 4. MVP SimPy Integration

## Overview

**Location:** `popupsim/backend/src/shared/infrastructure/simulation/engines/simpy_adapter.py`

SimPy provides discrete event simulation for the Retrofit Workflow Context. Integration
follows a port/adapter pattern (`SimulationEnginePort` + `SimPyEngineAdapter`) to isolate
SimPy dependencies.

## Architecture

```
┌─────────────────────────────────────────┐
│   Retrofit Workflow Context            │
│   - Coordinators (Application)         │
│   - Domain Services (No SimPy)         │
└─────────────────┬───────────────────────┘
                  │
                  │ Uses
                  │
┌─────────────────▼───────────────────────┐
│   SimPy Adapter (Shared/Infrastructure) │
│   - Environment wrapper                 │
│   - Process management                  │
└─────────────────┬───────────────────────┘
                  │
                  │
┌─────────────────▼───────────────────────┐
│   SimPy Framework                       │
│   - Environment, Resource, Process      │
└─────────────────────────────────────────┘
```

## SimPy Engine Adapter

**File:** `shared/infrastructure/simulation/engines/simpy_adapter.py`

`SimPyEngineAdapter` implements `SimulationEnginePort` and wraps a `simpy.Environment`:

```python
import simpy
from collections.abc import Callable, Generator
from datetime import timedelta
from typing import Any


class SimPyEngineAdapter(SimulationEnginePort):
    """Adapter for the SimPy simulation environment."""

    @classmethod
    def create(cls) -> 'SimPyEngineAdapter':
        """Create an adapter with a fresh SimPy environment."""
        return cls(simpy.Environment())

    def current_time(self) -> float:
        """Current simulation time."""
        ...

    def delay(self, duration: float | timedelta) -> Generator[Any]:
        """Wait for the given duration (env.timeout)."""
        ...

    def schedule_process(self, process: Generator[Any] | Callable) -> Any:
        """Register a process (env.process)."""
        ...

    def create_resource(self, capacity: int, name: str | None = None) -> simpy.Resource: ...
    def create_store(self, capacity: int | None = None, name: str | None = None) -> Any: ...
    def create_event(self) -> Any: ...

    def run(self, until: float | None = None) -> None:
        """Run the simulation (env.run)."""
        ...
```

## Coordinator Pattern

Coordinators use SimPy generators for discrete event simulation:

**File:** `contexts/retrofit_workflow/application/coordinators/collection_coordinator.py`

```python
from typing import Generator, Any


class CollectionCoordinator:
    """Coordinates wagon collection."""

    def start(self) -> None:
        """Start coordinator process."""
        self.config.env.process(self._collection_process())

    def _collection_process(self) -> Generator[Any, Any, None]:
        """Main collection loop."""
        while True:
            # Wait for wagon
            wagon = yield self.config.collection_queue.get()

            # Collect batch
            wagons = yield from self._collect_batch(wagon)

            # Transport
            yield from self._transport_batch(wagons)
```

## Resource Management

SimPy Resources manage limited capacity:

**File:** `contexts/retrofit_workflow/infrastructure/resources/locomotive_resource_manager.py`

The `LocomotiveResourceManager` uses SimPy to model the limited locomotive pool and hands out
locomotives to the coordinators. Locomotives are keyed by their `id`. See the file for the
exact API.

## Event Bus Integration

External Trains Context publishes events via SimPy:

**File:** `contexts/external_trains/application/external_trains_context.py`

`start_processes()` schedules one SimPy process per train (via
`infra.engine.schedule_process(...)`). Each process waits until the train's arrival time,
creates the wagon entities, and publishes a `TrainArrivedEvent` onto the event bus:

```python
def _process_single_train_arrival(self, train: Any) -> Any:
    """Process a single train arrival."""
    arrival_delay = datetime_to_ticks(train.arrival_time, self.scenario.start_date)
    yield from self.infra.engine.delay(arrival_delay)

    # ... create wagons ...
    event = TrainArrivedEvent(train_id=train.train_id, wagons=train_wagons, ...)
    self.event_bus.publish(event)
```

## Testing

### Unit Tests (No SimPy)

Domain services don't depend on SimPy, so they can be tested with plain objects:

```python
def test_batch_formation() -> None:
    """Test a domain service without SimPy."""
    service = BatchFormationService()
    wagons = [Wagon(...) for _ in range(5)]

    batch = service.form_batch_for_workshop(wagons, ...)
    assert len(batch.wagon_ids) == 5
```

See `popupsim/backend/tests/unit/contexts/retrofit_workflow/domain/` for the real tests and
exact service signatures.

### Integration Tests (With SimPy)

```python
def test_collection_coordinator() -> None:
    """Test with SimPy."""
    env = simpy.Environment()
    queue = simpy.Store(env)
    
    coordinator = CollectionCoordinator(...)
    coordinator.start()
    
    # Add wagon
    queue.put(Wagon(...))
    
    # Run simulation
    env.run(until=100)
    
    # Verify wagon processed
    assert len(coordinator.processed_wagons) == 1
```

## Best Practices

### Do's
- Keep domain logic SimPy-free
- Use generators for coordinators
- Isolate SimPy in infrastructure layer
- Test domain logic without SimPy

### Don'ts
- Don't import SimPy in domain services
- Don't put business logic in generators
- Don't use global SimPy resources

---
