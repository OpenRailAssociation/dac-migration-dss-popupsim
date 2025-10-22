# Copilot Instructions for PopUp-Sim (DAC Migration DSS)

## Project Overview
PopUp-Sim is a Python-based simulation tool for modeling the European freight rail industry's transition to Digital Automatic Couplers (DAC). It simulates logistics, retrofitting, and operational bottlenecks during a critical migration period. The backend is located in `popupsim/backend/`.

## Architecture & Key Components
- **Backend Core**: All main logic is in `popupsim/backend/src/`. Entry point: `main.py`.
- **Configuration**: Managed via `pyproject.toml`.
- **Testing**: Unit tests in `popupsim/backend/tests/unit/`.
- **Dev Scripts**: Commit hooks and setup scripts in `setup/dev/`.
- **Documentation**: High-level docs in `docs/`, backend-specific in `popupsim/backend/README.md`.

## Developer Workflows
- **Environment Setup**:
  - Requires Python 3.13+, [uv](https://docs.astral.sh/uv/) for dependency management.
  - Install dependencies: `uv pip install -r requirements.txt` or as per backend README.
  - Activate venv: `source .venv/bin/activate`.
- **Quality Checks** (run before commit):
  - Format: `uv run ruff format .`
  - Lint: `uv run ruff check .`
  - Type check: `uv run mypy backend/src/`
  - Static analysis: `uv run pylint backend/src/`
  - Tests: `uv run pytest`
  - All checks: `uv run ruff format . && uv run ruff check . && uv run mypy backend/src/ && uv run pylint backend/src/ && uv run pytest`
- **Pre-commit Hooks**: Install with `uv run ./setup/dev/set_commit_msg_hooks.py`.

## Conventions & Patterns
- **Formatting**: Ruff is enforced for code style and linting.
- **Type Safety**: MyPy is required for static type checks.
- **Testing**: Pytest is used for all unit tests. Place new tests in `popupsim/backend/tests/unit/`.
- **Branching**: Use feature branches (`feature/your-feature`) and open PRs against `main`.
- **CI/CD**: See `.github/workflows/README.md` for pipeline details. All backend changes trigger full QA pipeline.

## Integration Points
- **External**: No direct external service calls; simulation logic is self-contained.
- **Frontend**: (Planned) Vue.js integration, see architecture docs for context.

## Examples
- To run all checks before a commit:
  ```sh
  uv run ruff format . && uv run ruff check . && uv run mypy backend/src/ && uv run pylint backend/src/ && uv run pytest
  ```
- To add a new simulation scenario, create a module in `popupsim/backend/src/` and corresponding tests in `popupsim/backend/tests/unit/`.

## References
- [popupsim/backend/README.md](../popupsim/backend/README.md)
- [docs/architecture/](../docs/architecture/)
- [.github/workflows/README.md](workflows/README.md)

---
**Feedback requested:** Please review for missing or unclear sections, especially regarding build/test workflows, code conventions, or integration points.
