# Chapter 3: Topology Configuration

## File: topology.json

The topology.json file defines the physical network structure of your railway yard. It specifies nodes (connection points) and edges (track segments) that form the foundation for track definitions.

## Example Configuration

```json
{
  "nodes": [1, 2],
  "edges": {
    "parking1": {"nodes": [1, 2], "length": 150.0},
    "parking2": {"nodes": [1, 2], "length": 270.0},
    "collection1": {"nodes": [1, 2], "length": 500.0},
    "WS1": {"nodes": [1, 2], "length": 260.0},
    "WS2": {"nodes": [1, 2], "length": 260.0},
    "Mainline": {"nodes": [1, 2], "length": 8000.0}
  }
}
```

## Structure

PopUpSim will use a node edge model of the track network in the future. This
is not implemented in the MVP since PopUpSim will not e.g. take connectivity
between tracks into account. Only track length is important till now.

### Nodes

The nodes are currently unused in PopUpSim. They become imporant when the full
node edge model for representing the track network.

Nodes represent connection points in the railway network (e.g., switches, junctions).

```json
"nodes": [1, 2]
```

- **Type:** Array of integers
- **Purpose:** Define connection points for edges
- **Example:** `[1, 2]` creates two nodes

**In the ten_trains_two_days scenario:**
- Only 2 nodes are used (simplified topology)
- All tracks connect between these two nodes
- This represents a linear yard layout

### Edges

Edges represent physical track segments connecting nodes. The node definitions
are currently unused. The length is important.

```json
"edges": {
  "edge_id": {
    "nodes": [start_node, end_node],
    "length": length_in_meters
  }
}
```

| Parameter | Type | Description | Unit |
|-----------|------|-------------|------|
| `edge_id` | string | Unique identifier for the edge | - |
| `nodes` | array[int, int] | Start and end node IDs | - |
| `length` | float | Physical length of the track segment | meters |

## Example Edges

Here the nodes are just defined, they have no real meaning but are necessary to
define the edges.

### Parking Tracks

```json
"parking1": {"nodes": [1, 2], "length": 150.0},
"parking2": {"nodes": [1, 2], "length": 270.0}
```

- Short to medium length (100-600m)
- Used for wagon storage
- Length determines wagon capacity

### Collection Tracks

```json
"collection1": {"nodes": [1, 2], "length": 500.0},
"collection2": {"nodes": [1, 2], "length": 500.0}
```

- Medium length (500m)
- Used for incoming train reception
- Must accommodate full train lengths

### Workshop Tracks

```json
"WS1": {"nodes": [1, 2], "length": 260.0},
"WS2": {"nodes": [1, 2], "length": 260.0}
```

- Medium length (260m)
- Used for retrofit operations
- Length affects workshop capacity

### Mainline

```json
"Mainline": {"nodes": [1, 2], "length": 8000.0}
```

- Very long (8000m)
- Connects different yard areas
- Represents main circulation path

## Track Length Considerations

Track length directly affects capacity:

**Wagon Capacity Calculation:**
```
capacity = floor(track_length / wagon_length)
```

**Example:**
- Track length: 260m
- Average wagon length: 20m
- Capacity: 260 / 20 = 13 wagons

**Typical Wagon Lengths:**
- Short wagons: 15-17m
- Medium wagons: 18-22m
- Long wagons: >23m

Note: Average values are only here for elucidation. The code itself uses the
given lengths in meters defined for each wagon.

## Common Modifications

### Adding a New Parking Track

```json
"parking17": {"nodes": [1, 2], "length": 300.0}
```

Then reference it in tracks.json:
```json
{"id": "parking17", "name": "Additional parking", "edges": ["parking17"], "type": "parking"}
```

### Adjusting Track Capacity

To increase capacity, increase length:

```json
"parking1": {"nodes": [1, 2], "length": 300.0}  // Was 150.0
```

This doubles the wagon capacity from ~7 to ~15 wagons.

### Creating Complex Topologies

For more realistic yards with multiple connection points:

```json
{
  "nodes": [1, 2, 3, 4],
  "edges": {
    "main_entry": {"nodes": [1, 2], "length": 500.0},
    "branch_left": {"nodes": [2, 3], "length": 300.0},
    "branch_right": {"nodes": [2, 4], "length": 300.0},
    "parking_a": {"nodes": [3, 3], "length": 200.0},
    "parking_b": {"nodes": [4, 4], "length": 200.0}
  }
}
```

## Validation Rules

- All node IDs in edges must exist in the nodes array
- Edge IDs must be unique
- Lengths must be positive numbers
- Each edge must connect exactly 2 nodes
- Edge IDs referenced in tracks.json must exist here

## Effect on Simulation

- **Track length** determines wagon capacity
- **Network structure** affects routing complexity
- **Node count** impacts route calculation performance
- **Edge naming** must match references in tracks.json

## Next Steps

Continue to [Chapter 4: Track Configuration](04-track-configuration.md) to learn how edges become functional tracks.
