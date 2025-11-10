# 6. MVP Technology Stack

## Overview

**Note:** See [Architecture Section 7.10](../architecture/07-deployment.md#710-technology-stack-summary) for complete technology stack.

This document provides detailed information about technology choices for the MVP.

## Core Technologies

### Python 3.13+
- **Purpose**: Main programming language
- **Rationale**: Modern type system, excellent ecosystem, rapid development
- **Key Features**: Type hints, dataclasses, pattern matching
- **Installation**: Via uv package manager

### SimPy
- **Purpose**: Discrete event simulation engine
- **Version**: Latest stable
- **Rationale**: Mature, well-documented, Python-native
- **Key Features**: Environment, Resource, Process
- **Documentation**: https://simpy.readthedocs.io/

### Pydantic 2.0+
- **Purpose**: Data validation and settings management
- **Rationale**: Type-safe, comprehensive validation, excellent error messages
- **Key Features**: BaseModel, field validators, JSON schema
- **Migration**: Uses v2 syntax (@field_validator, not @validator)

### Matplotlib
- **Purpose**: Data visualization and charting
- **Rationale**: Standard Python plotting library, extensive chart types
- **Key Features**: Line charts, bar charts, histograms
- **Output**: PNG files

### Pandas
- **Purpose**: Data processing and CSV handling
- **Rationale**: Industry standard for data manipulation
- **Key Features**: DataFrame, CSV read/write, data aggregation

## Development Tools

### uv
- **Purpose**: Fast Python package manager
- **Rationale**: Faster than pip, better dependency resolution
- **Commands**:
  - `uv sync`: Install dependencies
  - `uv run`: Run commands in virtual environment
  - `uv pip install`: Install packages

### Ruff
- **Purpose**: Code formatting and linting
- **Rationale**: Fast, replaces Black + Flake8 + isort
- **Commands**:
  - `uv run ruff format .`: Format code
  - `uv run ruff check .`: Lint code
  - `uv run ruff check --fix .`: Auto-fix issues

### MyPy
- **Purpose**: Static type checking
- **Rationale**: Enforces type hints, catches type errors
- **Configuration**: `disallow_untyped_defs = true` in pyproject.toml
- **Command**: `uv run mypy backend/src/`

### Pylint
- **Purpose**: Static code analysis
- **Rationale**: Catches code quality issues, enforces standards
- **Command**: `uv run pylint backend/src/`

### Pytest
- **Purpose**: Testing framework
- **Rationale**: Standard Python testing tool, excellent plugin ecosystem
- **Key Features**: Fixtures, parametrize, coverage
- **Command**: `uv run pytest`

### pytest-cov
- **Purpose**: Code coverage measurement
- **Command**: `uv run pytest --cov=backend/src`

## Technology Decisions

### Why SimPy over alternatives?

| Aspect | SimPy | Salabim | Custom DES |
|--------|-------|---------|------------|
| **Learning Curve** | Low | Medium | High |
| **Documentation** | Excellent | Good | N/A |
| **Community** | Large | Small | N/A |
| **Performance** | Good | Better | Best |
| **MVP Fit** | ✅ Perfect | ⚠️ Overkill | ❌ Too slow |

**Decision**: SimPy for MVP, thin adapter allows future replacement.

### Why Pydantic 2.0?

| Feature | Pydantic | Dataclasses | attrs |
|---------|----------|-------------|-------|
| **Validation** | ✅ Built-in | ❌ Manual | ⚠️ Plugin |
| **Type Safety** | ✅ Runtime | ✅ Static only | ✅ Runtime |
| **JSON Schema** | ✅ Auto-gen | ❌ No | ❌ No |
| **Error Messages** | ✅ Detailed | ❌ Basic | ⚠️ Good |

**Decision**: Pydantic for comprehensive validation and error reporting.

### Why Matplotlib over alternatives?

| Aspect | Matplotlib | Plotly | Seaborn |
|--------|------------|--------|---------|
| **Static Charts** | ✅ Excellent | ⚠️ Overkill | ✅ Good |
| **File Output** | ✅ PNG/PDF | ⚠️ HTML | ✅ PNG/PDF |
| **Simplicity** | ✅ Simple | ❌ Complex | ✅ Simple |
| **Dependencies** | ✅ Minimal | ❌ Heavy | ⚠️ Medium |

**Decision**: Matplotlib for simple, static charts with minimal dependencies.

## Dependency Management

### pyproject.toml Structure

```toml
[project]
name = "popupsim"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "simpy>=4.1.1",
    "pydantic>=2.0.0",
    "matplotlib>=3.8.0",
    "pandas>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
    "pylint>=3.0.0",
    "ruff>=0.1.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocs-mermaid2-plugin>=1.1.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.mypy]
python_version = "3.13"
disallow_untyped_defs = true
strict = true

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

### Installation Commands

```bash
# Install core dependencies
uv sync

# Install with dev dependencies
uv sync --group dev

# Install with docs dependencies
uv sync --group docs

# Install all groups
uv sync --all-groups
```

## Type Hints Requirements

All code must include explicit type annotations:

```python
from typing import Optional

# Functions
def calculate_throughput(
    wagons: list[Wagon], 
    duration_hours: float
) -> float:
    return len(wagons) / duration_hours

# Methods
class Workshop:
    def get_available_track(self) -> Optional[WorkshopTrack]:
        for track in self.tracks:
            if track.is_available():
                return track
        return None

# Test methods
def test_throughput_calculation() -> None:
    wagons = [Wagon(id="W1"), Wagon(id="W2")]
    result = calculate_throughput(wagons, 1.0)
    assert result == 2.0

# Fixtures
import pytest

@pytest.fixture
def sample_workshop() -> Workshop:
    return Workshop(tracks=[])
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Python Backend

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies
        run: uv sync --group dev
      
      - name: Format check
        run: uv run ruff format --check .
      
      - name: Lint
        run: uv run ruff check .
      
      - name: Type check
        run: uv run mypy backend/src/
      
      - name: Static analysis
        run: uv run pylint backend/src/
      
      - name: Test
        run: uv run pytest --cov=backend/src
```

## Not in MVP

### Excluded Technologies
- ❌ **FastAPI**: No web API needed
- ❌ **Vue.js**: No web frontend needed
- ❌ **PostgreSQL**: No database needed
- ❌ **Redis**: No caching needed
- ❌ **Docker**: Desktop application only
- ❌ **Kubernetes**: No container orchestration needed

### Post-MVP Additions
- **FastAPI**: For web API in full version
- **PostgreSQL**: For persistent storage
- **Docker**: For containerized deployment
- **Celery**: For async task processing
