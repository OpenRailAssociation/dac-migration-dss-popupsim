# 0. Getting Started (for Developers)

This page is the single entry point for a new developer. It takes you from a fresh clone to
running a simulation, viewing results, and running the quality checks — then points you at the
deeper docs.

## Prerequisites

- **Python 3.13+** (the project requires `>=3.13`)
- **[uv](https://docs.astral.sh/uv/)** package manager

If uv is installed, it will fetch the right Python version automatically during `uv sync`.

## 1. Clone and install

```bash
git clone https://github.com/OpenRailAssociation/dac-migration-dss-popupsim.git
cd dac-migration-dss-popupsim

# Runtime + dev tooling (the `dev` dependency group is included by default)
uv sync

# Include the docs tooling too (mkdocs) if you plan to build the docs
uv sync --group docs
```

## 2. Set up pre-commit hooks (development)

```bash
uv run pre-commit install
uv run ./setup/dev/set_commit_msg_hooks.py
```

Hooks run Ruff (format + lint), MyPy, and Pylint on commit.

## 3. Run a simulation

The CLI (`popupsim/backend/src/main.py`, built with Typer) has two commands: `run` and
`optimize`.

```bash
# Run the baseline example scenario
uv run python popupsim/backend/src/main.py run \
  --scenario Data/examples/ten_trains_two_days_baseline/ \
  --output output/
```

Output is written as flat CSV/JSON files into `output/` (e.g. `summary_metrics.json`,
`wagon_journey.csv`, `locomotive_movements.csv`). See
[File Formats](07-mvp-file-formats.md) and
[Running the Simulation](../../tutorial/10-running-simulation.md#output-files) for details.

### View results in the dashboard

Run this in a separate terminal (it's a long-running server):

```bash
uv run streamlit run popupsim/frontend/dashboard.py
```

The dashboard opens at http://localhost:8501 and reads the files in your output directory.

### Optional: optimize task priorities

```bash
uv run python popupsim/backend/src/main.py optimize \
  --scenario Data/examples/ten_trains_two_days_baseline/
```

See [Optimizing Scenarios](../../tutorial/11-optimizing-scenarios.md).

## 4. Run tests and quality checks

```bash
# Tests
uv run pytest

# Coverage (a minimum of 40% is enforced)
uv run pytest --cov=popupsim/backend/src/

# Full quality gate (format, lint, type-check, static analysis, tests)
uv run ruff format . && \
uv run ruff check . && \
uv run mypy popupsim/backend/src/ && \
uv run pylint popupsim/backend/src/ && \
uv run pytest
```

## 5. Build the documentation (optional)

```bash
uv run --group docs mkdocs serve   # live preview at http://127.0.0.1:8000
```

## Where things live

| Area | Location |
|------|----------|
| CLI entry point | `popupsim/backend/src/main.py` |
| Orchestration | `popupsim/backend/src/application/simulation_service.py` |
| Bounded contexts | `popupsim/backend/src/contexts/` |
| Shared kernel (incl. SimPy engine adapter) | `popupsim/backend/src/shared/` |
| Technical infrastructure (event bus, tracking) | `popupsim/backend/src/infrastructure/` |
| Optimizer | `popupsim/backend/src/optimizer/` |
| Dashboard (Streamlit) | `popupsim/frontend/` |
| Tests | `popupsim/backend/tests/` |
| Example scenarios | `Data/examples/` |
| Coding standards | `.amazonq/rules/project-rules.md` |

## Recommended reading order

1. **[MVP Architecture Overview](../architecture/README.md)** — the big picture (arc42).
2. **[Bounded Contexts](02-mvp-contexts.md)** — the four contexts and their responsibilities.
3. **[Domain Model](03-mvp-domain-model.md)** — entities, models, and domain services.
4. **[Data Flow](05-mvp-data-flow.md)** — how a run moves from input files to output.
5. **[SimPy Integration](04-mvp-simpy-integration.md)** — how the simulation engine is wired.
6. **[Testing Strategy](08-mvp-testing-strategy.md)** — how the tests are organized.
7. **[Architecture Decisions](../architecture/09-architecture-decisions.md)** — the ADRs and
   why key choices were made.

Then read the actual code under `popupsim/backend/src/` — the docs point to the authoritative
files rather than duplicating them.
