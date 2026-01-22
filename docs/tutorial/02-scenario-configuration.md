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
  "track_selection_strategy": "least_occupied",
  "workshop_selection_strategy": "least_occupied",
  "parking_selection_strategy": "least_occupied",
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

These strategies determine how the simulation selects resources when multiple options are available:

| Parameter | Type | Available Values | Description |
|-----------|------|------------------|-------------|
| `track_selection_strategy` | string | `"least_occupied"`, `"first_available"` | How to select parking tracks for wagons |
| `workshop_selection_strategy` | string | `"least_occupied"`, `"first_available"` | How to select workshops for retrofit operations |
| `parking_selection_strategy` | string | `"least_occupied"`, `"first_available"` | How to select parking locations for completed wagons |

**Strategy Descriptions:**

- **least_occupied** - Selects the resource with the most available capacity (balances load)
- **first_available** - Selects the first resource with any available capacity (simpler, may create bottlenecks)

**Effect on Simulation:**
- `least_occupied` typically results in better resource utilization and throughput
- `first_available` may be faster to compute but can lead to uneven resource usage
- For realistic scenarios, `least_occupied` is recommended

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

### Changing Selection Strategy

To test different resource allocation approaches:

```json
{
  "track_selection_strategy": "first_available",
  "workshop_selection_strategy": "least_occupied",
  "parking_selection_strategy": "least_occupied"
}
```

## Validation Rules

- `id` must be unique across scenarios
- `start_date` must be before `end_date`
- All referenced files must exist
- Selection strategies must use valid values
- Dates must be in ISO 8601 format with timezone

## Next Steps

Continue to [Chapter 3: Topology Configuration](03-topology-configuration.md) to learn about network structure.
