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

## Validation Rules

- `id` must be unique across scenarios
- `start_date` must be before `end_date`
- All referenced files must exist
- Selection strategies must use valid values
- Dates must be in ISO 8601 format with timezone

## Next Steps

Continue to [Chapter 3: Topology Configuration](03-topology-configuration.md) to learn about network structure.
