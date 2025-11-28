# ADR-003: Capacity Management Integration for SimPy Stores

## Status
Proposed

## Context

Currently we have dual capacity management systems:
- **TrackCapacityManager**: Length-based physical capacity (75m track, wagons 10-20m each)
- **SimPy Stores**: Count-based workflow coordination (unlimited capacity)

This creates potential inconsistencies where SimPy stores could accept wagons that exceed physical track capacity.

### Current Implementation
```python
# Physical capacity (correct)
if track_capacity.can_add_wagon("retrofitted", wagon.length):
    track_capacity.add_wagon("retrofitted", wagon.length)

# Workflow coordination (separate)
yield retrofitted_wagons_ready.put(wagon)
```

### Problem
No automatic validation between physical capacity and SimPy workflow stores.

## Decision Options

### Option A: SimPy Store with Capacity Validation

**Approach**: Add validation wrapper around existing SimPy stores

```python
def put_wagon_if_fits(self, store_name: str, track_id: str, wagon: Wagon) -> Generator:
    """Put wagon in store only if track has physical capacity."""
    if self.track_capacity.can_add_wagon(track_id, wagon.length):
        self.track_capacity.add_wagon(track_id, wagon.length)
        yield getattr(self, store_name).put(wagon)
        return True
    # Handle capacity exceeded (wait/reject)
    return False
```

**Pros:**
- ✅ Minimal code changes
- ✅ Reuses existing TrackCapacityManager
- ✅ Maintains current SimPy store behavior
- ✅ Easy to implement incrementally

**Cons:**
- ⚠️ Manual validation required at each put()
- ⚠️ Easy to forget validation in new code
- ⚠️ Dual responsibility (capacity + workflow)

### Option B: Custom Length-Aware Store

**Approach**: Create domain-specific store that encapsulates both concerns

```python
class LengthAwareStore:
    def __init__(self, sim: SimulationAdapter, track_capacity: TrackCapacityManager, track_id: str):
        self._store = sim.create_store()
        self._capacity = track_capacity
        self._track_id = track_id
    
    def put(self, wagon: Wagon) -> Generator:
        if not self._capacity.can_add_wagon(self._track_id, wagon.length):
            raise CapacityExceededError(f"Track {self._track_id} full")
        self._capacity.add_wagon(self._track_id, wagon.length)
        return self._store.put(wagon)
    
    def get(self) -> Generator:
        wagon = yield self._store.get()
        self._capacity.remove_wagon(self._track_id, wagon.length)
        return wagon
```

**Pros:**
- ✅ Automatic capacity validation
- ✅ Single responsibility per store
- ✅ Type-safe domain modeling
- ✅ Impossible to forget validation

**Cons:**
- ⚠️ More complex implementation
- ⚠️ New abstraction to maintain
- ⚠️ Requires refactoring existing code

## Analysis

### Implementation Effort
- **Option A**: Low (wrapper functions)
- **Option B**: Medium (new class + refactoring)

### Maintainability
- **Option A**: Manual validation prone to errors
- **Option B**: Automatic validation, harder to misuse

### Domain Alignment
- **Option A**: Procedural approach
- **Option B**: Object-oriented domain modeling

### Risk Assessment
- **Option A**: Risk of missing validation calls
- **Option B**: Risk of over-engineering

## Recommendation

**Option A (SimPy Store with Capacity Validation)** for the following reasons:

1. **Pragmatic**: Solves the immediate problem with minimal changes
2. **Incremental**: Can be implemented store-by-store
3. **Familiar**: Uses existing patterns and components
4. **Testable**: Easy to verify validation behavior

### Implementation Strategy
1. Create validation helper functions
2. Update `move_to_parking` first (highest risk area)
3. Add validation to other store operations incrementally
4. Consider Option B if validation becomes too complex

## Consequences

### Positive
- Quick resolution of capacity inconsistency issue
- Maintains existing SimPy integration patterns
- Low risk of breaking current functionality

### Negative
- Requires discipline to use validation consistently
- Manual process prone to human error
- May need refactoring to Option B later if complexity grows

## Implementation Notes

Priority order for validation:
1. `retrofitted_wagons_ready` store (W07 fix area)
2. `wagons_ready_for_stations` stores
3. `wagons_completed` stores (workshop capacity managed separately)