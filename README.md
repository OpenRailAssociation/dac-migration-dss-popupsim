# PopUpSim - DAC Migration Simulation Tool

[![Badge Stage 1](https://openrailassociation.org/badges/openrail-project-stage-1.svg)](https://link.openrailassociation.org/stage-1)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Backend](https://img.shields.io/badge/Backend-Python%203.13+-blue.svg)](https://www.python.org/downloads/)

PopUpSim is a microscopic simulation system for optimizing Pop-Up retrofitting sites during the European freight rail industry's transition to Digital Automatic Couplers (DAC). The tool simulates the complex logistics of retrofitting approximately 500,000 freight wagons during the critical 3-week "Big Bang" migration period (2029-2034).

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
- **Comprehensive Analysis** - Throughput metrics, utilization statistics, bottleneck identification
- **Open Source** - Apache 2.0 licensed for cross-company collaboration

## Quick Start

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone repository
git clone https://github.com/open-rail-association/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# Install dependencies
uv sync

# Run example simulation
uv run python popupsim/backend/src/main.py --scenario ./Data/examples/small_scenario/ --output output/small_scenario
```

### Example Scenarios

Three ready-to-use scenarios are included:

- **[Small Scenario](Data/examples/small_scenario/README.md)** - 2 trains, 20 wagons, 1 workshop track (quick testing)
- **[Medium Scenario](Data/examples/medium_scenario/README.md)** - 4 trains, 160 wagons, 2 workshop tracks
- **[Large Scenario](Data/examples/large_scenario/README.md)** - 10 trains, 500 wagons, 2 workshop tracks (high complexity)

## Architecture

PopUpSim MVP uses a 3-context architecture:

1. **Configuration Context** - Input validation & parsing (Pydantic)
2. **Workshop Operations Context** - Simulation execution & analysis (SimPy)
3. **Analysis & Reporting Context** - Orchestration & output (Matplotlib, CSV)

For detailed architecture documentation, see [docs/mvp/architecture/](docs/mvp/architecture/README.md).

## Documentation

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
- **Pytest** - Comprehensive test coverage
- **Pylint** - Static code analysis and linting

## Technology Stack

- **Python 3.13+** - Latest stable Python with improved type system
- **SimPy** - Discrete event simulation framework
- **Pydantic 2.0+** - Data validation and settings management
- **Matplotlib** - Visualization and chart generation
- **Pandas** - CSV data processing
- **uv** - Fast, reliable Python package manager

## Project Status

**Current Phase:** MVP Implementation Complete

**Implemented:**
- ✅ Configuration Context (Builder pattern, Pydantic validation, multi-file loading)
- ✅ Workshop Operations Context (5 process coordinators, SimPy integration, resource management)
- ✅ Analysis & Reporting Context (KPI calculation, CSV export, Matplotlib visualization)
- ✅ Resource Management (ResourcePool, TrackCapacityManager, WorkshopCapacityManager)
- ✅ Metrics Collection (Real-time collectors for wagons, locomotives, workshops)
- ✅ Domain Services (State managers, selectors, distributors - no SimPy dependencies)
- ✅ Example scenarios (small, medium, large)
- ✅ Architecture documentation (arc42 with Level 3 details)
- ✅ CLI interface (Typer-based)

**In Progress:**
- 🚧 Unit and integration tests
- 🚧 Performance optimization
- 🚧 Additional example scenarios

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
