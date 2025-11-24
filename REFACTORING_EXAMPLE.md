# Separation of Concerns: Business Logic vs SimPy Coordination

## Problem: Mixed Concerns

Current code mixes business logic with SimPy coordination:

```python
def process_train_arrivals(popupsim: PopupSim) -> Generator[Any]:
    for train in scenario.trains:
        yield popupsim.sim.delay(...)  # SimPy coordination
        
        for wagon in train.wagons:
            wagon.status = WagonStatus.SELECTING  # Business logic
            if wagon.needs_retrofit and not wagon.is_loaded:  # Business logic
                collection_track_id = popupsim.track_capacity.select_collection_track(wagon.length)  # Business logic
                
                if collection_track_id:
                    popupsim.track_capacity.add_wagon(collection_track_id, wagon.length)  # Business logic
                    wagon.track_id = collection_track_id  # Business logic
                    wagon.status = WagonStatus.SELECTED  # Business logic
                    popupsim.wagons_queue.append(wagon)  # State management
                else:
                    wagon.status = WagonStatus.REJECTED  # Business logic
            
            yield popupsim.sim.delay(...)  # SimPy coordination
```

## Solution: Separate Layers

### Layer 1: Business Logic (Pure Functions)

```python
# wagon_operations.py - NO SimPy dependencies

class WagonStateManager:
    """Pure business logic for wagon state."""
    
    @staticmethod
    def start_movement(wagon: Wagon, from_track: str, to_track: str) -> None:
        wagon.status = WagonStatus.MOVING
        wagon.source_track_id = from_track
        wagon.destination_track_id = to_track
        wagon.track_id = None
    
    @staticmethod
    def select_for_retrofit(wagon: Wagon, track_id: str) -> None:
        wagon.track_id = track_id
        wagon.status = WagonStatus.SELECTED


class WagonSelector:
    """Business rules for wagon selection."""
    
    @staticmethod
    def needs_retrofit(wagon: Wagon) -> bool:
        return wagon.needs_retrofit and not wagon.is_loaded
```

### Layer 2: Coordination (SimPy Generators)

```python
# popupsim.py - SimPy coordination ONLY

def process_train_arrivals(popupsim: PopupSim) -> Generator[Any]:
    """Coordinate train arrival process using business logic."""
    wagon_selector = WagonSelector()
    wagon_state = WagonStateManager()
    
    for train in scenario.trains:
        # SimPy: Wait for train arrival
        yield popupsim.sim.delay((train.arrival_time - scenario.start_date).total_seconds() / 60.0)
        
        # SimPy: Delay to hump
        yield popupsim.sim.delay(process_times.train_to_hump_delay)
        
        # Process each wagon
        for wagon in train.wagons:
            # Business logic: Check if needs retrofit
            if wagon_selector.needs_retrofit(wagon):
                # Business logic: Select track
                collection_track_id = popupsim.track_capacity.select_collection_track(wagon.length)
                
                if collection_track_id:
                    # Business logic: Update state
                    popupsim.track_capacity.add_wagon(collection_track_id, wagon.length)
                    wagon_state.select_for_retrofit(wagon, collection_track_id)
                    popupsim.wagons_queue.append(wagon)
                else:
                    wagon_state.reject_wagon(wagon)
            else:
                wagon_state.reject_wagon(wagon)
            
            # SimPy: Delay between wagons
            yield popupsim.sim.delay(process_times.wagon_hump_interval)
        
        # SimPy: Signal completion
        popupsim.train_processed_event.trigger()
```

## Benefits

1. **Testability**: Business logic can be unit tested without SimPy
2. **Clarity**: Clear separation between "what" (business logic) and "when" (coordination)
3. **Reusability**: Business logic can be used outside simulation
4. **Maintainability**: Changes to business rules don't affect coordination

## Example Test

```python
def test_wagon_needs_retrofit():
    """Test business logic without SimPy."""
    wagon = Wagon(wagon_id="W1", needs_retrofit=True, is_loaded=False)
    assert WagonSelector.needs_retrofit(wagon) == True
    
    wagon.is_loaded = True
    assert WagonSelector.needs_retrofit(wagon) == False
```

## Recommendation

Create separate modules:
- `wagon_operations.py` - Wagon business logic
- `locomotive_operations.py` - Locomotive business logic  
- `capacity_operations.py` - Capacity management logic
- `popupsim.py` - SimPy coordination only

This follows the **Hexagonal Architecture** pattern where business logic is in the core and SimPy is an adapter.
