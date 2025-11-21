# Timeline Validator Usage Guide

The timeline validator allows you to define expected locomotive state transitions in a simple, declarative format.

## Basic Usage

```python
from .timeline_validator import validate_loco_timeline

def test_my_scenario():
    # ... run simulation ...
    loco = popup_sim.locomotives_queue[0]
    
    # Validate locomotive timeline
    validate_loco_timeline(loco, """
        t=0: PARKING Initial state
        t=0: MOVING parking→collection
        t=1: COUPLING at collection
        t=1: MOVING collection→retrofit
        t=2: DECOUPLING at retrofit
        t=2: MOVING retrofit→parking
        t=3: PARKING back at parking
    """)
```

## Timeline Format

Each line specifies one state transition:

```
t=TIME: STATUS description
```

- **TIME**: Simulation time (float, e.g., `0`, `1.5`, `15.0`)
- **STATUS**: Locomotive status (PARKING, MOVING, COUPLING, DECOUPLING)
- **description**: Human-readable description (optional, for documentation)

## Available Statuses

- `PARKING` - Locomotive at parking track
- `MOVING` - Locomotive traveling between tracks
- `COUPLING` - Locomotive coupling wagons
- `DECOUPLING` - Locomotive decoupling wagons

## Benefits

1. **Readable**: Timeline is self-documenting
2. **Maintainable**: Easy to update when process changes
3. **Concise**: Replaces 15+ assert statements with a simple spec
4. **Clear errors**: Shows exactly which transition failed and why

## Example Error Message

```
AssertionError: [8] retrofit→WS1: Expected t=5.0, got t=4.0
```

This immediately tells you:
- Which transition failed (index 8)
- What was happening (retrofit→WS1)
- What was expected vs actual (t=5.0 vs t=4.0)
