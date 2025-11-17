# Routes Format

Predefined routes for shunting movements in yard simulation.

## Overview

Routes define specific paths through the yard topology for train movements. Each route specifies:
- Start and end points
- Exact path through nodes and edges
- Optional duration

## Schema

**Location**: `tools/osm2popupsim/schemas/routes_schema.json`

## Formats

Routes support two formats:

### 1. Waypoint Format (Simple)

User-friendly format where you just specify track names. Path is auto-generated.

```yaml
routes:
  - id: "route_1"
    name: "Track 8 to 1a with reversal"
    type: "waypoint"
    waypoints: ["8", "1a", "1a", "20"]  # Repeat track for reversal
```

### 2. Explicit Format (Detailed)

Full control over exact path through nodes and edges.

```yaml
routes:
  - id: "route_2"
    name: "Custom path"
    type: "explicit"
    from: "track_1"
    to: "track_2"
    path: ["track_1", "edge_123", "node_456", "edge_124", "track_2"]
    duration: 120  # Optional
```

## Fields

### Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Human-readable description |
| `version` | string | Yes | Schema version (semantic versioning) |
| `topology_reference` | string | Yes | Path to topology YAML file |
| `tracks_reference` | string | No | Path to tracks YAML file |

### Waypoint Route

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique route identifier |
| `name` | string | No | Human-readable route name |
| `type` | string | Yes | Must be "waypoint" |
| `waypoints` | array | Yes | Track names in order (repeat for reversal) |
| `duration` | number | No | Total duration in seconds (calculated if omitted) |

### Explicit Route

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique route identifier |
| `name` | string | No | Human-readable route name |
| `type` | string | Yes | Must be "explicit" |
| `from` | string | Yes | Starting point (track ID or boundary node) |
| `to` | string | Yes | Destination (track ID or boundary node) |
| `path` | array | Yes | Sequence of nodes and edges |
| `duration` | number | No | Total duration in seconds (calculated if omitted) |
| `segment_durations` | object | No | Duration per edge in seconds (overrides speed calculation) |

## Path Specification

The `path` array contains an alternating sequence of nodes and edges:

```yaml
path: ["track_1", "edge_10", "node_20", "edge_30", "track_2"]
#      ^start     ^edge     ^node     ^edge     ^end
```

**Rules**:
- Must start and end with node/track IDs
- Alternates between nodes and edges
- All IDs must exist in topology
- Path must be continuous (edges connect nodes)

## Reversals

Reversals are detected automatically when the same edge appears twice consecutively:

```yaml
path: ["track_1", "edge_100", "node_200", "edge_100", "node_300", "edge_101", "track_3"]
#                 ^edge_100              ^edge_100 again = REVERSAL at node_200
```

**Detection logic**:
- Same edge ID appears twice in sequence → reversal
- Reversal point is the node between the two edge occurrences
- Edge must have `direction: "bi-directional"` in topology

## Duration

### Total Duration

**Optional field**: If omitted, duration is calculated from:
- Edge lengths (from topology)
- Train speed (from simulation parameters)

**If specified**: Used directly by simulation (in seconds)

### Segment Durations

**Optional field**: Specify duration per edge (in seconds)

```yaml
segment_durations:
  edge_123: 45  # 45 seconds for edge_123
  edge_124: 30  # 30 seconds for edge_124
```

**Priority**:
1. `segment_durations` (if specified for an edge)
2. `duration` (total, distributed across edges)
3. Calculated from edge length / speed

**Use cases**:
- Different speeds per segment
- Account for acceleration/deceleration zones
- Include dwell times at specific locations
- Model congestion or speed restrictions

## Throat Handling

Throats are **not specified in routes** - they are detected automatically:

```python
# Simulation detects which throats are used
throats_used = find_throats_on_path(route.path, tracks_config)

# Check capacity before executing
for throat in throats_used:
    if throat.is_occupied():
        wait()
    throat.occupy()

# Execute route
train.move(route.path)

# Release throats
for throat in throats_used:
    throat.release()
```

## Waypoint Format Details

### Reversal Detection

Repeat a track name to indicate reversal:

```yaml
waypoints: ["8", "1a", "1a", "20"]
#                 ^^^^  ^^^^ = reversal at track 1a
```

**Behavior**:
1. Train enters track 1a from track 8
2. Train reverses within track 1a
3. Train exits track 1a toward track 20

### Path Generation

The system automatically:
1. Finds shortest path between consecutive tracks
2. Detects reversals (repeated track names)
3. Generates complete node/edge sequence
4. Creates explicit route for simulation

### Example Generation

```python
# User specifies waypoints
waypoints = ["8", "1a", "1a", "20"]

# System generates:
# 8 -> 1a: finds shortest path
# 1a (reversal): detected, handled
# 1a -> 20: finds shortest path
# Result: complete explicit path
```

## Examples

### Waypoint: Simple Route

```yaml
- id: "route_simple"
  type: "waypoint"
  waypoints: ["8", "1a"]
```

### Waypoint: With Reversal

```yaml
- id: "route_reversal"
  type: "waypoint"
  waypoints: ["8", "1a", "1a", "20"]
  # Enter 1a, reverse, exit to 20
```

### Waypoint: Multiple Reversals

```yaml
- id: "route_complex"
  type: "waypoint"
  waypoints: ["1", "2", "2", "3", "3", "4"]
  # Reverse at track 2, then reverse at track 3
```

### Explicit: Simple Route

```yaml
- id: "arrival_to_track1"
  name: "Arrival to Track 1"
  from: "boundary_entry"
  to: "track_1"
  path: ["boundary_entry", "edge_10", "node_20", "edge_11", "track_1"]
  duration: 90
```

### Route with Reversal

```yaml
- id: "track1_to_track2_reversal"
  name: "Track 1 to Track 2 (via reversal)"
  from: "track_1"
  to: "track_2"
  path: [
    "track_1",
    "edge_stem",      # Move forward on stem
    "node_junction",
    "edge_stem",      # Reverse on stem (same edge twice)
    "node_switch",
    "edge_branch",
    "track_2"
  ]
```

### Route without Duration

```yaml
- id: "track3_to_exit"
  name: "Track 3 to Exit"
  from: "track_3"
  to: "boundary_exit"
  path: ["track_3", "edge_50", "node_60", "edge_70", "boundary_exit"]
  # Duration calculated: sum(edge_lengths) / train_speed
```

### Route with Segment Durations

```yaml
- id: "track1_to_track5_custom"
  name: "Track 1 to Track 5 (custom segment times)"
  from: "track_1"
  to: "track_5"
  path: ["track_1", "edge_10", "node_20", "edge_30", "node_40", "edge_50", "track_5"]
  segment_durations:
    edge_10: 60   # Slow acceleration zone
    edge_30: 30   # Normal speed
    edge_50: 45   # Deceleration zone
  # Total duration: 60 + 30 + 45 = 135 seconds
```

## Validation

Routes should be validated against topology:

1. **Path continuity**: Each edge connects its adjacent nodes
2. **Node/edge existence**: All IDs exist in topology
3. **Reversals valid**: Reversed edges have `direction: "bi-directional"`
4. **Start/end match**: Path starts at `from`, ends at `to`

## Usage in Simulation

```python
# Load route
route = routes_config['routes'][0]

# Validate
validate_route(route, topology)

# Check throats
throats = find_throats_on_path(route.path, tracks_config)

# Execute
if all(not t.is_occupied() for t in throats):
    for t in throats:
        t.occupy()
    
    train.move(route.path, duration=route.get('duration'))
    
    for t in throats:
        t.release()
```

## Duration Calculation Logic

```python
def calculate_segment_duration(edge_id, route, topology, default_speed):
    # Priority 1: Explicit segment duration
    if 'segment_durations' in route and edge_id in route['segment_durations']:
        return route['segment_durations'][edge_id]
    
    # Priority 2: Distribute total duration
    if 'duration' in route:
        # Distribute proportionally by edge length
        edge_length = topology['edges'][edge_id]['length']
        total_length = sum(topology['edges'][e]['length'] for e in get_edges_from_path(route['path']))
        return route['duration'] * (edge_length / total_length)
    
    # Priority 3: Calculate from speed
    edge_length = topology['edges'][edge_id]['length']
    return edge_length / default_speed
```

## Future Extensions

Potential additions:
- **Dwell times**: Stops at specific nodes
- **Alternative paths**: Multiple paths for same from/to
- **Conditions**: When to use specific routes
- **Priority**: Route priority for conflict resolution
- **Speed limits**: Per-edge speed restrictions
