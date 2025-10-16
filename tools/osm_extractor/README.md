# OSM Railway Data Extractor

A Python tool for extracting, processing, and visualizing railway infrastructure data from OpenStreetMap (OSM) using the Overpass API.

## Features

- **Extract** railway data from OSM (tracks, switches, buffer stops)
- **Clip** data to precise geographic boundaries (bounding box or polygon)
- **Project** coordinates to Cartesian system (elliptical Mercator)
- **Visualize** railway networks with specialized node markers
- **Robust** error handling with custom exceptions
- **Efficient** geometry operations using Shapely

## Installation

From the project root:

```bash
uv sync --group osm-extractor
```

## Testing

Run the test suite:

```bash
# From project root
uv run pytest tools/osm_extractor/tests/ -v

# Or from osm_extractor directory
cd tools/osm_extractor
uv run pytest tests/ -v
```

### Coverage

Run tests with coverage reporting:

```bash
# Unix/Linux/macOS
./tools/osm_extractor/run_tests.sh

# Windows
tools\osm_extractor\run_tests.bat

# Manual (from project root)
uv run pytest tools/osm_extractor/tests/ \
    --cov=tools/osm_extractor/src/osm_extractor \
    --cov-report=term-missing \
    --cov-report=html:tools/osm_extractor/htmlcov \
    -v
```

Coverage reports:
- **Terminal**: Shows coverage summary with missing lines
- **HTML**: `tools/osm_extractor/htmlcov/index.html`
- **XML**: `tools/osm_extractor/coverage.xml`

### Test Structure

- **Unit tests**: Fast, isolated tests for individual functions
  - `test_models.py`: Data model validation
  - `test_projection.py`: Coordinate projection
  - `test_geometry.py`: Geometry operations
  - `test_exceptions.py`: Exception hierarchy
  - `test_projector.py`: Projector class
- **Integration tests**: Tests with mocked external dependencies
  - `test_extractor_integration.py`: OSM extraction with mocked API
  - `test_clipper_integration.py`: Data clipping operations
  - `test_plotter_integration.py`: Visualization generation
  - `test_cli_integration.py`: CLI commands end-to-end

## CLI Usage

The tool provides a clean command-line interface with four main commands:

### 1. Extract

Extract railway data from OSM within a specified boundary.

**Bounding Box:**
```bash
uv run --group osm-extractor osm-extractor extract \
  "47.37,8.54,47.39,8.56" \
  -t bbox \
  -o raw_data.json
```

**Polygon:**
```bash
uv run --group osm-extractor osm-extractor extract \
  "52.286,11.404 52.281,11.416 52.280,11.416 52.281,11.413 52.282,11.409 52.284,11.407 52.286,11.404" \
  -t polygon \
  -o raw_data.json
```

**Options:**
- `-t, --type`: Boundary type (`bbox` or `polygon`)
- `-o, --output`: Output JSON file (default: `railway_data.json`)
- `-r, --railway-types`: Comma-separated railway types (default: `rail,siding,yard,spur`)
- `-n, --node-types`: Comma-separated node types (default: `switch,buffer_stop`)
- `--timeout`: Request timeout in seconds (default: 60)

### 2. Clip

Clip extracted data to remove elements outside the boundary.

```bash
uv run --group osm-extractor osm-extractor clip \
  raw_data.json \
  -o clipped_data.json \
  -c "52.286,11.404 52.281,11.416 52.280,11.416" \
  -t polygon
```

**Options:**
- `-o, --output`: Output JSON file (default: `clipped.json`)
- `-c, --coordinates`: Boundary coordinates
- `-t, --type`: Boundary type (`bbox` or `polygon`)

### 3. Project

Project geographic coordinates (lat/lon) to Cartesian coordinates (x/y).

```bash
uv run --group osm-extractor osm-extractor project \
  clipped_data.json \
  -o projected_data.json
```

**Options:**
- `-o, --output`: Output JSON file (default: `projected.json`)

### 4. Plot

Visualize railway data with automatic coordinate system detection.

```bash
uv run --group osm-extractor osm-extractor plot \
  projected_data.json \
  -o railway_map.png \
  -t "Railway Network"
```

**With boundary overlay (debug):**
```bash
uv run --group osm-extractor osm-extractor plot \
  clipped_data.json \
  -o debug_map.png \
  --show-boundary \
  -c "52.286,11.404 52.281,11.416" \
  --boundary-type polygon
```

**Options:**
- `-o, --output`: Output image file (default: `railway_plot.png`)
- `-t, --title`: Plot title
- `--no-nodes`: Hide node markers
- `--show-boundary`: Show boundary overlay
- `-c, --coordinates`: Boundary coordinates (required with `--show-boundary`)
- `--boundary-type`: Boundary type for overlay

### 5. Info

Show available railway and node types.

```bash
uv run --group osm-extractor osm-extractor info
```

## Complete Pipeline Example

Extract, clip, project, and visualize railway data for Haldensleben station:

```bash
# Define coordinates
COORDS="52.286,11.404 52.281,11.416 52.280,11.416 52.281,11.413 52.282,11.409 52.284,11.407 52.286,11.404"

# 1. Extract
uv run --group osm-extractor osm-extractor extract \
  "$COORDS" -t polygon -o haldensleben_raw.json

# 2. Clip
uv run --group osm-extractor osm-extractor clip \
  haldensleben_raw.json -o haldensleben_clipped.json \
  -c "$COORDS" -t polygon

# 3. Project
uv run --group osm-extractor osm-extractor project \
  haldensleben_clipped.json -o haldensleben_projected.json

# 4. Plot (geographic)
uv run --group osm-extractor osm-extractor plot \
  haldensleben_clipped.json -o haldensleben_geo.png \
  -t "Haldensleben Station (Geographic)"

# 5. Plot (projected with boundary)
uv run --group osm-extractor osm-extractor plot \
  haldensleben_projected.json -o haldensleben_proj.png \
  -t "Haldensleben Station (Projected)" \
  --show-boundary -c "$COORDS" --boundary-type polygon
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

### Node Markers

- **Switches**: Red X (size 100)
- **Buffer Stops**: Orange square (size 80)
- **Other Nodes**: Gray circle (size 20)

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
