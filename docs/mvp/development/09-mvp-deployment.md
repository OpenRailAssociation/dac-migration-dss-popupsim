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
uv run python popupsim/backend/src/main.py run \
  --scenario Data/examples/ten_trains_two_days_baseline/ --output output/

# Optimize task priorities
uv run python popupsim/backend/src/main.py optimize \
  --scenario Data/examples/ten_trains_two_days_baseline/

# View results in the dashboard (separate terminal)
uv run streamlit run popupsim/frontend/dashboard.py
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

Results are written as flat CSV/JSON files into the `--output` directory (no chart images):

```
output/
├── summary_metrics.json
├── wagon_journey.csv
├── rejected_wagons.csv
├── locomotive_movements.csv
├── workshop_metrics.csv
├── resource_states.csv
├── resource_locations.csv
├── resource_processes.csv
├── events.log
└── scenario/                # copy of the input scenario
```

See [Running the Simulation](../../tutorial/10-running-simulation.md#output-files) for the
full file list and columns.

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
