# PopUpSim - DAC Migration Simulation Tool

[![Badge Stage 1](https://openrailassociation.org/badges/openrail-project-stage-1.svg)](https://link.openrailassociation.org/stage-1)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Backend](https://img.shields.io/badge/Backend-Python%203.13+-blue.svg)](https://www.python.org/downloads/)

PopUpSim is a microscopic simulation system for optimizing Pop-Up retrofitting sites during the European freight rail industry's transition to Digital Automatic Couplers (DAC). The tool simulates the complex logistics of retrofitting approximately 500,000 freight wagons during the critical 3-week "Big Bang" migration period (2029-2034).

> [!NOTE]  
> The Pandas dependency is pinned to an exact version (`pandas==3.0.5`) to avoid a
> Windows segfault observed with some releases. See `pyproject.toml` for the current pin.

## Overview

PopUpSim helps railway operators:
- **Test workshop configurations** - Develop and validate standardized Pop-Up workshop designs
- **Estimate throughput** - Calculate maximum wagon processing capacity
- **Import infrastructure data** - Use existing railway infrastructure data (CSV/JSON)
- **Identify bottlenecks** - Optimize resource allocation before real-world implementation
- **Assess capacity** - Validate if planned workshops meet migration targets

## Key Features

- **Microscopic Simulation** - Track individual wagons and resources through workshop operations
- **SimPy-based Engine** - Deterministic discrete event simulation for reproducible results
- **File-based Configuration** - Easy-to-edit JSON/CSV configuration files
- **Analysis** - Throughput metrics, utilization statistics, bottleneck identification
- **Open Source** - Apache 2.0 licensed for cross-company collaboration

## Quick Start

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager

If uv is used, the necessary Python version will be automatically installed during installation
of PopUpSim.
For different ways of installing uv can be found in **Step 1** of the [installation guide](https://openrailassociation.github.io/dac-migration-dss-popupsim/tutorial/00-installation/).

### Installation

A more detailed description of the installation process can be found in the
[installation guide](https://openrailassociation.github.io/dac-migration-dss-popupsim/tutorial/00-installation/)

#### Option 1: Using Git (Recommended)

If you have a git client installed:

```bash
# Clone repository
git clone https://github.com/OpenRailAssociation/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# Install dependencies
uv sync

# Run example simulation
uv run popupsim --scenario Data/examples/ten_trains_two_days_baseline/ --output output/
```

#### Option 2: Download ZIP Archive

If you don't have git installed:

1. Download the latest release as ZIP:
   - Visit: https://github.com/OpenRailAssociation/dac-migration-dss-popupsim/archive/refs/heads/main.zip
   - Or go to the [GitHub repository](https://github.com/OpenRailAssociation/dac-migration-dss-popupsim) and click "Code" → "Download ZIP"

2. Extract the archive to your desired location

3. Open a terminal/command prompt and navigate to the extracted folder:
   ```bash
   cd dac-migration-dss-popupsim-main

   # Install dependencies
   uv sync

   # Run example simulation
   uv run popupsim --scenario Data/examples/ten_trains_two_days_baseline/ --output output/
   ```

### Running PopUpSim

After installation, run simulations with:

```bash
# Navigate to project directory (if not already there)
cd dac-migration-dss-popupsim

# Run with baseline scenario
uv run python popupsim/backend/src/main.py --scenario Data/examples/ten_trains_two_days_baseline/ --output output/

# Or run a variant scenario
uv run python popupsim/backend/src/main.py --scenario Data/examples/ten_trains_two_days_var1/ --output output/var1/
```

### Viewing Results with Dashboard

PopUpSim includes a web-based dashboard for visualizing simulation results:

**Windows:**
```bash
run_dashboard.bat
```

**Linux/macOS:**
```bash
uv run streamlit run popupsim/frontend/dashboard.py
```

The dashboard will open in your browser at http://localhost:8501

**Dashboard Tabs:**
- **Overview** - KPIs, per-workshop breakdown, locomotive activity, workshop utilization
- **Scenario Config** - The input configuration for the loaded run
- **Wagons** - Wagon status distribution, location changes, individual journeys
- **Locomotives** - Activity breakdown and utilization
- **Workshops** - Workshop utilization and throughput
- **Track Capacity** - Track configuration and utilization per track
- **Bottleneck Analysis** - Process flow heatmap and resource utilization
- **Animation** - Animated playback of the run on a schematic yard

**Note:** Run the dashboard in a separate terminal window so you can continue running simulations.


### Example Scenarios

Seven ready-to-use scenarios are included (10 trains, 224 wagons over 2 days):

- **[Baseline](Data/examples/ten_trains_two_days_baseline/)** - 1 locomotive, 2 collection tracks, 1 retrofit track, 1 retrofitted track, 2 workshops (2 bays each)
- **[Variant 1](Data/examples/ten_trains_two_days_var1/)** - 1 locomotive, 3 collection tracks, 2 workshops (2 bays each), plus fill-level task prioritization
- **[Variant 2](Data/examples/ten_trains_two_days_var2/)** - 1 locomotive, 3 collection tracks, 2 retrofit tracks, 2 workshops (2 bays each)
- **[Variant 3](Data/examples/ten_trains_two_days_var3/)** - 2 locomotives, 3 collection tracks, 2 retrofit tracks, 2 workshops (2 bays each)
- **[Variant 4](Data/examples/ten_trains_two_days_var4/)** - 2 locomotives, 3 collection tracks, 2 retrofit tracks, 2 workshops (4 bays each - increased capacity)
- **[Variant 5](Data/examples/ten_trains_two_days_var5/)** - 2 locomotives, 3 collection tracks, 2 retrofit tracks, 2 workshops (4 bays each)
- **[Variant 6](Data/examples/ten_trains_two_days_var6/)** - 4 locomotives, 3 collection tracks, 2 retrofit tracks, 3 workshops (2 bays each), opportunistic parking strategy

**Known Limitations:**
- **Multiple retrofitted tracks**: Currently not fully stable - use single retrofitted track for production scenarios
- **Smart accumulation parking strategy**: May cause simulation deadlock if threshold is not reached at end of simulation - use `opportunistic` strategy for reliability

## Architecture

PopUpSim uses a 4 bounded-context architecture following Domain-Driven Design:

1. **Configuration Context** - Input loading & validation (Pydantic)
2. **External Trains Context** - Train arrivals & wagon creation (event publishing)
3. **Railway Infrastructure Context** - Track capacity & occupancy (domain aggregates)
4. **Retrofit Workflow Context** - Simulation execution, coordination & reporting (SimPy)

The bounded contexts follow a hexagonal (ports/adapters) style and communicate through a
shared event bus. Simulation output is consumed by a separate Streamlit dashboard.

For detailed architecture documentation, see [docs/mvp/architecture/](docs/mvp/architecture/README.md).

## Documentation

- **[Tutorial](docs/tutorial/README.md)** - Step-by-step configuration guide using the ten_trains_two_days example
- **[Architecture Documentation](docs/mvp/architecture/README.md)** - Complete arc42 architecture (12 sections)
- **[Development Guide](docs/mvp/development/README.md)** - Implementation details and code examples
- **[Backend README](popupsim/backend/README.md)** - Backend-specific documentation
- **[Use Cases](docs/requirements/use-cases.md)** - User stories and requirements

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
uv pip install pre-commit
pre-commit install
uv run ./setup/dev/set_commit_msg_hooks.py
```

### Development Commands

```bash
# Run all quality checks
uv run ruff format . && uv run ruff check . && uv run mypy popupsim/backend/src/ && uv run pylint popupsim/backend/src/ && uv run pytest

# Individual commands
uv run pytest                          # Run tests
uv run ruff format .                   # Format code
uv run ruff check .                    # Lint code
uv run mypy popupsim/backend/src/      # Type checking
uv run pylint popupsim/backend/src/    # Code quality analysis
```

### Code Quality Standards

- **Type hints mandatory** - All functions/methods must have explicit type annotations
- **MyPy strict mode** - `disallow_untyped_defs = true`
- **Ruff formatting** - Consistent code style
- **Pytest** - Automated test suite
- **Pylint** - Static code analysis and linting

## Technology Stack

- **Python 3.13+** - Latest stable Python with improved type system
- **SimPy** - Discrete event simulation framework
- **Pydantic 2.0+** - Data validation and settings management
- **Typer** - CLI framework for the `run` and `optimize` commands
- **Streamlit + Plotly** - Web dashboard and interactive visualization
- **Pandas** - CSV/data processing
- **uv** - Fast, reliable Python package manager

## Project Status

**Current Phase:** MVP Implementation and code stabilization


## Contributing

We welcome contributions from the railway industry and open source community!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes following code quality standards
4. Run all quality checks
5. Commit your changes (`git commit -m 'Add feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Open Rail Association** - Project governance and cross-company collaboration
- **3-Länderhack 2024** - Initial prototype development with ÖBB, DB, and SBB
- **DB Cargo Migration Team** - Domain expertise and requirements
- **Skydeck Accelerator (DB Systel GmbH)** - Project support

## Contact & Support

- **GitHub Issues** - [Report bugs or request features](https://github.com/open-rail-association/dac-migration-dss-popupsim/issues)
- **Documentation** - [Complete architecture docs](docs/mvp/architecture/README.md)
- **Open Rail Association** - [Project homepage](https://openrailassociation.org/)

---

**Note:** PopUpSim is under active development. The MVP focuses on desktop simulation with file-based configuration. Future versions will include e.g. a web interface.
