# OSM Extractor Testing Guide

## Test Suite Overview

The osm_extractor has a comprehensive test suite with **70 tests** covering both unit and integration testing.

### Test Coverage: 81.73%

| Module | Coverage | Notes |
|--------|----------|-------|
| `__init__.py` | 100% | Package initialization |
| `clipper.py` | 100% | Data clipping operations |
| `exceptions.py` | 100% | Exception hierarchy |
| `extractor.py` | 100% | OSM data extraction |
| `models.py` | 100% | Data models |
| `projection.py` | 100% | Coordinate projection |
| `projector.py` | 100% | Projection orchestration |
| `plotter.py` | 98.81% | Visualization |
| `geometry.py` | 94.74% | Geometry operations |
| `cli.py` | 91.15% | CLI commands |
| `visualize.py` | 15.84% | Visualization utilities (legacy) |

## Running Tests

### All Tests

```bash
# From project root
uv run pytest tools/osm_extractor/tests/ -v

# From osm_extractor directory
cd tools/osm_extractor
uv run pytest tests/ -v
```

### By Test Type

```bash
# Unit tests only
uv run pytest tools/osm_extractor/tests/ -m unit -v

# Integration tests only
uv run pytest tools/osm_extractor/tests/ -m integration -v
```

### Specific Test Files

```bash
# Models
uv run pytest tools/osm_extractor/tests/test_models.py -v

# Extractor integration
uv run pytest tools/osm_extractor/tests/test_extractor_integration.py -v

# CLI integration
uv run pytest tools/osm_extractor/tests/test_cli_integration.py -v
```

## Coverage Reports

### Quick Coverage

```bash
uv run pytest tools/osm_extractor/tests/ \
    --cov=tools/osm_extractor/src/osm_extractor \
    --cov-report=term-missing \
    -v
```

### Full Coverage with HTML Report

**Unix/Linux/macOS:**
```bash
./tools/osm_extractor/run_tests.sh
```

**Windows:**
```cmd
tools\osm_extractor\run_tests.bat
```

**Manual:**
```bash
uv run pytest tools/osm_extractor/tests/ \
    --cov=tools/osm_extractor/src/osm_extractor \
    --cov-report=term-missing \
    --cov-report=html:tools/osm_extractor/htmlcov \
    --cov-report=xml:tools/osm_extractor/coverage.xml \
    -v
```

### Coverage Output Locations

- **Terminal**: Inline summary with missing lines
- **HTML**: `tools/osm_extractor/htmlcov/index.html`
- **XML**: `tools/osm_extractor/coverage.xml`

## Test Structure

### Unit Tests (28 tests)

Fast, isolated tests for individual functions:

- **test_models.py** (6 tests): BoundingBox and Polygon validation
- **test_projection.py** (4 tests): Coordinate projection math
- **test_geometry.py** (4 tests): Geometry filtering operations
- **test_geometry_edge_cases.py** (3 tests): Edge cases for geometry
- **test_exceptions.py** (8 tests): Exception hierarchy
- **test_projector.py** (3 tests): Projector class

### Integration Tests (42 tests)

Tests with mocked external dependencies:

- **test_extractor_integration.py** (11 tests)
  - Successful extraction (bbox, polygon)
  - Geometry filtering
  - Error handling (rate limit, timeout, invalid query)
  - Query building
  - Custom types configuration

- **test_clipper_integration.py** (4 tests)
  - Clipping with bbox and polygon
  - File I/O operations
  - Error handling

- **test_plotter_integration.py** (6 tests)
  - Geographic and projected data plotting
  - Boundary overlays
  - Node marker visibility
  - File I/O operations
  - Error handling

- **test_plotter_edge_cases.py** (4 tests)
  - Boundary rendering (bbox, polygon)
  - Geographic vs projected data
  - Node type markers

- **test_cli_integration.py** (6 tests)
  - Extract command (bbox, polygon)
  - Clip command
  - Project command
  - Plot command
  - Info command

- **test_cli_error_paths.py** (10 tests)
  - Invalid coordinates
  - Extraction errors
  - Geometry errors
  - Projection errors
  - Plotting errors

- **test_projector_edge_cases.py** (2 tests)
  - Invalid JSON handling
  - Missing file handling

## Test Fixtures

Defined in `conftest.py`:

- `sample_bbox`: BoundingBox(47.37, 8.54, 47.39, 8.56)
- `sample_polygon`: Polygon with 4 coordinates
- `sample_osm_data`: OSM JSON with node and way
- `mock_overpass_response`: Mocked overpy.Overpass response

## Continuous Integration

### Pre-commit Hook

Tests run automatically on commit via pre-commit hooks.

### Manual Pre-commit Run

```bash
uv run pre-commit run --all-files
```

## Coverage Goals

| Priority | Module | Current | Target | Status |
|----------|--------|---------|--------|--------|
| ✅ High | `cli.py` | 91% | 85% | **Achieved** |
| ✅ High | `plotter.py` | 99% | 95% | **Achieved** |
| ✅ High | `projector.py` | 100% | 95% | **Achieved** |
| ✅ Medium | `geometry.py` | 95% | 95% | **Achieved** |
| Low | `visualize.py` | 16% | 50% | Legacy module, consider refactor |

## Adding New Tests

### Unit Test Template

```python
"""Unit tests for new_module."""

import pytest
from osm_extractor.new_module import new_function


class TestNewFunction:
    """Unit tests for new_function."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = new_function(input_data)
        assert result == expected_output
```

### Integration Test Template

```python
"""Integration tests for new_module."""

import pytest
from unittest.mock import patch

from osm_extractor.new_module import NewClass


@pytest.mark.integration
class TestNewClassIntegration:
    """Integration tests for NewClass."""

    @patch('osm_extractor.new_module.external_dependency')
    def test_with_mock(self, mock_dep):
        """Test with mocked external dependency."""
        mock_dep.return_value = mock_data
        instance = NewClass()
        result = instance.method()
        assert result == expected
```

## Troubleshooting

### Matplotlib Backend Error

If you see `TclError: Can't find a usable init.tcl`, matplotlib is trying to use a GUI backend. This is fixed in `conftest.py` with:

```python
import matplotlib
matplotlib.use('Agg')
```

### Import Errors

Ensure dependencies are installed:

```bash
uv sync --group osm-extractor
```

### Coverage Not Showing

Verify coverage configuration in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["backend/src", "tools/osm_extractor/src"]
omit = ["backend/tests/*", "tools/osm_extractor/tests/*"]
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External APIs**: Use `@patch` for Overpass API calls
3. **Use Fixtures**: Reuse common test data via fixtures
4. **Descriptive Names**: Test names should describe what they test
5. **Fast Tests**: Keep unit tests under 100ms
6. **Clean Up**: Use `tempfile.TemporaryDirectory()` for file tests
7. **Mark Tests**: Use `@pytest.mark.integration` for integration tests
