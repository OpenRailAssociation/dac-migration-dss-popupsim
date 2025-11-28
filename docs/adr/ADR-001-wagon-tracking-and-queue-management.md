# ADR-001: Wagon Tracking and Queue Management Architecture

## Status
**OPEN** - Under evaluation

## Context

PopUpSim currently has a fundamental issue with wagon tracking and queue management that causes wagons to be "lost" during the simulation workflow. The root cause is a dual-purpose `wagons_queue` that serves both as a processing queue and a global wagon registry, leading to data inconsistency.

### Current Problem
- **W07 stuck on retrofit track**: Wagons moved to retrofitted track are not added back to `wagons_queue`, making them invisible to `move_to_parking` process
- **Dual-purpose queue**: `popupsim.wagons_queue` used for both processing workflow and wagon tracking
- **Broken workflow chain**: Train → Collection → Retrofit → Workshop → Retrofitted → ❌ LOST → Parking
- **Data inconsistency**: Wagons removed from queue during processing but needed for later stages

### Current Architecture Issues
```python
# Problematic dual-purpose usage
self.wagons_queue: list[Wagon] = []  # Both processing queue AND global registry

# Broken lookup in move_to_parking
wagons_on_retrofitted = [
    w for w in popupsim.wagons_queue  # ❌ Wagons not in queue anymore!
    if w.track == retrofitted_track.id and w.status == WagonStatus.RETROFITTED
]
```

## Decision Options

### Option 1: Separation of Concerns - Registry + Queues

**Principle**: Single Responsibility - separate tracking from workflow coordination

```python
class WagonTracker:
    """Single responsibility: Track all wagons in system"""
    def __init__(self):
        self.registry: dict[str, Wagon] = {}  # Never remove wagons
    
    def get_wagons_by_track(self, track_id: str) -> list[Wagon]: ...
    def get_wagons_by_status(self, status: WagonStatus) -> list[Wagon]: ...

class WorkflowQueues:
    """Single responsibility: Manage processing workflows"""
    def __init__(self, sim):
        self.collection_queue: list[Wagon] = []
        self.retrofit_queue: list[Wagon] = []
        self.retrofitted_ready = sim.create_store()  # For move_to_parking
        self.parking_queue: list[Wagon] = []
```

**Pros:**
- Clear separation of concerns
- No data loss - registry never loses wagons
- Easy debugging - clear data ownership
- Solves W07 problem directly

**Cons:**
- More complexity - multiple data structures
- Need to maintain consistency across structures

### Option 2: Event-Driven State Machine

**Principle**: Reactive architecture with event-driven workflow coordination

```python
class WagonEventManager:
    def __init__(self, sim):
        self.wagon_states: dict[str, Wagon] = {}
        self.wagon_events: dict[WagonStatus, SimPy.Store] = {
            WagonStatus.RETROFITTED: sim.create_store(),
            WagonStatus.READY_FOR_PARKING: sim.create_store(),
        }
    
    def handle_wagon_retrofitted(self, wagon: Wagon) -> None:
        self.wagon_states[wagon.id] = wagon
        self.wagon_events[WagonStatus.RETROFITTED].put(wagon)
```

**Pros:**
- Reactive - no polling required
- Clear workflow triggers
- Natural event integration
- Scalable architecture

**Cons:**
- More complex event handling
- Still needs state storage for analytics
- Higher learning curve

### Option 3: Single Registry + Status-Based Queries

**Principle**: Single source of truth with query-based access

```python
class WagonRegistry:
    def __init__(self):
        self.all_wagons: dict[str, Wagon] = {}
    
    def get_wagons_by_status_and_track(self, status: WagonStatus, track_id: str) -> list[Wagon]:
        return [w for w in self.all_wagons.values() 
                if w.status == status and w.track == track_id]
```

**Pros:**
- Simple - single source of truth
- No data synchronization issues
- Easy to understand and maintain

**Cons:**
- O(n) queries - potential performance issues
- No workflow coordination mechanism
- Polling-based approach

### Option 4: Track-Based Wagon Management

**Principle**: Each track manages its own wagons

```python
class TrackBasedWagonManager:
    def __init__(self):
        self.track_wagons: dict[str, list[Wagon]] = {
            "collection": [],
            "retrofit": [],
            "retrofitted": [],
            "parking": []
        }
    
    def move_wagon(self, wagon: Wagon, from_track: str, to_track: str): ...
```

**Pros:**
- Natural organization by physical location
- Efficient lookups by track
- Mirrors real-world track organization

**Cons:**
- Need to maintain consistency across moves
- Complex cross-track operations
- Potential data duplication

### Option 5: Resource State Machines

**Principle**: Explicit state management with automatic transitions and side effects

```python
class WagonStateMachine:
    states = [
        'ARRIVING', 'SELECTING', 'ON_COLLECTION', 'MOVING_TO_RETROFIT',
        'ON_RETROFIT', 'RETROFITTING', 'RETROFITTED', 'MOVING_TO_PARKING', 'PARKING'
    ]
    
    def on_enter_RETROFITTED(self, wagon: Wagon):
        # Automatic queue management
        self.orchestrator.parking_queue.put(wagon)
        # Automatic event firing
        self.metrics.record_event(WagonRetrofittedEvent.create(wagon_id=wagon.id))
    
    def can_move_to_retrofit(self, wagon: Wagon) -> bool:
        return (self.workshop_capacity.has_available_stations() and
                self.track_capacity.can_add_wagon(wagon.length))
```

**Pros:**
- Explicit state management - no "lost" wagons
- Automatic queue coordination
- Built-in validation with guards
- Natural event integration
- Excellent debugging capabilities
- Prevents invalid state transitions

**Cons:**
- Added complexity and abstraction
- Learning curve for state machine concepts
- Potential over-engineering for simple workflows

## Analytics Considerations

All options must support analytics requirements:

```python
# Analytics needs access to:
wagon.retrofit_start_time    # When did retrofit begin?
wagon.retrofit_end_time      # When did it complete?  
wagon.waiting_time          # How long did wagon wait?
wagon.track                 # Where is wagon now?
wagon.status               # What state is it in?
```

**Analytics Compatibility:**
- **Option 1**: ✅ Complete state in registry
- **Option 2**: ⚠️ Needs separate state storage
- **Option 3**: ✅ Direct state access
- **Option 4**: ✅ State distributed across tracks
- **Option 5**: ✅ State in machines + automatic events

## Implementation Phases

### MVP Phase (Immediate)
**Goal**: Solve W07 problem with minimal changes
- **Recommended**: Option 1 (Registry + Queues) or Option 5 (Wagon State Machine)
- **Rationale**: Clear separation, solves immediate problem, foundation for future

### Post-MVP Phase (Enhanced)
**Goal**: Improved analytics and workflow coordination
- **Recommended**: Hybrid of Option 1 + Option 2 (Registry + Events)
- **Add**: Enhanced event projections, real-time analytics

### Full Version (Enterprise)
**Goal**: Scalable, enterprise-grade architecture
- **Recommended**: Event Sourcing + CQRS + State Machines
- **Features**: Time-travel debugging, what-if analysis, microservices ready

## Migration Strategy

```
Phase 1: MVP → Registry + Queues (solve W07)
Phase 2: Enhanced → Add event projections  
Phase 3: Full → Event sourcing + CQRS
Phase 4: Enterprise → Microservices + real-time analytics
```

## Open Questions

1. **Performance vs. Simplicity**: How important is O(1) lookup performance vs. code simplicity?
2. **State Machine Scope**: Should state machines apply to all resources or just critical ones (Wagon, Locomotive)?
3. **Event Integration**: How tightly should new architecture integrate with existing event system?
4. **Migration Path**: Should we implement incrementally or do a complete refactor?
5. **Testing Strategy**: How do we ensure no regressions during architecture changes?

## Next Steps

1. **Prototype Option 1** - Registry + Queues approach to solve W07
2. **Evaluate Option 5** - State machine for Wagon resource
3. **Performance testing** - Compare query performance across options
4. **Team discussion** - Gather input on complexity vs. benefits trade-offs
5. **Decision timeline** - Target decision by [DATE]

## References

- Current issue: W07 wagon stuck on retrofit track
- Existing events: `WagonDeliveredEvent`, `WagonRetrofittedEvent`
- Analytics requirements: KPI calculation, throughput metrics
- MVP constraints: Direct context calls, file-based configuration

---

**Authors**: Development Team  
**Date**: 2024-12-19  
**Review Date**: TBD