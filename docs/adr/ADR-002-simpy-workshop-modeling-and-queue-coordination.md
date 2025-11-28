# ADR-002: SimPy Workshop Modeling and Queue Coordination

## Status
**OPEN** - Under evaluation

## Context

PopUpSim currently has a hybrid approach to SimPy usage - some components use SimPy resources and stores effectively, while others rely on manual queue management and polling. This inconsistency has led to the W07 wagon tracking issue and creates opportunities for better SimPy integration.

### Current SimPy Usage Analysis

**✅ Already Using SimPy Well:**
```python
# Workshop stations as SimPy Resources
self.resources[track_id] = sim.create_resource(capacity=workshop.retrofit_stations)

# Workflow coordination with SimPy Stores
self.wagons_ready_for_stations[track_id] = sim.create_store(capacity=1000)
self.wagons_completed[track_id] = sim.create_store(capacity=1000)

# Proper resource blocking in process_single_wagon
with workshop_resource.request() as station_req:
    yield station_req  # Blocks until station available
```

**❌ Missing SimPy Opportunities:**
```python
# W07 problem: No SimPy Store for retrofitted wagons
# move_to_parking searches wagons_queue instead of using SimPy coordination
wagons_on_retrofitted = [
    w for w in popupsim.wagons_queue  # Manual search + polling
    if w.track == retrofitted_track.id and w.status == WagonStatus.RETROFITTED
]

# Polling-based approach instead of event-driven
if not wagons_on_retrofitted:
    yield popupsim.sim.delay(1.0)  # Inefficient polling
    continue
```

### Root Cause
The fundamental issue is **incomplete SimPy workflow coordination**. We have SimPy stores for some workflow stages but not others, creating gaps where manual queue management and polling are required.

## Decision Options

### Option 1: Minimal SimPy Store Fix

**Principle**: Add missing SimPy store to complete the workflow chain

```python
class WorkshopOrchestrator:
    def __init__(self, sim, scenario):
        # Add missing store for retrofitted wagons
        self.retrofitted_wagons_ready = sim.create_store(capacity=1000)

# In _pickup_track_batches - after moving to retrofitted track:
for wagon in batch:
    popupsim.track_capacity.add_wagon(retrofitted_track.id, wagon.length)
    popupsim.wagon_state.complete_arrival(wagon, retrofitted_track.id, WagonStatus.RETROFITTED)
    # ✅ Add to SimPy store for move_to_parking
    yield popupsim.retrofitted_wagons_ready.put(wagon)

# In move_to_parking - use SimPy store instead of searching wagons_queue:
def move_to_parking(popupsim: WorkshopOrchestrator) -> Generator[Any]:
    while True:
        # ✅ Block until wagons available (no polling!)
        wagon = yield popupsim.retrofitted_wagons_ready.get()
        # Process wagon for parking...
```

**Pros:**
- Solves W07 problem immediately (5 lines of code)
- No polling - event-driven coordination
- Consistent with existing SimPy usage
- Minimal risk - small, focused change

**Cons:**
- Doesn't address broader architectural issues
- Still maintains dual-purpose wagons_queue
- Partial solution to larger problem

### Option 2: Complete SimPy Workflow Stores

**Principle**: Replace wagons_queue with stage-specific SimPy stores throughout

```python
class SimPyWorkshopFlow:
    def __init__(self, sim):
        # Stage-specific stores (replaces dual-purpose wagons_queue)
        self.collection_ready = sim.create_store(capacity=100)
        self.retrofit_ready = sim.create_store(capacity=100)
        self.workshop_input = sim.create_store(capacity=100)
        self.workshop_output = sim.create_store(capacity=100)
        self.retrofitted_ready = sim.create_store(capacity=100)  # Solves W07
        self.parking_ready = sim.create_store(capacity=100)

# Natural workflow chain:
# Train → collection_ready → retrofit_ready → workshop_input → 
# workshop_output → retrofitted_ready → parking_ready
```

**Pros:**
- Complete SimPy integration - no manual queue management
- Event-driven throughout - no polling anywhere
- Natural workflow modeling
- Automatic capacity management
- Solves W07 and prevents similar issues

**Cons:**
- Larger refactor - affects multiple components
- Need to migrate existing wagons_queue usage
- More complex migration path

### Option 3: SimPy Workshop Entity Model

**Principle**: Model workshop as complete SimPy entity with input/output queues

```python
class SimPyWorkshop:
    """Model entire workshop workflow with SimPy primitives"""
    def __init__(self, sim, workshop_config):
        # Input queue (wagons waiting for retrofit)
        self.input_queue = sim.create_store(capacity=workshop_config.max_input)
        
        # Processing stations (SimPy Resources)
        self.stations = sim.create_resource(capacity=workshop_config.retrofit_stations)
        
        # Output queue (retrofitted wagons ready for pickup)
        self.output_queue = sim.create_store(capacity=workshop_config.max_output)
        
        # Start continuous workshop process
        sim.run_process(self._workshop_process)
    
    def _workshop_process(self) -> Generator:
        """Continuous workshop processing"""
        while True:
            # Get wagon from input
            wagon = yield self.input_queue.get()
            
            # Request station
            with self.stations.request() as station:
                yield station
                # Process wagon
                yield self.sim.delay(self.retrofit_time)
                wagon.status = WagonStatus.RETROFITTED
                
            # Send to output
            yield self.output_queue.put(wagon)

# Usage:
workshop = SimPyWorkshop(sim, workshop_config)
yield workshop.input_queue.put(wagon)  # Send wagon to workshop
retrofitted_wagon = yield workshop.output_queue.get()  # Get completed wagon
```

**Pros:**
- Most natural SimPy modeling approach
- Encapsulates workshop behavior completely
- Automatic internal workflow management
- Easy to test and reason about
- Scales to complex workshop configurations

**Cons:**
- Significant architectural change
- Need to redesign workshop interactions
- Higher complexity for simple scenarios

### Option 4: Hybrid SimPy + Manual Approach

**Principle**: Use SimPy where it adds value, manual management where simpler

```python
# SimPy for resource contention and blocking
workshop_resource = sim.create_resource(capacity=stations)
with workshop_resource.request() as req:
    yield req

# SimPy for workflow coordination
retrofitted_ready = sim.create_store()
yield retrofitted_ready.put(wagon)

# Manual for simple state tracking
wagon_registry: dict[str, Wagon] = {}  # Simple lookup
```

**Pros:**
- Pragmatic approach - best tool for each job
- Leverages SimPy strengths without over-engineering
- Easier migration path
- Maintains flexibility

**Cons:**
- Mixed paradigms - less consistent
- Need to decide SimPy vs manual for each case
- Potential for inconsistencies

## Current SimPy Infrastructure Assessment

**Existing SimPy Components:**
- ✅ `SimulationAdapter` - Good abstraction over SimPy
- ✅ `ResourcePool` - Uses SimPy Store for locomotive management
- ✅ `WorkshopCapacityManager` - Uses SimPy Resources for stations
- ✅ Workflow stores - `wagons_ready_for_stations`, `wagons_completed`

**Missing SimPy Components:**
- ❌ Store for retrofitted wagons (causes W07 problem)
- ❌ Consistent store-based workflow throughout
- ❌ SimPy-based track capacity coordination

## Performance Considerations

**SimPy Store Benefits:**
- O(1) put/get operations
- Automatic blocking/unblocking
- Built-in capacity management
- No polling overhead

**Manual Queue Drawbacks:**
- O(n) search operations (`wagons_queue` filtering)
- Polling delays (1.0 second intervals)
- Manual capacity tracking
- Race condition potential

## Integration with Existing Events

All options must maintain compatibility with existing event system:
```python
# Events still fired regardless of queue mechanism
event = WagonRetrofittedEvent.create(wagon_id=wagon.id)
popupsim.metrics.record_event(event)
```

## Migration Strategies

### Strategy A: Incremental SimPy Enhancement
1. **Phase 1**: Add `retrofitted_wagons_ready` store (solve W07)
2. **Phase 2**: Replace remaining manual queues with SimPy stores
3. **Phase 3**: Evaluate full SimPy workshop modeling

### Strategy B: Complete SimPy Refactor
1. **Phase 1**: Design complete SimPy workflow architecture
2. **Phase 2**: Implement new SimPy-based components
3. **Phase 3**: Migrate existing code to new architecture

### Strategy C: Hybrid Approach
1. **Phase 1**: Add SimPy stores where they solve specific problems
2. **Phase 2**: Keep manual management where it's simpler
3. **Phase 3**: Optimize based on performance and maintainability

## Open Questions

1. **Scope**: Should we fix just W07 or redesign the entire workflow coordination?
2. **Performance**: How important is eliminating polling vs. code simplicity?
3. **SimPy Modeling**: Should workshops be modeled as complete SimPy entities?
4. **Migration Risk**: What's the acceptable risk level for workflow changes?
5. **Testing**: How do we ensure no regressions during SimPy migration?
6. **Capacity Management**: Should track capacity also use SimPy resources?

## Recommendations

### For Immediate W07 Fix
**Option 1** (Minimal SimPy Store Fix) - Low risk, immediate solution

### For Long-term Architecture
**Option 2** (Complete SimPy Workflow Stores) - Better architectural consistency

### For Advanced Modeling
**Option 3** (SimPy Workshop Entity Model) - Most natural SimPy approach

## Next Steps

1. **Prototype Option 1** - Minimal fix to validate approach
2. **Performance testing** - Compare polling vs. SimPy store performance
3. **Architecture review** - Evaluate long-term SimPy integration strategy
4. **Team discussion** - Gather input on SimPy modeling preferences
5. **Decision timeline** - Target decision by [DATE]

## References

- Current W07 issue: Wagon stuck on retrofit track due to missing SimPy store
- Existing SimPy usage: `WorkshopCapacityManager`, `ResourcePool`, workflow stores
- SimPy documentation: Resources, Stores, and Process coordination
- Related: ADR-001 (Wagon Tracking and Queue Management Architecture)

---

**Authors**: Development Team  
**Date**: 2024-12-19  
**Review Date**: TBD