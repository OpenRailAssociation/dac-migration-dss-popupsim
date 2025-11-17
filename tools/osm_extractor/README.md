# OSM Railway Data Extractor

A Python tool for extracting, processing, and visualizing railway infrastructure data from OpenStreetMap (OSM) using the Overpass API.

## Features

- **Extract** railway data from OSM (active and disused tracks, switches, buffer stops)
- **Clip** data to precise geographic boundaries (bounding box or polygon)
- **Project** coordinates to Cartesian system (elliptical Mercator)
- **Visualize** railway networks with customizable display options
- **Hierarchical output** format with nodes, edges, and ways
- **Robust** error handling with custom exceptions
- **Efficient** geometry operations using Shapely

## Installation

From the project root:

```bash
uv sync --group osm-extractor
```

## CLI Usage

The tool provides a clean command-line interface with two main commands:

### 1. Extract

Extract railway data from OSM within a specified boundary.

**Bounding Box:**
```bash
uv run osm-extractor extract \
  "47.37,8.54,47.39,8.56" \
  -t bbox \
  -o railway_data.json
```

**Polygon:**
```bash
uv run osm-extractor extract \
  "52.276235,11.426263 52.276402,11.426447 52.278037,11.421849 52.280368,11.416562" \
  -t polygon \
  -o railway_data.json
```

**With projection and clipping:**
```bash
uv run osm-extractor extract \
  "52.276235,11.426263 52.276402,11.426447 52.278037,11.421849 52.280368,11.416562" \
  -t polygon \
  -o railway_data.json \
  --project \
  --clip
```

**Options:**
- `-o, --output`: Output JSON file (default: `railway_data.json`)
- `-t, --type`: Boundary type (`bbox` or `polygon`, default: `bbox`)
- `-r, --railway-types`: Comma-separated railway types (default: `rail,siding,yard,spur`)
- `-n, --node-types`: Comma-separated node types (default: `switch,buffer_stop`)
- `--timeout`: Request timeout in seconds (default: 180)
- `--include-disused`: Include disused/abandoned tracks
- `--include-razed`: Include razed (demolished) tracks
- `--project`: Project to Cartesian coordinates (elliptical Mercator)
- `--clip`: Clip geometry to boundary (removes segments outside)
- `--plot`: Show plot after extraction

**Note:** By default, only active tracks are extracted. Use `--include-disused` and `--include-razed` flags to include inactive infrastructure. Orphaned nodes (not connected to any ways) are automatically removed.

### 2. Plot

Visualize railway data with automatic coordinate system detection and customizable display options.

**Basic plot:**
```bash
uv run osm-extractor plot railway_data.json -o railway_map.png
```

**With track labels:**
```bash
uv run osm-extractor plot railway_data.json -o railway_map.png --labels
```

**With switch labels:**
```bash
uv run osm-extractor plot railway_data.json -o railway_map.png --switch-labels
```

**Options:**
- `-o, --output`: Output image file (PNG)
- `--labels`: Show track labels from railway:track_ref tags
- `--switch-labels`: Show switch labels (ref or ID)

**Track Colors:**
- **Blue**: Active tracks
- **Red**: Disused/abandoned tracks

**Node Markers:**
- **Red X**: Switches
- **Orange square**: Buffer stops
- **Gray circle**: Other nodes

## Complete Pipeline Example

```bash
# Extract, project, and clip in one command
uv run osm-extractor extract \
  "52.276235,11.426263 52.276402,11.426447 52.278037,11.421849 52.280368,11.416562" \
  -t polygon \
  -o railway_data.json \
  --project \
  --clip

# Visualize with labels
uv run osm-extractor plot railway_data.json \
  -o network.png \
  --labels \
  --switch-labels
```

## Python API

```python
from osm_extractor import (
    OSMRailwayExtractor,
    BoundingBox,
    Polygon,
    plot_railway_data,
)

# Create extractor
extractor = OSMRailwayExtractor(
    railway_types=['rail', 'siding', 'yard'],
    node_types=['switch', 'buffer_stop']
)

# Define boundary
bbox = BoundingBox(south=47.37, west=8.54, north=47.39, east=8.56)

# Extract data
data = extractor.extract(bbox, filter_geometry=True)

# Visualize
fig = plot_railway_data(data, boundary=bbox, title="Railway Network")
fig.savefig('output.png')
```

## Exception Handling

The tool provides specific exceptions for different error types:

- `OSMExtractorError`: Base exception
- `ExtractionError`: Data extraction errors
  - `RateLimitError`: API rate limit exceeded
  - `QueryTimeoutError`: Query timeout
  - `InvalidQueryError`: Invalid query syntax
- `GeometryError`: Geometry operation errors
- `ProjectionError`: Coordinate projection errors
- `PlottingError`: Visualization errors

## Data Format

### Input/Output JSON Structure

```json
{
  "elements": [
    {
      "type": "node",
      "id": 123456,
      "lat": 52.286,
      "lon": 11.404,
      "tags": {"railway": "switch"}
    },
    {
      "type": "way",
      "id": 789012,
      "geometry": [
        {"lat": 52.286, "lon": 11.404},
        {"lat": 52.287, "lon": 11.405}
      ],
      "tags": {"railway": "rail"}
    }
  ]
}
```

### Projected Data (additional fields)

```json
{
  "type": "node",
  "lat": 52.286,
  "lon": 11.404,
  "x": 1268234.56,
  "y": 6876543.21
}
```

## Visualization

The plotter automatically detects coordinate systems:
- **Geographic**: Uses lat/lon, shows "Longitude" and "Latitude" labels
- **Projected**: Uses x/y, shows "X (meters)" and "Y (meters)" labels

### Display Elements

**Node Markers:**
- **Switches**: Red X (size 100)
- **Buffer Stops**: Orange square (size 80)
- **Other Nodes**: Gray circle (size 20)

**Track Colors:**
- **Blue**: Active tracks (railway=rail, usage=main/industrial/freight)
- **Red**: Disused/abandoned tracks (disused:railway, abandoned:railway, usage=disused/abandoned)

**Labels:**
- **Track labels**: White boxes with track reference (railway:track_ref)
- **Switch labels**: Yellow boxes with switch ID

## Development

### Running Tests

```bash
# All tests
uv run pytest tools/osm_extractor/tests/

# Unit tests only
uv run pytest tools/osm_extractor/tests/ -m unit

# Integration tests only
uv run pytest tools/osm_extractor/tests/ -m integration

# Specific test file
uv run pytest tools/osm_extractor/tests/test_models.py

# Specific test
uv run pytest tools/osm_extractor/tests/test_models.py::TestBoundingBox::test_creation
```

### Code Quality

```bash
# Format code
uv run ruff format tools/osm_extractor/

# Lint code
uv run ruff check tools/osm_extractor/
```

## License

Apache 2.0
