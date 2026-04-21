# 6. MVP Technology Stack

## Core Technologies

| Technology | Version | Purpose | Location |
|------------|---------|---------|----------|
| **Python** | 3.13+ | Runtime | All contexts |
| **SimPy** | 4.0.1+ | Discrete event simulation | Retrofit Workflow |
| **Pydantic** | 2.0+ | Data validation | Configuration |
| **Plotly** | 6.5+ | Visualization | Frontend dashboard |
| **Streamlit** | 1.52+ | Dashboard UI | Frontend |
| **Pandas** | 2.0+ | CSV processing | Configuration, Frontend |

## Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **uv** | Package manager | `pyproject.toml` |
| **Ruff** | Formatting & linting | `pyproject.toml` |
| **MyPy** | Type checking | `disallow_untyped_defs = true` |
| **Pylint** | Static analysis | `pyproject.toml` |
| **Pytest** | Testing | 374 tests passing |

## Context-Specific Technologies

### Configuration Context
- **Pydantic 2.0+** - Model validation
- **Pandas** - CSV parsing
- **JSON** - File loading

### Retrofit Workflow Context
- **SimPy** - Simulation engine
- **Matplotlib** - Chart generation
- **Dataclasses** - Domain entities

### Railway Infrastructure Context
- **Dataclasses** - Track aggregates
- **Enums** - Track types

### External Trains Context
- **SimPy** - Event scheduling
- **Dataclasses** - Events

## Installation

```bash
# Install uv
pip install uv

# Install dependencies
uv sync

# Verify installation
uv run pytest
```

## Dependencies

See `pyproject.toml` for complete dependency list.

---
