# 6. MVP Technology Stack

## Core Technologies

| Technology | Version | Purpose | Location |
|------------|---------|---------|----------|
| **Python** | 3.13+ | Runtime | All contexts |
| **SimPy** | 4.1.2+ | Discrete event simulation | Retrofit Workflow |
| **Pydantic** | 2.13.4+ | Data validation | Configuration |
| **Typer** | 0.26.8+ | CLI | `main.py` |
| **Plotly** | 6.9+ | Visualization | Frontend dashboard |
| **Streamlit** | 1.58+ | Dashboard UI | Frontend |
| **Pandas** | 3.0.5 (pinned) | CSV processing | Configuration, Frontend |

> Versions reflect `pyproject.toml` at time of writing; check that file for the current pins.

## Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **uv** | Package manager | `pyproject.toml` |
| **Ruff** | Formatting & linting | `pyproject.toml` |
| **MyPy** | Type checking | `disallow_untyped_defs = true` |
| **Pylint** | Static analysis | `pyproject.toml` |
| **Pytest** | Testing | Run `uv run pytest` |
| **Typer** | CLI framework | `run` / `optimize` commands |

## Context-Specific Technologies

### Configuration Context
- **Pydantic 2.0+** - Model validation
- **Pandas** - CSV parsing
- **JSON** - File loading

### Retrofit Workflow Context
- **SimPy** - Simulation engine
- **Dataclasses** - Domain entities
- **Pandas** - CSV export of events/metrics

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
