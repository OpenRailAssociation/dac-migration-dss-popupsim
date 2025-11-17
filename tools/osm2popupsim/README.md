# OSM to PopUpSim Converter

Convert OpenStreetMap railway data to PopUpSim network format.

## Installation

```bash
cd tools/osm2popupsim
uv sync
```

## Features

- **Convert** OSM railway data to PopUpSim topology format
- **Extract tracks** from OSM ref tags (railway:track_ref, ref)
- **Plot networks** with track type visualization
- **Animate train movements** using Folium (HTML) or Matplotlib (GIF)
- **Detect switch topology** automatically using angle analysis

## Usage

### Convert OSM to Topology

```bash
# Convert OSM JSON to topology YAML (active tracks only)
uv run osm2popupsim convert railway_data.json -o topology.yaml -d "Yard name"

# Include disused/abandoned tracks
uv run osm2popupsim convert railway_data.json -o topology.yaml -d "Yard name" --include-disused

# Include razed (demolished) tracks
uv run osm2popupsim convert railway_data.json -o topology.yaml -d "Yard name" --include-razed

# Include both disused and razed tracks
uv run osm2popupsim convert railway_data.json -o topology.yaml -d "Yard name" --include-disused --include-razed
```

### Extract Tracks

```bash
# Extract tracks from OSM ref tags
uv run osm2popupsim extract-tracks railway_data.json topology.yaml -o tracks.yaml
```

### Plot Network

```bash
# Plot topology only
uv run osm2popupsim plot topology.yaml

# Plot with track labels
uv run osm2popupsim plot topology.yaml -t tracks.yaml -o network.png

# Debug plot with all node/edge IDs (Folium HTML)
uv run osm2popupsim plot-debug topology.yaml -o debug.html

# Interactive Folium plot with track types
uv run osm2popupsim plot-folium topology.yaml tracks.yaml -o network.html

# Folium plot with throat highlighting
uv run osm2popupsim plot-folium topology.yaml tracks.yaml --throats throats.yaml -o network.html
```

### Animate Train Movements

```bash
# Create Folium HTML animation
uv run osm2popupsim animate sequence.yaml topology.yaml tracks.yaml routes.yaml -o animation.html

# Create Matplotlib GIF animation
uv run osm2popupsim animate-matplotlib sequence.yaml topology.yaml tracks.yaml routes.yaml -o animation.gif --fps 10
```

## Testing

Run the test suite:

```bash
# From project root
uv run pytest tools/osm2popupsim/tests/ -v

# From osm2popupsim directory
cd tools/osm2popupsim
uv run pytest tests/ -v
```

## Format

See `schemas/` for:
- `popupsim_schema.json` - Topology JSON schema
- `popupsim_template.yaml` - Topology example
- `tracks_schema.json` - Tracks JSON schema
- `tracks_template.yaml` - Tracks example
- `routes_schema.json` - Routes JSON schema
- `routes_template.yaml` - Routes example
- `network_schema.json` - Mesoscopic network JSON schema
- `network_template.yaml` - Mesoscopic network example

See documentation:
- `docs/NETWORK_FORMAT.md` - Complete format specification
- `docs/TRACKS_FORMAT.md` - Tracks and throats details
- `docs/ROUTES_FORMAT.md` - Routes specification

## Switch Topology Detection

The converter uses **angle analysis** to detect switch topology:

**Simple switches** (3 edges):
- Finds pair closest to 180° (straight through) = main line
- Stem = one edge of main line
- Branches = diverging track(s)

**Double slip / Scissors** (4 edges):
- Detects 2 straight-through pairs (both ~180°)
- Stem = first edge of first main line
- Branches = other 3 edges (including second main line)

**Limitations**:
- Uses 17° tolerance for "straight through" detection
- Complex junctions may need manual verification

## CLI Commands

### convert

Convert OSM railway data to PopUpSim topology format.

**Arguments:**
- `input_file`: Input OSM JSON file (required)

**Options:**
- `-o, --output`: Output topology YAML file (default: topology.yaml)
- `-d, --description`: Network description (default: "Railway network")
- `--include-disused`: Include disused/abandoned tracks
- `--include-razed`: Include razed (demolished) tracks

### extract-tracks

Extract track definitions from OSM railway data.

**Arguments:**
- `input_file`: Input OSM JSON file (required)
- `topology`: Topology YAML file path (required)

**Options:**
- `-o, --output`: Output tracks YAML file (default: tracks.yaml)

### plot

Plot PopUpSim railway network.

**Arguments:**
- `topology_file`: Topology YAML file (required)

**Options:**
- `-t, --tracks`: Tracks YAML file for labels
- `-o, --output`: Output image file (PNG)

### animate

Create animated Folium map of train movements.

**Arguments:**
- `sequence_file`: Animation sequence YAML file (required)
- `topology_file`: Topology YAML file (required)
- `tracks_file`: Tracks YAML file (required)
- `routes_file`: Routes YAML file (required)

**Options:**
- `-o, --output`: Output HTML file (default: animation.html)
- `-t, --timestep`: Time between frames in seconds (default: 1.0)

### animate-matplotlib

Create Matplotlib animation of train movements.

**Arguments:**
- `sequence_file`: Animation sequence YAML file (required)
- `topology_file`: Topology YAML file (required)
- `tracks_file`: Tracks YAML file (required)
- `routes_file`: Routes YAML file (required)

**Options:**
- `-o, --output`: Output GIF file (default: animation.gif)
- `-t, --timestep`: Time between frames in seconds (default: 1.0)
- `--fps`: Frames per second (default: 10)

### plot-debug

Plot topology with all node and edge IDs for debugging using Folium.

**Arguments:**
- `topology_file`: Topology YAML file (required)

**Options:**
- `-o, --output`: Output HTML file (default: debug.html)

### plot-folium

Plot network with track types and throats using interactive Folium map.

**Arguments:**
- `topology_file`: Topology YAML file (required)
- `tracks_file`: Tracks YAML file (required)

**Options:**
- `-o, --output`: Output HTML file (default: network.html)
- `--throats`: Throats YAML file (optional, highlights throat edges in cyan)

## Output Structure

### Topology (Yard Detail)

```yaml
metadata:
  description: "Railway network"
  version: "1.0.0"
  level: "microscopic"
  projection: "cartesian"
  crs: "EPSG:3857"
  units:
    length: "meters"
    coordinates: "meters"

nodes:
  node_123:
    type: "switch"
    coords: [950149.41, 5972564.69]  # [x, y] in meters
    switch_config:
      stem: "edge_1"  # Main line (detected by angle analysis)
      branches: ["edge_2", "edge_3"]  # Other edges
      switch_type: "default"  # From OSM
  
  node_entry:
    type: "boundary"  # Entry/exit points for mesoscopic connections
    boundary_type: "entry"  # entry, exit, or both
    coords: [950000.00, 5972000.00]

edges:
  edge_1:
    nodes: ["node_123", "node_456"]
    length: 245.8
    direction: "bi-directional"
    type: "rail"
    status: "active"  # active, disused, or razed
```

### Tracks (Logical Groupings)

```yaml
metadata:
  description: "Yard tracks"
  version: "1.0.0"
  topology_reference: "topology.yaml"

tracks:
  - id: "track_1"
    name: "1"  # From OSM ref tag
    edges: ["edge_1", "edge_2", "edge_3"]
    type: "retrofit"  # User-defined

throats:
  # Simple: any entry → any exit
  - id: "throat_west"
    name: "West Throat"
    nodes: ["switch_1", "switch_2"]
    entries: ["boundary_entry"]
    exits: ["track_1", "track_2"]
```

### Mesoscopic Network (Yard Connections)

```yaml
metadata:
  description: "Multi-yard network"
  version: "1.0.0"
  level: "mesoscopic"
  units: "meters"

yards:
  - id: "haldensleben"
    name: "Haldensleben Yard"
    microscopic_network: "yards/haldensleben.yaml"
    entry_points: ["node_123"]
    exit_points: ["node_789"]

connections:
  - from_yard: "haldensleben"
    from_exit: "node_789"
    to_yard: "magdeburg"
    to_entry: "node_001"
    length: 45000
```

## Track Status

By default, only **active** tracks are converted. Use flags to include:
- `--include-disused`: Include disused/abandoned tracks (status: "disused")
- `--include-razed`: Include razed/demolished tracks (status: "razed")

## Track Status

By default, only **active** tracks are converted. Use flags to include:
- `--include-disused`: Include disused/abandoned tracks (status: "disused")
- `--include-razed`: Include razed/demolished tracks (status: "razed")

## Post-Conversion Manual Steps

After conversion, you must manually:
1. **Add boundary nodes** to topology (entry/exit points for mesoscopic connections)
2. **Set track types** in tracks file (retrofit, storage, collection, etc.)
3. **Define throats** in tracks file (group switches for simplified routing)
4. **Create routes** file for predefined shunting movements

## Animation Sequence Format

For train movement animations, create a sequence YAML file:

```yaml
sequence:
  - type: "route"
    train_id: "train_1"
    route_id: "route_1"
    duration: 120  # seconds
  
  - type: "wait"
    train_id: "train_1"
    duration: 30  # seconds
  
  - type: "route"
    train_id: "train_1"
    route_id: "route_2"
    duration: 90
```

## Python API

```python
from osm2popupsim import convert_osm_to_popupsim
import json
import yaml

# Load OSM data
with open('railway_data.json') as f:
    osm_data = json.load(f)

# Convert to PopUpSim format
popupsim_data = convert_osm_to_popupsim(
    osm_data,
    description="My Yard",
    include_disused=False,
    include_razed=False
)

# Save to YAML
with open('topology.yaml', 'w') as f:
    yaml.dump(popupsim_data, f, default_flow_style=False, sort_keys=False)
```

## Complete Workflow

```bash
# 1. Extract railway data from OSM
uv run --group osm-extractor osm-extractor extract \
  "47.37,8.54,47.39,8.56" -t bbox -o railway_data.json --project --clip

# 2. Convert to PopUpSim topology
uv run osm2popupsim convert railway_data.json -o topology.yaml -d "My Yard"

# 3. Extract tracks
uv run osm2popupsim extract-tracks railway_data.json topology.yaml -o tracks.yaml

# 4. Plot network
uv run osm2popupsim plot topology.yaml -t tracks.yaml -o network.png

# 5. Manually edit tracks.yaml to add track types and throats
# 6. Create routes.yaml with predefined routes
# 7. Create sequence.yaml for animation
# 8. Generate animation
uv run osm2popupsim animate sequence.yaml topology.yaml tracks.yaml routes.yaml
```
