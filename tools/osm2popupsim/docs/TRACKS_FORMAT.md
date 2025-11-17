# Tracks and Throats Format

This document describes the tracks configuration format for PopUpSim yard simulation.

## Overview

The tracks file defines:
1. **Tracks**: Logical groupings of edges representing physical tracks
2. **Throats**: Grouped switches that simplify simulation routing

## Purpose

- **Tracks** reference edges from the topology file and represent complete physical tracks
- **Track types** are user-defined (collection, retrofit, storage, etc.) for simulation logic
- **Throats** merge multiple switches into single routing elements to simplify simulation

## File Structure

```yaml
metadata:
  description: "Yard tracks configuration"
  version: "1.0.0"
  topology_reference: "topology.yaml"  # Path to topology file

tracks:
  - id: "track_1"
    name: "1"
    edges: ["edge_123", "edge_124"]
    type: "retrofit"

throats:
  - id: "throat_west"
    name: "West Throat"
    nodes: ["switch_1", "switch_2"]
    connections:
      - from: "boundary_entry"
        to: "track_1"
```

## Tracks

### Extraction from OSM

Tracks are automatically extracted from OSM data using:
- `railway:track_ref` tag (preferred)
- `ref` tag (fallback)

Edges with the same track reference are grouped into one track.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique track identifier |
| `name` | string | Yes | Track name (from OSM or user-defined) |
| `edges` | array | Yes | List of edge IDs from topology file |
| `type` | string | No | Track function (user-defined) |

### Track Types

Track types are user-defined based on simulation needs. Common examples:

- **`collection`**: Track for collecting wagons
- **`retrofit`**: Track where DAC retrofit happens
- **`storage`**: Storage track for waiting wagons
- **`inspection`**: Inspection track
- **`departure`**: Departure track
- **`arrival`**: Arrival track

## Throats

### Purpose

Throats simplify simulation by grouping multiple switches into a single routing element. Instead of simulating individual switch positions, the simulation can treat the throat as a black box with defined entry/exit connections.

### Benefits

1. **Simplified routing**: Define high-level connections instead of switch-by-switch paths
2. **Performance**: Reduce simulation complexity in switch-heavy areas
3. **Abstraction**: Hide internal switch complexity from simulation logic

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique throat identifier |
| `name` | string | Yes | Throat name |
| `nodes` | array | Yes | Switch node IDs grouped in this throat |
| `connections` | array | Yes | Possible routes through the throat |

### Throat Formats

**Simple Format** (recommended for most cases):
```yaml
entries: ["entry_1", "entry_2"]
exits: ["exit_1", "exit_2"]
# Implies: any entry can reach any exit
```

**Complex Format** (for restricted routing):
```yaml
connections:
  - from: "entry_1"
    to: "exit_1"
  - from: "entry_2"
    to: "exit_2"
# Explicit: only specified routes allowed
```

### Example: Yard with Two Throats

```yaml
metadata:
  description: "Yard with entry and exit throats"
  version: "1.0.0"
  topology_reference: "yard_topology.yaml"

tracks:
  - id: "track_1"
    name: "1"
    edges: ["edge_10", "edge_11", "edge_12"]
    type: "retrofit"

  - id: "track_2"
    name: "2"
    edges: ["edge_20", "edge_21"]
    type: "storage"

  - id: "track_3"
    name: "3"
    edges: ["edge_30", "edge_31", "edge_32"]
    type: "collection"

throats:
  # Entry throat: one entry to multiple exits (simple format)
  - id: "throat_entry"
    name: "Entry Throat"
    nodes: ["switch_1", "switch_2", "switch_3"]
    entries: ["boundary_west_entry"]
    exits: ["track_1", "track_2", "track_3"]

  # Exit throat: multiple entries to one exit (simple format)
  - id: "throat_exit"
    name: "Exit Throat"
    nodes: ["switch_4", "switch_5"]
    entries: ["track_1", "track_2", "track_3"]
    exits: ["boundary_east_exit"]
```

## Workflow

### 1. Extract Topology from OSM

```bash
uv run --group osm2popupsim osm2popupsim convert \
  railway_data.json -o topology.yaml -d "Yard name"
```

### 2. Extract Tracks from OSM

```bash
uv run --group osm2popupsim osm2popupsim extract-tracks \
  railway_data.json topology.yaml -o tracks.yaml
```

### 3. Manual Configuration

After extraction, manually edit `tracks.yaml`:

1. **Add track types**: Set `type` field for each track based on function
2. **Define throats**: Group switches and define connections
3. **Verify edge references**: Ensure all edge IDs exist in topology

### 4. Validation

Check that:
- All edge IDs in tracks exist in topology file
- All node IDs in throats exist in topology file
- All connection `from`/`to` references are valid (track IDs or boundary node IDs)
- Track types are set appropriately for simulation

## Simulation Usage

### Without Throats

Simulation must:
1. Route through individual switches
2. Set each switch position
3. Track complex paths through switch networks

### With Throats

Simulation can:
1. Route at throat level (entry → track, track → exit)
2. Treat throat as single routing decision
3. Simplify path planning

## Best Practices

1. **Group related switches**: Throats should contain switches that work together
2. **Define all connections**: List all possible routes through each throat
3. **Use meaningful names**: Track and throat names should reflect their function
4. **Set track types**: Always define track types for simulation logic
5. **Document custom types**: If using custom track types, document their meaning

## Schema

See `schemas/tracks_schema.json` for complete JSON schema validation.
