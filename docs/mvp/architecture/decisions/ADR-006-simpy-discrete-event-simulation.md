# ADR-006: SimPy for Discrete Event Simulation

**Status:** IMPLEMENTED - 2025-01-15

## Context

Need a discrete event simulation framework for modeling Pop-Up workshop operations with individual wagon tracking and resource management.

## Decision

Use **SimPy** as the simulation engine.

## Rationale

- **Proven in POC**: Successfully validated during 3-Länderhack 2024 hackathon
- **Python native**: Integrates seamlessly with Python ecosystem
- **Discrete event paradigm**: Perfect fit for workshop operations simulation
- **Deterministic**: Supports reproducible results
- **Well-documented**: Mature library with good community support
- **Lightweight**: No heavy infrastructure requirements

## Alternatives Considered

- **SimPy** ✅ Chosen
- **Mesa**: Agent-based, overkill for our use case
- **Custom simulation**: Too much development effort
- **AnyLogic**: Commercial, not open source

## Implementation in MVP

### Core SimPy Usage
```python
# workshop_operations/infrastructure/simulation/simpy_adapter.py
class SimulationAdapter:
    def __init__(self):
        self.env = simpy.Environment()
    
    def create_resource(self, capacity: int) -> simpy.Resource:
        return simpy.Resource(self.env, capacity)
    
    def create_store(self, capacity: int = float('inf')) -> simpy.Store:
        return simpy.Store(self.env, capacity)

# workshop_operations/application/orchestrator.py
class WorkshopOrchestrator:
    def run(self, until: float) -> None:
        self.sim.run_process(process_train_arrivals, self)
        self.sim.run_process(pickup_wagons_to_retrofit, self)
        self.sim.run_process(move_wagons_to_stations, self)
        self.sim.run(until)
```

### SimPy Resources and Stores
- **Workshop Stations**: `simpy.Resource` for retrofit station capacity
- **Locomotive Pool**: `simpy.Store` for locomotive availability
- **Workflow Coordination**: `simpy.Store` for wagon flow between processes
- **Event Scheduling**: `simpy.Environment` for deterministic time progression

## Consequences

### Achieved
- ✅ **Deterministic Results**: Reproducible simulation runs with same seed
- ✅ **Resource Management**: SimPy Resources handle workshop station blocking
- ✅ **Event-Driven Workflow**: SimPy Stores eliminate polling delays
- ✅ **Process Coordination**: 5 concurrent processes coordinate via SimPy primitives
- ✅ **Abstraction Layer**: SimulationAdapter isolates SimPy dependencies

### Files Implementing This Decision
- `workshop_operations/infrastructure/simulation/simpy_adapter.py` - SimPy abstraction
- `workshop_operations/application/orchestrator.py` - Main simulation orchestration
- `workshop_operations/infrastructure/resources/` - Resource management with SimPy