# Chapter 2: Scenario Configuration

## File: scenario.json

The scenario.json file is the entry point for your simulation. It defines metadata, simulation timeframe, selection strategies, and references to all other configuration files.

## Example Configuration

```json
{
  "id": "test_scenario_01",
  "description": "DAC retrofit simulation",
  "version": "1.0.0",
  "start_date": "2025-12-01T00:00:00+00:00",
  "end_date": "2025-12-20T00:00:00+00:00",
  "collection_track_strategy": "first_available",
  "retrofit_selection_strategy": "best_fit",
  "retrofitted_selection_strategy": "first_available",
  "workshop_selection_strategy": "least_occupied",
  "parking_selection_strategy": "first_available",
  "references": {
    "locomotives": "locomotive.json",
    "process_times": "process_times.json",
    "routes": "routes.json",
    "trains": "train_schedule.csv",
    "topology": "topology.json",
    "tracks": "tracks.json",
    "workshops": "workshops.json"
  }
}
```

## Parameters

### Metadata

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `id` | string | Unique scenario identifier | `"test_scenario_01"` |
| `description` | string | Human-readable description | `"DAC retrofit simulation"` |
| `version` | string | Scenario version (semantic versioning) | `"1.0.0"` |

### Simulation Timeframe

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_date` | ISO 8601 datetime | Simulation start time (UTC) | `"2025-12-01T00:00:00+00:00"` |
| `end_date` | ISO 8601 datetime | Simulation end time (UTC) | `"2025-12-20T00:00:00+00:00"` |

**Important:** 
- Use ISO 8601 format with timezone (`+00:00` for UTC)
- End date must be after start date
- All train arrivals in train_schedule.csv must fall within this timeframe

### Selection Strategies

These strategies determine how the simulation selects resources when multiple options are available. Each track type and resource can have its own strategy.

| Parameter | Type | Available Values | Description |
|-----------|------|------------------|-------------|
| `collection_track_strategy` | string | See strategies below | How to select collection tracks for arriving trains |
| `retrofit_selection_strategy` | string | See strategies below | How to select retrofit tracks for wagon staging |
| `retrofitted_selection_strategy` | string | See strategies below | How to select retrofitted tracks for completed wagons |
| `workshop_selection_strategy` | string | See strategies below | How to select workshops for retrofit operations |
| `parking_selection_strategy` | string | See strategies below | How to select parking tracks for final storage |

**Available Strategies:**

| Strategy | Description | Best For |
|----------|-------------|----------|
| `least_occupied` | Selects resource with most available capacity | Load balancing, even utilization |
| `most_available` | Same as `least_occupied` (alias) | Load balancing |
| `first_available` | Selects first resource with any capacity | Simple scenarios, predictable behavior |
| `best_fit` | Selects resource with least available capacity that fits | Space optimization, filling tracks completely |
| `round_robin` | Cycles through resources in order | Fair distribution |
| `shortest_queue` | Selects resource with shortest waiting queue | Minimizing wait times |
| `random` | Random selection from available resources | Testing, load distribution |

**Recommended Configurations:**

- **Collection tracks**: `first_available` - Simple, predictable train arrival handling
- **Retrofit tracks**: `best_fit` - Optimizes space usage, fills tracks efficiently
- **Retrofitted tracks**: `first_available` - Simple staging before parking
- **Workshops**: `least_occupied` - Balances workload across workshops
- **Parking tracks**: `first_available` - Simple final storage allocation

### References

The `references` object maps logical names to configuration filenames. All paths are relative to the scenario directory.

| Key | Required | Description | Typical Filename |
|-----|----------|-------------|------------------|
| `locomotives` | Yes | Locomotive configuration | `locomotive.json` |
| `process_times` | Yes | Operation timing parameters | `process_times.json` |
| `routes` | Yes | Movement paths between tracks | `routes.json` |
| `trains` | Yes | Train schedule and wagon data | `train_schedule.csv` |
| `topology` | Yes | Network structure | `topology.json` |
| `tracks` | Yes | Track definitions | `tracks.json` |
| `workshops` | Yes | Workshop configurations | `workshops.json` |

**Note:** All referenced files must exist in the scenario directory, or PopUpSim will fail validation.

## Common Modifications

### Extending Simulation Duration

To simulate a longer period:

```json
{
  "start_date": "2025-12-01T00:00:00+00:00",
  "end_date": "2025-12-31T23:59:59+00:00"
}
```

### Changing Selection Strategies

To test different resource allocation approaches:

```json
{
  "collection_track_strategy": "round_robin",
  "retrofit_selection_strategy": "least_occupied",
  "retrofitted_selection_strategy": "first_available",
  "workshop_selection_strategy": "shortest_queue",
  "parking_selection_strategy": "best_fit"
}
```

**Strategy Impact Examples:**

- Using `best_fit` for retrofit tracks fills each track completely before using the next, maximizing space efficiency
- Using `least_occupied` for workshops distributes work evenly, preventing bottlenecks
- Using `shortest_queue` for workshops minimizes wagon waiting times

### Setting Maximum Fill Levels Per Track Type

To define how much of each track type's physical length should be usable, use `track_type_fill_factors`. This sets a default fill factor for all tracks of a given type:

```json
{
  "track_type_fill_factors": {
    "parking": 0.6,
    "collection": 0.8,
    "retrofit": 0.9,
    "retrofitted": 0.85,
    "workshop": 1.0
  }
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `track_type_fill_factors` | object | Maps track type names to fill factor values (0.0 – 1.0) |

**Fill Factor Values:**
- `1.0` = 100% of physical track length is usable
- `0.75` = 75% of physical track length is usable (default when not specified)
- `0.5` = 50% of physical track length is usable

**Precedence:** If an individual track in `tracks.json` specifies its own `fillfactor`, that value takes priority over the type-level default defined here.

**Use Cases:**
- Set parking tracks to 60% to leave safety margins for shunting operations
- Set collection tracks to 80% to account for coupling distances
- Set workshop tracks to 100% since wagons are precisely positioned

### Locomotive Task Priorities

To control which operations a locomotive serves first, configure `task_priorities`. Priorities are dynamic — they change based on track fill levels, so the system reacts to pressure automatically.

```json
{
  "task_priorities": {
    "collection_to_retrofit": {
      "base_priority": 2,
      "hold_until": {"condition": "target_fill_below", "threshold": 0.6},
      "rules": [
        {"condition": "source_fill_above", "threshold": 0.7, "priority": 1},
        {"condition": "source_fill_above", "threshold": 0.9, "priority": 0}
      ]
    },
    "retrofit_to_workshop": {
      "base_priority": 3,
      "rules": [
        {"condition": "target_idle", "threshold": 0.0, "priority": 1},
        {"condition": "source_fill_below", "threshold": 0.2, "priority": 5}
      ]
    },
    "workshop_to_retrofitted": {
      "base_priority": 2,
      "rules": []
    },
    "retrofitted_to_parking": {
      "base_priority": 3,
      "hold_until": {"condition": "source_fill_above", "threshold": 0.3},
      "rules": [
        {"condition": "source_fill_above", "threshold": 0.8, "priority": 1},
        {"condition": "source_fill_above", "threshold": 0.95, "priority": 0}
      ]
    }
  }
}
```

**Task Types:**

| Task Type | Movement |
|-----------|----------|
| `collection_to_retrofit` | Collection track → Retrofit staging |
| `retrofit_to_workshop` | Retrofit staging → Workshop |
| `workshop_to_retrofitted` | Workshop → Retrofitted staging |
| `retrofitted_to_parking` | Retrofitted staging → Parking |

**Priority Values:**
- Lower number = higher priority (0 is most urgent)
- `base_priority` applies when no rules match
- Rules are evaluated top-to-bottom, last matching rule wins

**Hold Until (Task Eligibility Gate):**

The `hold_until` field prevents a task from being submitted until a condition is met. This avoids wasteful small-batch trips — wagons accumulate until there's enough room at the target for a meaningful batch.

| Parameter | Type | Description |
|-----------|------|-------------|
| `condition` | string | Condition that must be TRUE for the task to proceed |
| `threshold` | float | Threshold value (0.0–1.0) |

**Example:** `"hold_until": {"condition": "target_fill_below", "threshold": 0.6}` means "don't move wagons until the target track is below 60% full." While held, wagons accumulate at the source, naturally forming larger batches.

**Available Conditions (for both rules and hold_until):**

| Condition | Description |
|-----------|-------------|
| `source_fill_above` | Source track type fill level exceeds threshold |
| `source_fill_below` | Source track type fill level is below threshold |
| `target_fill_above` | Target track type fill level exceeds threshold |
| `target_fill_below` | Target track type fill level is below threshold |
| `target_idle` | Target resource (workshop) is idle |

**How It Works:**
1. Coordinator detects wagons ready to move
2. If `hold_until` condition is NOT met → task is held (not submitted)
3. Once condition is met → task is submitted to the dispatcher
4. Dispatcher evaluates priority of all eligible pending tasks
5. Highest-priority task (lowest number) gets the next free locomotive
6. Ties are broken by submission time (first-come-first-served)

**Optimization Use Cases:**
- Hold collection→retrofit until retrofit is below 60% (accumulate proper batches)
- Hold parking until retrofitted track is above 30% (don't waste trips for 1-2 wagons)
- Clear collection tracks urgently when trains are arriving (prevent blocking)
- Feed idle workshops immediately (maximize throughput)
- Escalate parking when retrofitted track fills up (prevent workshop stalling)

## Validation Rules

- `id` must be unique across scenarios
- `start_date` must be before `end_date`
- All referenced files must exist
- Selection strategies must use valid values
- Dates must be in ISO 8601 format with timezone

## Next Steps

Continue to [Chapter 3: Topology Configuration](03-topology-configuration.md) to learn about network structure.
