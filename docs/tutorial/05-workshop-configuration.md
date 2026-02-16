# Chapter 5: Workshop Configuration

## File: workshops.json

The workshops.json file defines retrofit workshops, their capacity, and associated tracks. Workshops are the critical bottleneck in the simulation where wagons receive DAC retrofits.

## Example Configuration

```json
{
  "metadata": {
    "description": "Workshop configurations for DAC retrofit operations",
    "version": "1.0.0",
    "created": "2024-01-15"
  },
  "workshops": [
    {
      "id": "WS_01",
      "name": "First workshop",
      "retrofit_stations": 2,
      "track": "track_WS1"
    },
    {
      "id": "WS_02",
      "name": "Second workshop",
      "retrofit_stations": 2,
      "track": "track_WS2"
    }
  ]
}
```

## Structure

### Metadata

Optional metadata for documentation:

| Parameter | Type | Description |
|-----------|------|-------------|
| `description` | string | Workshop configuration description |
| `version` | string | Configuration version |
| `created` | string | Creation date |

### Workshop Definitions

Each workshop in the `workshops` array:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Unique workshop identifier |
| `name` | string | No | Human-readable workshop name |
| `retrofit_stations` | integer | Yes | Number of parallel retrofit stations |
| `track` | string | Yes | Associated track ID from tracks.json |

## Parameters Explained

### id

Unique identifier for the workshop:

```json
"id": "WS_01"
```

- Must be unique across all workshops
- Used in logs and reports
- Referenced internally by simulation

### name

Human-readable workshop name:

```json
"name": "First workshop"
```

- Optional but recommended
- Used in reports and visualizations
- Helps identify workshops during analysis

### retrofit_stations

Number of parallel retrofit stations in the workshop:

```json
"retrofit_stations": 2
```

**Critical Parameter:**
- Determines how many wagons can be retrofitted simultaneously
- Directly affects workshop throughput
- More stations = higher capacity but higher cost
- **This is the ONLY capacity constraint** - track length is not checked

**Throughput Calculation:**
```
wagons_per_hour = (retrofit_stations * 60) / wagon_retrofit_time
```

**Example:**
- 2 stations, 60-minute retrofit time
- Throughput: (2 × 60) / 60 = 2 wagons/hour
- Daily capacity: 2 × 24 = 48 wagons/day

**Typical Values:**
- Small workshop: 1-2 stations
- Medium workshop: 2-4 stations
- Large workshop: 4-8 stations

### track

Reference to the workshop track:

```json
"track": "track_WS1"
```

- Must match a track ID from tracks.json
- Track must have type "workshop"
- Track length does NOT affect capacity (only retrofit_stations matter)

## Workshop Capacity Analysis

### Station Count Impact

| Stations | Wagons/Hour (60min retrofit) | Daily Capacity | Use Case |
|----------|------------------------------|----------------|----------|
| 1 | 1 | 24 | Small operations |
| 2 | 2 | 48 | Standard workshop |
| 4 | 4 | 96 | High-volume workshop |
| 8 | 8 | 192 | Industrial-scale |

**Important:** The number of retrofit_stations is the ONLY capacity constraint. The simulation pulls exactly as many wagons from the retrofit staging track as there are available stations. Track length is not checked.

## Common Modifications

### Increasing Workshop Capacity

Add more retrofit stations:

```json
{
  "id": "WS_01",
  "name": "First workshop - expanded",
  "retrofit_stations": 4,  // Was 2
  "track": "track_WS1"
}
```

**Effect:**
- Doubles throughput
- Reduces wagon waiting times
- Processes 4 wagons simultaneously instead of 2

### Adding a New Workshop

```json
{
  "id": "WS_03",
  "name": "Third workshop",
  "retrofit_stations": 2,
  "track": "track_WS3"
}
```

**Requirements:**
1. Add edge in topology.json: `"WS3": {"nodes": [1, 2], "length": 260.0}`
2. Add track in tracks.json: `{"id": "WS3", "edges": ["WS3"], "type": "workshop"}`
3. Add routes connecting WS3 to other tracks in routes.json

**Note:** Track length can be any reasonable value - it doesn't affect workshop capacity. Only `retrofit_stations` determines how many wagons are processed simultaneously.

**Effect:**
- Increases total retrofit capacity
- Improves throughput
- Reduces bottlenecks

### Asymmetric Workshop Configuration

Different workshops with different capacities:

```json
{
  "workshops": [
    {
      "id": "WS_01",
      "name": "Small workshop",
      "retrofit_stations": 1,
      "track": "track_WS1"
    },
    {
      "id": "WS_02",
      "name": "Large workshop",
      "retrofit_stations": 4,
      "track": "track_WS2"
    }
  ]
}
```

**Use case:** Modeling existing infrastructure with varying capacities

## Workshop Selection Strategy

The `workshop_selection_strategy` in scenario.json determines how wagons are assigned to workshops:

**least_occupied:**
```
Workshop 1: 1/2 stations busy → 50% utilization
Workshop 2: 2/2 stations busy → 100% utilization
→ Wagon assigned to Workshop 1
```

**first_available:**
```
Workshop 1: 1/2 stations busy → available
Workshop 2: 2/2 stations busy → full
→ Wagon assigned to Workshop 1 (first with capacity)
```

## Validation Rules

- Workshop IDs must be unique
- `retrofit_stations` must be positive integer
- Referenced tracks must exist in tracks.json
- Referenced tracks must have type "workshop"
- At least one workshop must be defined

## Effect on Simulation

- **retrofit_stations** is the primary throughput determinant
- **Number of workshops** provides redundancy and capacity
- **Track assignment** affects spatial distribution
- **Workshop capacity** often becomes the simulation bottleneck

## Performance Considerations

### Bottleneck Analysis

If workshops are the bottleneck:
- Wagons queue at retrofit staging tracks
- Parking tracks fill up
- Collection tracks may block

**Solutions:**
1. Increase `retrofit_stations` in workshops.json
2. Add more workshops
3. Optimize workshop selection strategy

### Capacity Planning

**Rule of thumb:**
```
required_stations = (total_wagons × wagon_retrofit_time) / (simulation_duration × 60)
```

**Example:**
- 224 wagons
- 60-minute retrofit time
- 48-hour simulation (2880 minutes)
- Required: (224 × 60) / 2880 = 4.67 → 5 stations minimum

**ten_trains_two_days has 4 stations (2 workshops × 2 stations)** → Expect some queuing

## Next Steps

Continue to [Chapter 6: Process Times Configuration](06-process-times-configuration.md) to learn about operation durations.
