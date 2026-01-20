# Capacity Constraint Handling

## Overview

Coordinators handle capacity constraints (full tracks, busy resources) as normal operational conditions. They wait for capacity to become available rather than failing.

## Behavior

### Normal Operation

When capacity is temporarily unavailable:

```
INFO: Parking full at t=25.0. Wagons ['W01', 'W02'] waiting 5 min.
```

Coordinator waits 5 minutes and checks again. This continues until capacity frees up.

### Potential Capacity Issue

After multiple waits (default: 3), warnings indicate possible undersizing:

```
WARNING: Parking still full after 15 minutes at t=40.0.
Wagons ['W01', 'W02'] still waiting. Check parking capacity configuration.
```

Simulation continues running - this is just a warning for capacity planning.

## Configuration

```python
coordinator = ParkingCoordinator(
    env=env,
    max_retry_attempts=3,    # When to start warning
    retry_delay=5.0,         # Wait time between checks (minutes)
)
```

## Implementation Pattern

```python
while not resource:
    resource = self.try_get_resource()
    
    if not resource:
        retry_count += 1
        
        if retry_count == 1:
            logger.info(f"Resource full, waiting {self.retry_delay} min")
        elif retry_count >= self.max_retry_attempts:
            logger.warning(f"Resource still full after {retry_count * self.retry_delay} minutes")
        
        yield self.env.timeout(self.retry_delay)
```

## Why Not Raise Errors?

1. **Normal operation** - Full tracks are expected in busy workshops
2. **Self-resolving** - Capacity frees up as wagons move through
3. **Simulation purpose** - We want to see how system behaves under load
4. **Timeout handles termination** - `env.run(until=X)` prevents infinite runs
