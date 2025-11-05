# 9. MVP Deployment

## Overview

**Note:** See [Architecture Section 7](../architecture/07-deployment.md) for detailed deployment view.

This document describes deployment and installation for the MVP.

## Installation

### Prerequisites
- **Python 3.13+**
- **uv** package manager
- **Git**

### Quick Start

```bash
# Clone repository
git clone https://github.com/OpenRailAssociation/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# Install dependencies
uv sync

# Run example simulation
uv run python popupsim/backend/src/main.py --config config/examples/small_scenario/scenario.json
```

### Development Setup

```bash
# Install with dev dependencies
uv sync --group dev

# Install pre-commit hooks
uv run python setup/dev/set_commit_msg_hooks.py

# Run all checks
uv run ruff format . && uv run ruff check . && uv run mypy backend/src/ && uv run pylint backend/src/ && uv run pytest
```

## Deployment Architecture

### Desktop Application

```
┌─────────────────────────────────────┐
│       Developer Laptop              │
│  ┌───────────────────────────────┐  │
│  │   PopUpSim MVP                │  │
│  │   Python 3.13+ + SimPy        │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │   File System                 │  │
│  │   config/ → results/          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Runtime Requirements
- **RAM**: To be measured during implementation
- **Disk**: ~500MB for installation and data
- **CPU**: Standard business laptop
- **OS**: Windows, macOS, Linux

## Configuration Management

### Configuration Files

```
config/
├── scenario.json          # Main scenario configuration
├── train_schedule.csv     # Train arrival schedule
├── workshop_tracks.csv    # Workshop track definitions (optional)
└── routes.csv            # Route definitions (optional)
```

### Environment Variables

```bash
# Optional: Set custom config path
export POPUPSIM_CONFIG_PATH=/path/to/config

# Optional: Set custom output path
export POPUPSIM_OUTPUT_PATH=/path/to/results

# Optional: Enable debug logging
export POPUPSIM_LOG_LEVEL=DEBUG
```

## Execution

### Command Line Interface

```bash
# Basic execution
uv run python popupsim/backend/src/main.py --config scenario.json

# With custom output path
uv run python popupsim/backend/src/main.py --config scenario.json --output results/

# With verbose logging
uv run python popupsim/backend/src/main.py --config scenario.json --verbose

# Dry run (validate config only)
uv run python popupsim/backend/src/main.py --config scenario.json --dry-run
```

### Python API

```python
from popupsim.application import PopUpSimApplication

# Create application
app = PopUpSimApplication()

# Run simulation
results = app.run_complete_analysis("config/scenario.json")

# Access results
print(f"Wagons processed: {results.simulation_results.total_wagons_processed}")
print(f"Throughput: {results.simulation_results.throughput_per_hour} wagons/hour")
```

## Output Management

### Result Files

```
results/
├── summary.csv           # KPI summary
├── wagons.csv           # Detailed wagon data
├── track_metrics.csv    # Track utilization metrics
├── events.csv           # Event log
├── results.json         # Complete results (JSON)
└── charts/              # Visualizations
    ├── throughput.png
    ├── waiting_times.png
    └── utilization.png
```

### Output Locations

Default: `results/` in current directory

Custom: Use `--output` flag or `POPUPSIM_OUTPUT_PATH` environment variable

## Logging

### Log Configuration

```python
# Default logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('popupsim.log'),
        logging.StreamHandler()
    ]
)
```

### Log Levels
- **DEBUG**: Detailed simulation events
- **INFO**: Normal execution flow
- **WARNING**: Potential issues
- **ERROR**: Errors with recovery
- **CRITICAL**: Fatal errors

## Error Handling

### Common Errors

**Configuration Error**:
```bash
ERROR - Configuration validation failed: end_date must be after start_date
```
**Solution**: Fix dates in scenario.json

**File Not Found**:
```bash
ERROR - Train schedule file not found: train_schedule.csv
```
**Solution**: Ensure file exists in config directory

**Simulation Error**:
```bash
ERROR - Simulation failed: Insufficient track capacity
```
**Solution**: Increase track capacity or reduce wagon count

## Distribution

### Packaging Options

**Option 1: Source Distribution**
```bash
# Users install from source
git clone <repo>
uv sync
```

**Option 2: Wheel Distribution**
```bash
# Build wheel
uv build

# Install wheel
uv pip install dist/popupsim-0.1.0-py3-none-any.whl
```

**Option 3: Executable (Post-MVP)**
```bash
# Create standalone executable with PyInstaller
pyinstaller --onefile popupsim/backend/src/main.py
```

## Platform-Specific Notes

### Windows
- Use backslashes in paths: `config\scenario.json`
- PowerShell recommended over CMD

### macOS
- May need to allow Python in Security & Privacy settings
- Use forward slashes in paths: `config/scenario.json`

### Linux
- Ensure Python 3.13+ is installed
- May need to install system dependencies for Matplotlib

## Troubleshooting

### Python Version Issues
```bash
# Check Python version
python --version  # Should be 3.13+

# If wrong version, use uv to install correct version
uv python install 3.13
```

### Dependency Issues
```bash
# Clear cache and reinstall
uv cache clean
uv sync --reinstall
```

### Permission Issues
```bash
# Ensure write permissions for output directory
chmod +w results/
```

## Performance Monitoring

### Resource Usage

Monitor during execution:
```bash
# Linux/macOS
top -p $(pgrep -f popupsim)

# Windows
tasklist | findstr python
```

### Profiling

```python
import cProfile
import pstats

# Profile simulation
cProfile.run('app.run_complete_analysis("scenario.json")', 'profile_stats')

# View results
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Migration Path

### Post-MVP Deployment Options
- **Docker**: Containerized deployment
- **Web Service**: FastAPI + Uvicorn
- **Cloud**: AWS/Azure/GCP deployment
- **CI/CD**: Automated testing and deployment
