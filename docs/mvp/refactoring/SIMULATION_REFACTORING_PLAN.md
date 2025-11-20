# PopUpSim Simulation Refactoring Plan

**Document Version:** 1.0  
**Date:** 2024  
**Status:** Planning Phase  
**Priority:** High

## Executive Summary

This document outlines a step-by-step refactoring plan for the PopUpSim simulation engine. The current implementation has architectural issues affecting maintainability, testability, and correctness. This plan addresses 7 major improvement areas with 23 specific action items.

---

## Table of Contents

1. [Critical Bugs to Fix Immediately](#1-critical-bugs-to-fix-immediately)
2. [Type Safety Improvements](#2-type-safety-improvements)
3. [Resource Management Refactoring](#3-resource-management-refactoring)
4. [Code Duplication Elimination](#4-code-duplication-elimination)
5. [Event-Driven Architecture](#5-event-driven-architecture)
6. [Data Structure Optimization](#6-data-structure-optimization)
7. [Testing & Observability](#7-testing--observability)

---

## 1. Critical Bugs to Fix Immediately

**Priority:** CRITICAL  
**Estimated Effort:** 1 hour

### Issue 1.1: Truncated Code in move_to_parking

**File:** `popupsim/backend/src/simulation/popupsim.py:523`

**Problem:**
```python
loco.track_id = parking_tr  # INCOMPLETE - NameError at runtime
```

**Fix:**
```python
loco.track_id = parking_track_id
loco.record_status_change(popupsim.sim.current_time(), LocoStatus.PARKING)
popupsim.locomotives.release_locomotive(loco)
```

**Action:** Add missing lines to complete the function.

---

### Issue 1.2: Type Mismatch in current_time()

**File:** `popupsim/backend/src/simulation/sim_adapter.py:134`

**Problem:**
```python
def current_time(self) -> str:  # Returns str
    return f'{float(self._env.now):8.2f}'

# But used as float:
wagon.retrofit_start_time = popupsim.sim.current_time()  # Type error
```

**Fix:**
```python
def current_time(self) -> float:
    """Get current simulation time as float."""
    return float(self._env.now)
```

**Action:** Change return type from `str` to `float` and remove formatting.

---

## 2. Type Safety Improvements

**Priority:** HIGH  
**Estimated Effort:** 2 hours

### Issue 2.1: Missing Generator Type Hints

**Files:** All generator functions in `popupsim.py`

**Problem:**
```python
def process_train_arrivals(popupsim: PopupSim):  # Missing return type
    yield popupsim.sim.delay(...)
```

**Fix:**
```python
from collections.abc import Generator
from typing import Any

def process_train_arrivals(popupsim: PopupSim) -> Generator[Any, None, None]:
    """Generator function to simulate train arrivals."""
    yield popupsim.sim.delay(...)
```

**Action:** Add `Generator[Any, None, None]` return type to all generator functions:
- `process_train_arrivals`
- `pickup_wagons_to_retrofit`
- `process_retrofit_work`
- `complete_retrofit`
- `pickup_retrofitted_wagons`
- `move_to_parking`

---

### Issue 2.2: Inconsistent Optional Handling

**Files:** `popupsim.py`, `route_finder.py`

**Problem:**
```python
route = find_route(...)  # Returns Route | None
if route and route.duration:  # Checks both None and duration
    yield popupsim.sim.delay(route.duration)
```

**Fix:**
```python
route = find_route(scenario.routes, loco.track_id, target_track_id)
if route is None:
    logger.warning('No route from %s to %s', loco.track_id, target_track_id)
    # Handle missing route appropriately
elif route.duration and route.duration > 0:
    yield popupsim.sim.delay(route.duration)
```

**Action:** Add explicit None checks and error handling for missing routes.

---

## 3. Resource Management Refactoring

**Priority:** HIGH  
**Estimated Effort:** 8 hours

### Issue 3.1: Unused acquire() Method

**File:** `popupsim/backend/src/simulation/popupsim.py:35-40`

**Problem:**
```python
def acquire(self):  # Never called, returns generator
    def _acq():
        while len(self.available_locomotives) >= 1:  # Logic inverted!
            yield self.sim.delay(self.poll)
        locomotive = self.allocate_locomotive()
        self.occupied_locomotives[locomotive.id] = locomotive
    return _acq()
```

**Issues:**
- Method never used (all code calls `allocate_locomotive()`)
- Logic bug: loops while locomotives ARE available (should be `< 1`)
- Returns generator but not integrated with SimPy properly

**Fix Option A - Remove unused code:**
```python
# Delete acquire() method entirely
```

**Fix Option B - Use SimPy Resource properly:**
```python
class LocomotivePool:
    def __init__(self, sim: SimulationAdapter, locomotives: list[Locomotive]) -> None:
        self.sim = sim
        self.locomotives = {loco.locomotive_id: loco for loco in locomotives}
        # Use SimPy Resource for proper blocking
        self.resource = sim.create_resource(capacity=len(locomotives))
    
    def request(self) -> Generator[Any, None, Locomotive]:
        """Request a locomotive (blocks if none available)."""
        with self.resource.request() as req:
            yield req
            # Allocate first available locomotive
            loco_id = next(iter(self.locomotives.keys()))
            return self.locomotives.pop(loco_id)
    
    def release(self, locomotive: Locomotive) -> None:
        """Release locomotive back to pool."""
        self.locomotives[locomotive.locomotive_id] = locomotive
```

**Action:** Choose Option B - refactor to use SimPy Resource for proper blocking behavior.

---

### Issue 3.2: Polling Instead of Event-Driven

**Files:** All process functions in `popupsim.py`

**Problem:**
```python
while True:
    loco = popupsim.locomotives.allocate_locomotive()
    if not loco:
        yield popupsim.sim.delay(1.0)  # Wasteful polling
        continue
```

**Fix - Use SimPy Store:**
```python
# In PopupSim.__init__:
self.locomotive_store = simpy.Store(self.sim._env)
for loco in self.locomotives_queue:
    self.locomotive_store.put(loco)

# In process functions:
loco = yield self.locomotive_store.get()  # Blocks until available
# ... use locomotive ...
yield self.locomotive_store.put(loco)  # Return to pool
```

**Action:** Replace polling loops with SimPy Store/Resource primitives.

---

### Issue 3.3: Hardcoded Startup Delays

**Files:** `popupsim.py:428, 489`

**Problem:**
```python
def process_retrofit_work(popupsim: PopupSim):
    # No delay - starts immediately

def pickup_retrofitted_wagons(popupsim: PopupSim):
    yield popupsim.sim.delay(20.0)  # Magic number

def move_to_parking(popupsim: PopupSim):
    yield popupsim.sim.delay(60.0)  # Magic number
```

**Fix - Use Events:**
```python
# In PopupSim:
self.first_wagon_retrofitting = simpy.Event(self.sim._env)
self.first_wagon_retrofitted = simpy.Event(self.sim._env)

# In process_retrofit_work:
def process_retrofit_work(popupsim: PopupSim) -> Generator[Any, None, None]:
    while True:
        retrofitting_wagons = [...]
        if retrofitting_wagons:
            for wagon in retrofitting_wagons:
                wagon.retrofit_start_time = popupsim.sim.current_time()
                popupsim.first_wagon_retrofitting.succeed()  # Trigger event
                popupsim.sim.run_process(complete_retrofit, ...)
        yield popupsim.sim.delay(1.0)

# In pickup_retrofitted_wagons:
def pickup_retrofitted_wagons(popupsim: PopupSim) -> Generator[Any, None, None]:
    yield popupsim.first_wagon_retrofitting  # Wait for event
    logger.info('Starting retrofitted wagon pickup process')
    # ... rest of logic
```

**Action:** Replace hardcoded delays with event-driven coordination.

---

## 4. Code Duplication Elimination

**Priority:** MEDIUM  
**Estimated Effort:** 4 hours

### Issue 4.1: Locomotive Movement Pattern

**Files:** `popupsim.py` (repeated 10+ times)

**Problem:**
```python
# Pattern repeated everywhere:
loco.record_status_change(popupsim.sim.current_time(), LocoStatus.MOVING)
route = find_route(scenario.routes, loco.track_id, target_track_id)
if route and route.duration:
    logger.debug('Loco %s traveling to %s', loco.locomotive_id, target_track_id)
    yield popupsim.sim.delay(route.duration)
loco.track_id = target_track_id
```

**Fix - Extract Helper:**
```python
def move_locomotive(
    popupsim: PopupSim,
    loco: Locomotive,
    target_track_id: str
) -> Generator[Any, None, None]:
    """Move locomotive to target track."""
    if loco.track_id == target_track_id:
        return  # Already there
    
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.MOVING)
    route = find_route(popupsim.scenario.routes, loco.track_id, target_track_id)
    
    if route is None:
        logger.error('No route from %s to %s', loco.track_id, target_track_id)
        raise ValueError(f'No route from {loco.track_id} to {target_track_id}')
    
    if route.duration and route.duration > 0:
        logger.debug('Loco %s traveling from %s to %s (%.1f min)',
                    loco.locomotive_id, loco.track_id, target_track_id, route.duration)
        yield popupsim.sim.delay(route.duration)
    
    loco.track_id = target_track_id

# Usage:
yield from move_locomotive(popupsim, loco, collection_track_id)
```

**Action:** Create `move_locomotive()` helper and replace all duplicated movement code.

---

### Issue 4.2: Coupling/Decoupling Operations

**Files:** `popupsim.py` (repeated 6 times)

**Problem:**
```python
# Coupling pattern:
loco.record_status_change(popupsim.sim.current_time(), LocoStatus.COUPLING)
coupling_time = len(wagons) * process_times.wagon_coupling_time
logger.debug('Loco %s coupling %d wagons', loco.locomotive_id, len(wagons))
yield popupsim.sim.delay(coupling_time)

# Decoupling pattern:
loco.record_status_change(popupsim.sim.current_time(), LocoStatus.DECOUPLING)
decoupling_time = len(wagons) * process_times.wagon_decoupling_time
logger.debug('Loco %s decoupling %d wagons', loco.locomotive_id, len(wagons))
yield popupsim.sim.delay(decoupling_time)
```

**Fix - Extract Helpers:**
```python
def couple_wagons(
    popupsim: PopupSim,
    loco: Locomotive,
    wagons: list[Wagon]
) -> Generator[Any, None, None]:
    """Couple wagons to locomotive."""
    if not wagons:
        return
    
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.COUPLING)
    coupling_time = len(wagons) * popupsim.scenario.process_times.wagon_coupling_time
    logger.debug('Loco %s coupling %d wagons', loco.locomotive_id, len(wagons))
    yield popupsim.sim.delay(coupling_time)

def decouple_wagons(
    popupsim: PopupSim,
    loco: Locomotive,
    wagons: list[Wagon]
) -> Generator[Any, None, None]:
    """Decouple wagons from locomotive."""
    if not wagons:
        return
    
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.DECOUPLING)
    decoupling_time = len(wagons) * popupsim.scenario.process_times.wagon_decoupling_time
    logger.debug('Loco %s decoupling %d wagons', loco.locomotive_id, len(wagons))
    yield popupsim.sim.delay(decoupling_time)

# Usage:
yield from couple_wagons(popupsim, loco, wagons_to_pickup)
```

**Action:** Create coupling/decoupling helpers and replace all duplicated code.

---

### Issue 4.3: Track Finding Pattern

**Files:** `popupsim.py` (repeated 5 times)

**Problem:**
```python
parking_tracks = [t for t in scenario.tracks if t.type == TrackType.PARKING or t.type.value == 'resourceparking']
retrofitted_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFITTED]
```

**Fix - Cache in PopupSim:**
```python
class PopupSim:
    def __init__(self, sim: SimulationAdapter, scenario: Scenario) -> None:
        # ... existing init ...
        
        # Cache track lookups
        self.parking_tracks = [t for t in scenario.tracks 
                              if t.type == TrackType.PARKING or t.type.value == 'resourceparking']
        self.collection_tracks = [t for t in scenario.tracks if t.type == TrackType.COLLECTION]
        self.retrofit_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFIT]
        self.retrofitted_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFITTED]
        
        if not self.parking_tracks:
            raise ValueError('Scenario must have at least one parking track')
        if not self.retrofitted_tracks:
            raise ValueError('Scenario must have at least one retrofitted track')

# Usage:
parking_track_id = popupsim.parking_tracks[0].id
```

**Action:** Cache track lists in PopupSim initialization.

---

## 5. Event-Driven Architecture

**Priority:** MEDIUM  
**Estimated Effort:** 6 hours

### Issue 5.1: Replace Polling with Events

**Current Architecture:**
```
Process A: while True: check condition -> delay(1.0) -> repeat
Process B: while True: check condition -> delay(1.0) -> repeat
Process C: while True: check condition -> delay(1.0) -> repeat
```

**Problems:**
- Wastes simulation time checking conditions
- Fixed 1-minute granularity
- Processes can miss state changes between polls

**Target Architecture:**
```
Process A: wait for event -> process -> trigger next event
Process B: wait for event -> process -> trigger next event
Process C: wait for event -> process -> trigger next event
```

**Implementation:**
```python
class PopupSim:
    def __init__(self, sim: SimulationAdapter, scenario: Scenario) -> None:
        # ... existing init ...
        
        # Event coordination
        self.wagon_ready_for_pickup = simpy.Store(self.sim._env)
        self.wagon_ready_for_retrofit = simpy.Store(self.sim._env)
        self.wagon_retrofitted = simpy.Store(self.sim._env)
        self.wagon_ready_for_parking = simpy.Store(self.sim._env)

# In process_train_arrivals:
def process_train_arrivals(popupsim: PopupSim) -> Generator[Any, None, None]:
    for train in popupsim.scenario.trains:
        # ... process wagons ...
        if wagon.status == WagonStatus.SELECTED:
            yield popupsim.wagon_ready_for_pickup.put(wagon)  # Signal event

# In pickup_wagons_to_retrofit:
def pickup_wagons_to_retrofit(popupsim: PopupSim) -> Generator[Any, None, None]:
    while True:
        wagon = yield popupsim.wagon_ready_for_pickup.get()  # Wait for event
        # ... process wagon ...
        yield popupsim.wagon_ready_for_retrofit.put(wagon)  # Signal next stage
```

**Action:** Refactor all polling loops to use SimPy Store/Event primitives.

---

## 6. Data Structure Optimization

**Priority:** LOW  
**Estimated Effort:** 3 hours

### Issue 6.1: Inefficient Wagon Queue Searches

**File:** `popupsim.py`

**Problem:**
```python
# O(n) search repeated in every process:
retrofitting_wagons = [
    w for w in popupsim.wagons_queue  # Linear search
    if w.status == WagonStatus.RETROFITTING and not w.retrofit_start_time
]
```

**Fix - Index by Status:**
```python
class PopupSim:
    def __init__(self, sim: SimulationAdapter, scenario: Scenario) -> None:
        # ... existing init ...
        
        # Index wagons by status for O(1) lookup
        self.wagons_by_status: dict[WagonStatus, set[Wagon]] = {
            status: set() for status in WagonStatus
        }
    
    def update_wagon_status(self, wagon: Wagon, new_status: WagonStatus) -> None:
        """Update wagon status and maintain index."""
        if wagon.status in self.wagons_by_status:
            self.wagons_by_status[wagon.status].discard(wagon)
        wagon.status = new_status
        self.wagons_by_status[new_status].add(wagon)

# Usage:
retrofitting_wagons = [
    w for w in popupsim.wagons_by_status[WagonStatus.RETROFITTING]
    if not w.retrofit_start_time
]
```

**Action:** Add status indexing to avoid repeated linear searches.

---

## 7. Testing & Observability

**Priority:** MEDIUM  
**Estimated Effort:** 8 hours

### Issue 7.1: Untestable Generator Functions

**Problem:**
- Generator functions tightly coupled to PopupSim
- Hard to test individual operations
- No way to mock SimPy environment

**Fix - Extract Service Layer:**
```python
# New file: simulation/locomotive_service.py
class LocomotiveService:
    """Service for locomotive operations (testable without SimPy)."""
    
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
    
    def calculate_travel_time(self, from_track: str, to_track: str) -> float:
        """Calculate travel time between tracks."""
        route = find_route(self.scenario.routes, from_track, to_track)
        if route is None:
            raise ValueError(f'No route from {from_track} to {to_track}')
        return route.duration or 0.0
    
    def calculate_coupling_time(self, wagon_count: int) -> float:
        """Calculate time to couple wagons."""
        return wagon_count * self.scenario.process_times.wagon_coupling_time

# Test without SimPy:
def test_calculate_travel_time() -> None:
    scenario = create_test_scenario()
    service = LocomotiveService(scenario)
    travel_time = service.calculate_travel_time('track1', 'track2')
    assert travel_time == 5.0
```

**Action:** Extract business logic into testable service classes.

---

### Issue 7.2: Missing Metrics Collection

**Problem:**
- Only locomotive utilization tracked
- No throughput metrics
- No bottleneck identification

**Fix - Add Metrics Collector:**
```python
# New file: simulation/metrics.py
from dataclasses import dataclass, field

@dataclass
class SimulationMetrics:
    """Collect simulation metrics."""
    
    wagons_processed: int = 0
    wagons_rejected: int = 0
    total_waiting_time: float = 0.0
    total_retrofit_time: float = 0.0
    track_utilization: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    
    def record_wagon_completed(self, wagon: Wagon, sim_time: float) -> None:
        """Record wagon completion."""
        self.wagons_processed += 1
        if wagon.retrofit_start_time and wagon.retrofit_end_time:
            self.total_retrofit_time += wagon.retrofit_end_time - wagon.retrofit_start_time
    
    def get_average_waiting_time(self) -> float:
        """Calculate average waiting time."""
        if self.wagons_processed == 0:
            return 0.0
        return self.total_waiting_time / self.wagons_processed
    
    def get_throughput(self, total_time: float) -> float:
        """Calculate wagons per hour."""
        if total_time == 0:
            return 0.0
        return (self.wagons_processed / total_time) * 60.0

# In PopupSim:
class PopupSim:
    def __init__(self, sim: SimulationAdapter, scenario: Scenario) -> None:
        # ... existing init ...
        self.metrics = SimulationMetrics()
```

**Action:** Add comprehensive metrics collection throughout simulation.

---

### Issue 7.3: No Simulation Event Log

**Problem:**
- Hard to debug process interactions
- No audit trail of decisions
- Can't replay simulations

**Fix - Add Event Logger:**
```python
# New file: simulation/event_log.py
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    TRAIN_ARRIVED = "train_arrived"
    WAGON_SELECTED = "wagon_selected"
    WAGON_REJECTED = "wagon_rejected"
    LOCO_ALLOCATED = "loco_allocated"
    LOCO_RELEASED = "loco_released"
    WAGON_MOVED = "wagon_moved"
    RETROFIT_STARTED = "retrofit_started"
    RETROFIT_COMPLETED = "retrofit_completed"

@dataclass
class SimulationEvent:
    timestamp: float
    event_type: EventType
    entity_id: str
    details: dict[str, Any]

class EventLog:
    def __init__(self) -> None:
        self.events: list[SimulationEvent] = []
    
    def log(self, timestamp: float, event_type: EventType, 
            entity_id: str, **details: Any) -> None:
        """Log simulation event."""
        event = SimulationEvent(timestamp, event_type, entity_id, details)
        self.events.append(event)
    
    def export_to_csv(self, path: Path) -> None:
        """Export events to CSV for analysis."""
        # Implementation...

# Usage:
popupsim.event_log.log(
    popupsim.sim.current_time(),
    EventType.WAGON_SELECTED,
    wagon.wagon_id,
    track_id=collection_track_id,
    strategy=popupsim.scenario.track_selection_strategy
)
```

**Action:** Add event logging for debugging and analysis.

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] Fix truncated code in move_to_parking
- [ ] Fix current_time() return type
- [ ] Add type hints to all generator functions
- [ ] Add error handling for missing routes

### Phase 2: Resource Management (Week 2)
- [ ] Refactor LocomotivePool to use SimPy Resource
- [ ] Replace polling with event-driven coordination
- [ ] Remove hardcoded startup delays
- [ ] Add proper resource contention handling

### Phase 3: Code Quality (Week 3)
- [ ] Extract move_locomotive() helper
- [ ] Extract couple_wagons() and decouple_wagons() helpers
- [ ] Cache track lookups in PopupSim
- [ ] Add wagon status indexing

### Phase 4: Testing & Metrics (Week 4)
- [ ] Extract LocomotiveService for testability
- [ ] Add SimulationMetrics collector
- [ ] Add EventLog for debugging
- [ ] Write unit tests for service layer
- [ ] Write integration tests for processes

---

## Success Criteria

### Code Quality
- [ ] All functions have type hints
- [ ] MyPy passes with no errors
- [ ] Pylint score > 9.0
- [ ] No code duplication (DRY principle)

### Performance
- [ ] No polling loops (event-driven only)
- [ ] O(1) wagon status lookups
- [ ] Simulation runs 2x faster

### Testability
- [ ] 80%+ code coverage
- [ ] Business logic testable without SimPy
- [ ] Integration tests for all processes

### Observability
- [ ] Comprehensive metrics collection
- [ ] Event log for debugging
- [ ] Bottleneck identification

---

## Risk Assessment

### High Risk
- **Resource refactoring** - May break existing simulations
  - Mitigation: Keep old code, add feature flag
  
### Medium Risk
- **Event-driven architecture** - Complex coordination logic
  - Mitigation: Refactor one process at a time, test thoroughly

### Low Risk
- **Code duplication** - Straightforward extraction
- **Type hints** - No runtime impact

---

## Notes

- All changes must maintain backward compatibility with existing scenarios
- Run full test suite after each phase
- Update documentation as code changes
- Consider performance benchmarks before/after refactoring

---

**Document Owner:** Development Team  
**Review Date:** After each phase completion  
**Next Review:** After Phase 1 (Week 1)
