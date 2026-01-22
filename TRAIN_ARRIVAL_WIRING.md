# Wiring Train Arrivals to Retrofit Context

## Current State

The test manually adds wagons to `collection_queue`:
```python
# From test
wagon = Wagon(id=f'W{i+1:02d}', length=15.0, ...)
wagon.classify()
wagon.move_to('collection')
context.collection_queue.put(wagon)
```

## What We Need

Add event handler to `RetrofitWorkshopContext` that:
1. Subscribes to `TrainArrivedEvent` from External Trains Context
2. Converts external wagon format to retrofit wagon format
3. Puts wagons into `collection_queue`

## Minimal Implementation

Add to `RetrofitWorkshopContext`:

```python
def subscribe_to_train_arrivals(self, event_bus: Any) -> None:
    """Subscribe to train arrival events from External Trains Context."""
    from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent
    event_bus.subscribe(TrainArrivedEvent, self._handle_train_arrived)

def _handle_train_arrived(self, event: Any) -> None:
    """Handle train arrived event - add wagons to collection queue."""
    from contexts.retrofit_workflow.domain.entities.wagon import Wagon
    from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler, CouplerType
    
    # Convert each wagon from external format to retrofit format
    for ext_wagon in event.wagons:
        # Create retrofit wagon
        wagon = Wagon(
            id=ext_wagon.id,
            length=ext_wagon.length,
            coupler_a=Coupler(CouplerType.SCREW, 'A'),
            coupler_b=Coupler(CouplerType.SCREW, 'B'),
        )
        
        # Set wagon state (like in test)
        wagon.classify()
        wagon.move_to('collection')
        
        # Add to collection queue
        self.collection_queue.put(wagon)
```

## That's It!

This is the ONLY code needed to wire train arrivals. The coordinators already:
- Monitor `collection_queue` (CollectionCoordinator)
- Process wagons through retrofit
- Move to parking

## Integration in simulation_service.py

```python
def _initialize_retrofit_workflow(self) -> None:
    """Initialize retrofit workflow."""
    from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
    
    # Create and initialize
    retrofit_context = RetrofitWorkshopContext(self.engine.env, self.scenario)
    retrofit_context.initialize()
    
    # Wire to train arrivals
    retrofit_context.subscribe_to_train_arrivals(self.infra.event_bus)
    
    # Store context
    self.contexts['retrofit_workflow'] = retrofit_context
```

Done! External Trains publishes `TrainArrivedEvent` → Retrofit context receives it → Wagons added to queue → Coordinators process them.
