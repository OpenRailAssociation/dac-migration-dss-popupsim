# 9. MVP Deployment

## Overview

PopUpSim MVP is a desktop application with local execution.

## Deployment Model

```
Developer Laptop
├── Python 3.13+
├── popupsim/backend/src/
│   └── contexts/
│       ├── configuration/
│       ├── retrofit_workflow/
│       ├── railway_infrastructure/
│       └── external_trains/
├── Data/examples/
└── output/
```

## Installation

```bash
# 1. Clone repository
git clone https://github.com/open-rail-association/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# 2. Install uv
pip install uv

# 3. Install dependencies
uv sync

# 4. Verify installation
uv run pytest
```

## Running Simulations

```bash
# Basic usage
uv run python popupsim/backend/src/main.py --config Data/examples/two_trains/

# With custom output
uv run python popupsim/backend/src/main.py \
  --config Data/examples/medium_scenario/ \
  --output results/my_test/
```

## Directory Structure

```
popupsim/backend/src/
├── main.py                     # Entry point
├── application/
│   └── simulation_service.py   # Orchestration
└── contexts/
    ├── configuration/
    ├── retrofit_workflow/
    ├── railway_infrastructure/
    └── external_trains/
```

## Requirements

- **Python:** 3.13+
- **OS:** Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **RAM:** Varies by scenario size
- **Disk:** ~500MB for installation

## Output

Results are written to `output/` directory:

```
output/
├── wagon_events.csv
├── locomotive_events.csv
├── workshop_events.csv
└── charts/
    ├── throughput.png
    └── utilization.png
```

## Development Commands

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run mypy popupsim/backend/src/

# Static analysis
uv run pylint popupsim/backend/src/

# All checks
uv run ruff format . && \
uv run ruff check . && \
uv run mypy popupsim/backend/src/ && \
uv run pylint popupsim/backend/src/ && \
uv run pytest
```

---
