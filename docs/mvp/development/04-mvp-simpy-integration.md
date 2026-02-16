# 4. MVP SimPy Integration

## Overview

**Location:** `popupsim/backend/src/contexts/shared/infrastructure/simpy_adapter.py`

SimPy provides discrete event simulation for the Retrofit Workflow Context. Integration follows a thin adapter pattern to isolate SimPy dependencies.

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

## SimPy Adapter

**File:** `contexts/shared/infrastructure/simpy_adapter.py`

```python
import simpy
from typing import Any, Callable, Generator

class SimPyAdapter:
    """Thin adapter for SimPy environment."""
    
    def __init__(self, env: simpy.Environment):
        self.env = env
    
    @property
    def now(self) -> float:
        """Current simulation time."""
        return self.env.now
    
    def timeout(self, delay: float) -> Any:
        """Wait for delay time units."""
        return self.env.timeout(delay)
    
    def process(self, generator: Generator) -> Any:
        """Register a process."""
        return self.env.process(generator)
    
    def run(self, until: float | None = None) -> None:
        """Run simulation."""
        self.env.run(until=until)
    
    @staticmethod
    def create_environment() -> simpy.Environment:
        """Create SimPy environment."""
        return simpy.Environment()
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

**File:** `contexts/retrofit_workflow/infrastructure/resource_managers/locomotive_resource_manager.py`

```python
import simpy
from typing import Any

class LocomotiveResourceManager:
    """Manages locomotive resources."""
    
    def __init__(self, env: simpy.Environment, locomotives: list[Locomotive]):
        self.env = env
        self.resource = simpy.Resource(env, capacity=len(locomotives))
        self.locomotives = {loco.locomotive_id: loco for loco in locomotives}
    
    def allocate(self) -> Any:
        """Allocate locomotive (blocks until available)."""
        return self.resource.request()
    
    def release(self, request: Any) -> None:
        """Release locomotive."""
        self.resource.release(request)
```

## Event Bus Integration

External Trains Context publishes events via SimPy:

**File:** `contexts/external_trains/application/external_trains_context.py`

```python
def _arrival_process(self, train: Train, arrival_time: float) -> Generator[Any, Any, None]:
    """Process single train arrival."""
    yield self.env.timeout(arrival_time)
    
    # Publish event
    event = TrainArrivedEvent(
        train_id=train.id,
        wagons=train.wagons,
        arrival_time=self.env.now
    )
    self.event_bus.publish(event)
```

## Testing

### Unit Tests (No SimPy)

Domain services don't depend on SimPy:

```python
def test_batch_formation() -> None:
    """Test without SimPy."""
    service = BatchFormationService()
    wagons = [Wagon(...) for _ in range(5)]
    
    assert service.can_form_batch(wagons, min_size=1, max_size=10)
    batch = service.form_batch(wagons, batch_size=5)
    assert len(batch) == 5
```

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

### ✅ Do's
- Keep domain logic SimPy-free
- Use generators for coordinators
- Isolate SimPy in infrastructure layer
- Test domain logic without SimPy

### ❌ Don'ts
- Don't import SimPy in domain services
- Don't put business logic in generators
- Don't use global SimPy resources

---
