# PopUpSim Network Format Documentation

This document describes the data formats used in PopUpSim for multi-scale railway network simulation.

## Overview

PopUpSim uses a two-level simulation architecture:

- **Microscopic Level**: Detailed yard topology with individual tracks, switches, and signals
- **Mesoscopic Level**: High-level yard-to-yard connections with travel distances

## File Structure

```
data/
  ├── network.yaml                    # Mesoscopic: yard connections
  └── yards/
      ├── haldensleben_topology.yaml  # Microscopic: yard topology (nodes/edges)
      ├── haldensleben_tracks.yaml    # Track definitions and throats
      ├── haldensleben_routes.yaml    # Predefined shunting routes
      ├── magdeburg_topology.yaml
      ├── magdeburg_tracks.yaml
      ├── magdeburg_routes.yaml
      └── ...
```

## Microscopic Format (Yard Networks)

Microscopic networks consist of three files:
1. **Topology**: Detailed track topology (nodes, edges, switches)
2. **Tracks**: Logical track groupings and throat definitions
3. **Routes**: Predefined paths for shunting movements

### Topology File

**Schema Location**:
- **Schema**: `tools/osm2popupsim/schemas/popupsim_schema.json`
- **Template**: `tools/osm2popupsim/schemas/popupsim_template.yaml`

**Structure**:

```yaml
metadata:
  description: "Yard name or description"
  version: "1.0.0"
  level: "microscopic"
  projection: "cartesian"
  crs: "EPSG:3857"
  units:
    length: "meters"
    coordinates: "meters"

nodes:
  node_id:
    type: "switch"  # or buffer_stop, crossing, signal, station, junction, boundary
    coords: [x, y]  # Projected coordinates in meters
    
    # For switches only
    switch_config:
      stem: "edge_1"
      branches: ["edge_2", "edge_3"]
      switch_type: "default"
    
    # For boundary nodes only
    boundary_type: "entry"  # or exit, both

edges:
  edge_id:
    nodes: ["node_1", "node_2"]
    length: 245.8  # meters
    direction: "bi-directional"  # or one-way
    type: "rail"  # or siding, yard, spur
    status: "active"  # or disused, abandoned
```

### Node Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `switch` | Railway switch/turnout | `coords`, `switch_config` |
| `buffer_stop` | End of track | `coords` |
| `crossing` | Level crossing | `coords` |
| `signal` | Railway signal | `coords` |
| `station` | Station stop | `coords` |
| `junction` | Track junction | `coords` |
| `boundary` | Entry/exit point | `coords`, `boundary_type` |

### Boundary Nodes

Boundary nodes mark entry and exit points where trains transition between microscopic and mesoscopic simulation:

- **`entry`**: Trains appear here when entering the yard
- **`exit`**: Trains disappear here when leaving the yard
- **`both`**: Node serves as both entry and exit

### Tracks File

**Schema Location**:
- **Schema**: `tools/osm2popupsim/schemas/tracks_schema.json`
- **Template**: `tools/osm2popupsim/schemas/tracks_template.yaml`

**Structure**:

```yaml
metadata:
  description: "Yard tracks"
  version: "1.0.0"
  topology_reference: "haldensleben_topology.yaml"

tracks:
  - id: "track_1"
    name: "1"  # From OSM railway:track_ref or ref tag
    edges: ["edge_123", "edge_124", "edge_125"]  # References topology edges
    type: null  # User sets: collection, retrofit, storage, etc.

  - id: "track_2"
    name: "2"
    edges: ["edge_126", "edge_127"]
    type: "retrofit"

throats:
  # Simple: any entry can reach any exit
  - id: "throat_west"
    name: "West Throat"
    nodes: ["switch_1", "switch_2", "switch_3"]
    entries: ["boundary_entry_west"]
    exits: ["track_1", "track_2"]

  # Complex: explicit routing
  - id: "throat_complex"
    name: "Complex Throat"
    nodes: ["switch_10"]
    connections:
      - from: "track_5"
        to: "track_6"
```

**Track Fields**:
- **`id`**: Unique track identifier
- **`name`**: Track name (extracted from OSM `railway:track_ref` or `ref` tag)
- **`edges`**: List of edge IDs from topology file
- **`type`**: Track function (user-defined: collection, retrofit, storage, etc.)

**Throat Fields**:
- **`id`**: Unique throat identifier
- **`name`**: Throat name
- **`nodes`**: Switch node IDs grouped in this throat
- **`entries`**: Entry points (any entry can reach any exit) - simple format
- **`exits`**: Exit points (any entry can reach any exit) - simple format
- **`connections`**: Explicit routes (use instead of entries/exits for complex routing)

### Routes File

**Schema Location**:
- **Schema**: `tools/osm2popupsim/schemas/routes_schema.json`
- **Template**: `tools/osm2popupsim/schemas/routes_template.yaml`
- **Documentation**: `docs/ROUTES_FORMAT.md`

**Structure**:

```yaml
metadata:
  description: "Yard routes"
  version: "1.0.0"
  topology_reference: "topology.yaml"
  tracks_reference: "tracks.yaml"

routes:
  - id: "route_1"
    name: "Track 1 to Track 2"
    from: "track_1"
    to: "track_2"
    path: ["track_1", "edge_123", "node_456", "edge_124", "track_2"]
    duration: 120  # Optional: seconds

  # Reversal: same edge twice
  - id: "route_2"
    from: "track_1"
    to: "track_3"
    path: ["track_1", "edge_100", "node_200", "edge_100", "track_3"]
```

**Route Fields**:
- **`id`**: Unique route identifier
- **`name`**: Human-readable route name (optional)
- **`from`**: Starting point (track ID or boundary node)
- **`to`**: Destination (track ID or boundary node)
- **`path`**: Sequence of nodes and edges (alternating)
- **`duration`**: Total duration in seconds (optional, calculated from speed if omitted)

**Notes**:
- Reversals detected when same edge appears twice
- Throats detected automatically from path
- All IDs must exist in topology

## Mesoscopic Format (Network Connections)

Mesoscopic networks describe yard-to-yard connections for inter-yard travel.

### Schema Location
- **Schema**: `tools/osm2popupsim/schemas/network_schema.json`
- **Template**: `tools/osm2popupsim/schemas/network_template.yaml`

### Structure

```yaml
metadata:
  description: "Network description"
  version: "1.0.0"
  level: "mesoscopic"
  units: "meters"

yards:
  - id: "haldensleben"
    name: "Haldensleben Yard"
    microscopic_network: "yards/haldensleben.yaml"
    entry_points: ["node_123", "node_456"]
    exit_points: ["node_789"]
    location: [11.4, 52.3]  # Optional: [lon, lat]
    capacity: 50  # Optional: wagon capacity

connections:
  - from_yard: "haldensleben"
    from_exit: "node_789"
    to_yard: "magdeburg"
    to_entry: "node_001"
    length: 45000  # meters
```

### Yards

Each yard definition includes:

- **`id`**: Unique identifier (used in connections)
- **`name`**: Human-readable name
- **`microscopic_network`**: Path to microscopic YAML file
- **`entry_points`**: List of boundary node IDs where trains enter
- **`exit_points`**: List of boundary node IDs where trains exit
- **`location`**: Optional [longitude, latitude] for visualization
- **`capacity`**: Optional yard capacity in wagons

### Connections

Each connection defines a point-to-point route between yards:

- **`from_yard`**: Source yard ID
- **`from_exit`**: Boundary node ID in source yard (must be in `exit_points`)
- **`to_yard`**: Destination yard ID
- **`to_entry`**: Boundary node ID in destination yard (must be in `entry_points`)
- **`length`**: Distance in meters (or kilometers if specified in metadata)

## Simulation Flow

1. **Train spawns** at entry boundary node in yard A (microscopic simulation)
2. **Train operates** within yard A using detailed track topology
3. **Train exits** at exit boundary node → disappears from microscopic simulation
4. **Mesoscopic layer** tracks train on connection edge
5. **Estimated arrival** = current_time + (length / train_speed)
6. **Train appears** at entry boundary node in yard B (microscopic simulation)

## Validation Rules

### Microscopic Networks
- All node IDs must be unique within the network
- All edge node references must exist in nodes
- Switch nodes must have `switch_config`
- Boundary nodes must have `boundary_type`
- Coordinates must be projected (cartesian)

### Mesoscopic Networks
- All yard IDs must be unique
- All `microscopic_network` paths must be valid
- Entry/exit point node IDs must exist in referenced microscopic networks
- Connection `from_exit` must be in source yard's `exit_points`
- Connection `to_entry` must be in destination yard's `entry_points`

## Example: Two-Yard Network

### network.yaml
```yaml
metadata:
  description: "Simple two-yard network"
  version: "1.0.0"
  level: "mesoscopic"
  units: "meters"

yards:
  - id: "yard_a"
    name: "Yard A"
    microscopic_network: "yards/yard_a.yaml"
    entry_points: ["boundary_in"]
    exit_points: ["boundary_out"]

  - id: "yard_b"
    name: "Yard B"
    microscopic_network: "yards/yard_b.yaml"
    entry_points: ["boundary_in"]
    exit_points: ["boundary_out"]

connections:
  - from_yard: "yard_a"
    from_exit: "boundary_out"
    to_yard: "yard_b"
    to_entry: "boundary_in"
    length: 50000

  - from_yard: "yard_b"
    from_exit: "boundary_out"
    to_yard: "yard_a"
    to_entry: "boundary_in"
    length: 50000
```

### yards/yard_a.yaml
```yaml
metadata:
  description: "Yard A"
  version: "1.0.0"
  level: "microscopic"
  projection: "cartesian"
  crs: "EPSG:3857"
  units:
    length: "meters"
    coordinates: "meters"

nodes:
  boundary_in:
    type: "boundary"
    boundary_type: "entry"
    coords: [0, 0]

  switch_1:
    type: "switch"
    coords: [100, 0]
    switch_config:
      stem: "edge_1"
      branches: ["edge_2", "edge_3"]
      switch_type: "default"

  boundary_out:
    type: "boundary"
    boundary_type: "exit"
    coords: [200, 0]

edges:
  edge_1:
    nodes: ["boundary_in", "switch_1"]
    length: 100
    direction: "bi-directional"
    type: "rail"
    status: "active"

  edge_2:
    nodes: ["switch_1", "boundary_out"]
    length: 100
    direction: "bi-directional"
    type: "rail"
    status: "active"
```

## Tools

### OSM to PopUpSim Converter

Convert OpenStreetMap railway data to topology and tracks:

```bash
# Convert to topology (nodes and edges)
uv run --group osm2popupsim osm2popupsim convert \
  input.json -o topology.yaml -d "Yard description"

# Extract tracks from OSM ref tags
uv run --group osm2popupsim osm2popupsim extract-tracks \
  input.json topology.yaml -o tracks.yaml
```

Note: 
- Boundary nodes must be manually added to topology after conversion
- Track types must be manually set by user (collection, retrofit, etc.)
- Throats must be manually defined by user

## Future Extensions

Potential additions to the format:

- **Signals**: Add signal positions and aspects
- **Speed limits**: Per-edge speed restrictions
- **Electrification**: Track electrification status
- **Gauge**: Track gauge information
- **Platforms**: Station platform data
- **Capacity constraints**: Edge capacity limits
