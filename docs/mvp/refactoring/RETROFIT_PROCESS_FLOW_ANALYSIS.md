# Retrofit Process Flow Analysis

**Issue:** Missing movement from retrofit track to retrofit stations  
**Date:** 2024  
**Priority:** HIGH

## Current Process Flow

### Step-by-Step Current Implementation

```
1. process_train_arrivals
   └─> Wagons placed on COLLECTION tracks (status: SELECTED)

2. pickup_wagons_to_retrofit
   ├─> Loco picks up wagons from COLLECTION track
   ├─> Loco travels to RETROFIT track
   ├─> Loco decouples wagons on RETROFIT track
   └─> Wagons immediately set to status: RETROFITTING
       └─> Workshop stations immediately occupied

3. process_retrofit_work
   └─> Monitors RETROFITTING wagons
       └─> Starts retrofit work (no movement involved)

4. pickup_retrofitted_wagons
   └─> Picks up completed wagons from RETROFIT track
```

## Problem Identified

**Line 408-418 in popupsim.py:**
```python
# Occupy retrofit stations and add to track
popupsim.workshop_capacity.occupy_stations(retrofit_track_id, len(wagons_to_deliver))
for wagon in wagons_to_deliver:
    popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
    wagon.track_id = retrofit_track_id
    wagon.source_track_id = None
    wagon.destination_track_id = None
    wagon.status = WagonStatus.RETROFITTING  # ← Immediate status change
    logger.info('Wagon %s moved to retrofit track %s (station occupied)', 
                wagon.wagon_id, retrofit_track_id)
```

**Issues:**
1. Wagons are placed on retrofit track AND stations are occupied simultaneously
2. No physical movement from track to station
3. No queuing mechanism if stations are busy
4. Stations occupied before wagon actually reaches them

## Real-World Retrofit Process

### Expected Physical Flow

```
COLLECTION TRACK
    ↓ (loco transport)
RETROFIT TRACK (waiting area)
    ↓ (internal movement/shunting)
RETROFIT STATION (actual work position)
    ↓ (retrofit work performed)
RETROFIT TRACK (completed wagons)
    ↓ (loco transport)
RETROFITTED TRACK
```

### Key Distinction

- **Retrofit Track** = Physical track where wagons wait/are stored
- **Retrofit Station** = Specific work position on that track where retrofit happens

## Proposed Solutions

### Option 1: Implicit Station Assignment (Current Approach - Simplified)

**Keep current flow but clarify semantics:**

```python
# When wagon arrives at retrofit track:
wagon.status = WagonStatus.WAITING_FOR_STATION  # New status
wagon.track_id = retrofit_track_id

# Separate process assigns to stations:
def assign_wagons_to_stations(popupsim: PopupSim):
    while True:
        waiting_wagons = [w for w in popupsim.wagons_queue 
                         if w.status == WagonStatus.WAITING_FOR_STATION]
        
        for wagon in waiting_wagons:
            track_id = wagon.track_id
            if popupsim.workshop_capacity.get_available_stations(track_id) > 0:
                popupsim.workshop_capacity.occupy_stations(track_id, 1)
                wagon.status = WagonStatus.RETROFITTING
                logger.info('Wagon %s assigned to station on %s', 
                           wagon.wagon_id, track_id)
        
        yield popupsim.sim.delay(0.5)  # Check frequently
```

**Pros:**
- Minimal code changes
- Separates track arrival from station assignment
- Allows queuing on track

**Cons:**
- No explicit movement time to station
- Still somewhat abstract

---

### Option 2: Explicit Station Movement (Realistic)

**Add explicit movement from track to station:**

```python
# In pickup_wagons_to_retrofit - only deliver to track:
for wagon in wagons_to_deliver:
    popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
    wagon.track_id = retrofit_track_id
    wagon.status = WagonStatus.ON_RETROFIT_TRACK  # New status
    logger.info('Wagon %s delivered to retrofit track %s', 
                wagon.wagon_id, retrofit_track_id)
    # NO station occupation here!

# New process: move_wagons_to_stations
def move_wagons_to_stations(popupsim: PopupSim):
    """Move wagons from retrofit track to available stations."""
    scenario = popupsim.scenario
    process_times = scenario.process_times
    
    logger.info('Starting wagon-to-station movement process')
    
    while True:
        # Find wagons waiting on retrofit tracks
        for retrofit_track_id in popupsim.workshop_capacity.workshops_by_track.keys():
            waiting_wagons = [
                w for w in popupsim.wagons_queue
                if w.track_id == retrofit_track_id 
                and w.status == WagonStatus.ON_RETROFIT_TRACK
            ]
            
            if not waiting_wagons:
                continue
            
            available_stations = popupsim.workshop_capacity.get_available_stations(
                retrofit_track_id
            )
            
            if available_stations > 0:
                wagon = waiting_wagons[0]  # FIFO
                
                # Simulate internal movement to station
                wagon.status = WagonStatus.MOVING_TO_STATION
                movement_time = process_times.wagon_to_station_time  # New config
                logger.debug('Moving wagon %s to station (%.1f min)', 
                            wagon.wagon_id, movement_time)
                yield popupsim.sim.delay(movement_time)
                
                # Occupy station and start retrofit
                popupsim.workshop_capacity.occupy_stations(retrofit_track_id, 1)
                wagon.status = WagonStatus.RETROFITTING
                logger.info('Wagon %s at station on %s', 
                           wagon.wagon_id, retrofit_track_id)
        
        yield popupsim.sim.delay(0.5)  # Check frequently
```

**Pros:**
- Realistic physical flow
- Explicit queuing on track
- Stations only occupied when wagon actually there
- Can add movement time

**Cons:**
- More complex
- Requires new WagonStatus values
- Requires new process_times configuration

---

### Option 3: Station-Based Architecture (Major Refactor)

**Model stations as SimPy Resources:**

```python
class WorkshopCapacityManager:
    def __init__(self, workshops: list[Workshop], sim: SimulationAdapter) -> None:
        self.workshops_by_track: dict[str, Workshop] = {}
        self.station_resources: dict[str, Any] = {}  # SimPy Resources
        
        for workshop in workshops:
            self.workshops_by_track[workshop.track_id] = workshop
            # Create SimPy Resource for stations
            self.station_resources[workshop.track_id] = sim.create_resource(
                capacity=workshop.retrofit_stations
            )
    
    def request_station(self, track_id: str):
        """Request a station (blocks if none available)."""
        return self.station_resources[track_id].request()
    
    def release_station(self, track_id: str, request):
        """Release a station."""
        return self.station_resources[track_id].release(request)

# In wagon processing:
def process_wagon_retrofit(popupsim: PopupSim, wagon: Wagon):
    """Process single wagon through retrofit."""
    retrofit_track_id = wagon.track_id
    
    # Wait for available station (blocks automatically)
    with popupsim.workshop_capacity.request_station(retrofit_track_id) as station:
        yield station  # Blocks until station available
        
        # Wagon now has station
        wagon.status = WagonStatus.RETROFITTING
        wagon.retrofit_start_time = popupsim.sim.current_time()
        logger.info('Wagon %s started retrofit at station', wagon.wagon_id)
        
        # Perform retrofit work
        yield popupsim.sim.delay(popupsim.scenario.process_times.wagon_retrofit_time)
        
        # Retrofit complete
        wagon.status = WagonStatus.RETROFITTED
        wagon.retrofit_end_time = popupsim.sim.current_time()
        logger.info('Wagon %s retrofit completed', wagon.wagon_id)
    
    # Station automatically released when exiting 'with' block
```

**Pros:**
- Proper SimPy resource management
- Automatic blocking/queuing
- Clean separation of concerns
- No polling needed

**Cons:**
- Major refactoring required
- Changes workshop_capacity API
- Requires understanding SimPy Resources

---

## Recommended Approach

### Phase 1: Quick Fix (Option 1)
**Effort:** 2 hours  
**Impact:** Low risk, clarifies current behavior

1. Add `WagonStatus.WAITING_FOR_STATION`
2. Create `assign_wagons_to_stations()` process
3. Separate track arrival from station assignment

### Phase 2: Realistic Flow (Option 2)
**Effort:** 4 hours  
**Impact:** Medium risk, more realistic simulation

1. Add `WagonStatus.ON_RETROFIT_TRACK` and `MOVING_TO_STATION`
2. Create `move_wagons_to_stations()` process
3. Add `wagon_to_station_time` to ProcessTimes
4. Update pickup_wagons_to_retrofit to not occupy stations

### Phase 3: Proper Architecture (Option 3)
**Effort:** 8 hours  
**Impact:** High risk, best long-term solution

1. Refactor WorkshopCapacityManager to use SimPy Resources
2. Create per-wagon retrofit process
3. Remove polling from process_retrofit_work
4. Update all station management code

---

## Implementation Plan

### Immediate Action (This Week)

**Add missing WagonStatus values:**
```python
# In models/wagon.py
class WagonStatus(Enum):
    PARKING = "parking"
    TO_BE_RETROFFITED = "to_be_retrofitted"
    SELECTING = "selecting"
    SELECTED = "selected"
    REJECTED = "rejected"
    MOVING = "moving"
    ON_RETROFIT_TRACK = "on_retrofit_track"  # NEW
    WAITING_FOR_STATION = "waiting_for_station"  # NEW
    MOVING_TO_STATION = "moving_to_station"  # NEW
    RETROFITTING = "retrofitting"
    RETROFITTED = "retrofitted"
    UNKNOWN = "unknown"
```

**Implement Option 1 (Quick Fix):**
1. Modify pickup_wagons_to_retrofit to set status to WAITING_FOR_STATION
2. Add assign_wagons_to_stations process
3. Update PopupSim.run() to start new process
4. Test with small scenario

### Next Sprint (Next Week)

**Implement Option 2 (Realistic Flow):**
1. Add wagon_to_station_time to ProcessTimes model
2. Implement move_wagons_to_stations process
3. Update configuration files with new timing
4. Test with medium scenario

### Future Refactoring (Month 2)

**Implement Option 3 (Proper Architecture):**
1. Study SimPy Resource patterns
2. Refactor WorkshopCapacityManager
3. Create per-wagon retrofit processes
4. Remove all polling loops
5. Comprehensive testing

---

## Testing Strategy

### Unit Tests
```python
def test_wagon_waits_for_station() -> None:
    """Wagon should wait on track if no stations available."""
    # Setup scenario with 1 station, 2 wagons
    # Assert second wagon waits until first completes

def test_station_released_after_retrofit() -> None:
    """Station should be available after wagon completes."""
    # Setup scenario with 1 station
    # Assert station count increases after completion

def test_fifo_station_assignment() -> None:
    """Wagons should be assigned to stations in FIFO order."""
    # Setup scenario with multiple waiting wagons
    # Assert first wagon gets first available station
```

### Integration Tests
```python
def test_full_retrofit_flow() -> None:
    """Test complete flow from collection to retrofitted."""
    # Run small scenario
    # Assert all wagons complete retrofit
    # Assert correct timing and sequencing
```

---

## Configuration Changes Required

### ProcessTimes Model
```python
# In models/process_times.py
class ProcessTimes(BaseModel):
    # ... existing fields ...
    wagon_to_station_time: float = Field(
        default=2.0,
        ge=0,
        description='Time to move wagon from track to station (minutes)'
    )
    station_preparation_time: float = Field(
        default=1.0,
        ge=0,
        description='Time to prepare station before retrofit (minutes)'
    )
```

---

## Success Criteria

- [ ] Wagons wait on retrofit track before station assignment
- [ ] Stations only occupied when wagon physically at station
- [ ] Clear separation between track capacity and station capacity
- [ ] FIFO queuing for station assignment
- [ ] Realistic timing for all movements
- [ ] No race conditions in station allocation
- [ ] Proper logging of all state transitions

---

## Related Issues

- See SIMULATION_REFACTORING_PLAN.md Section 3.2 (Polling vs Event-Driven)
- See SIMULATION_REFACTORING_PLAN.md Section 5.1 (Event-Driven Architecture)

---

**Document Owner:** Development Team  
**Next Review:** After Phase 1 implementation
