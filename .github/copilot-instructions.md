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
- **Type Safety**: MyPy is required for static type checks with `disallow_untyped_defs = true`.
- **Type Hints**: **MANDATORY** - All functions, methods, variables, and parameters must have explicit type annotations:
  - Function return types: `def function_name() -> ReturnType:`
  - Method return types: `def method_name(self) -> ReturnType:`
  - Test methods: `def test_something() -> None:`
  - Fixtures: `@pytest.fixture def fixture_name() -> FixtureType:`
  - Parameters: `def function(param: ParamType) -> ReturnType:`
  - Variables when type can't be inferred: `variable_name: TypeHint = value`
  - Use `from typing import` for generic types like `List`, `Dict`, `Optional`, `Union`, `Iterator`, `Generator`
  - Use `from typing_extensions import` for newer features like `Annotated`
- **Testing**: Pytest is used for all unit tests. Place new tests in `popupsim/backend/tests/unit/`.
- **Branching**: Use feature branches (`feature/your-feature`) and open PRs against `main`.
- **CI/CD**: See `.github/workflows/README.md` for pipeline details. All backend changes trigger full QA pipeline.

## Code Generation Rules
When generating or modifying code, **ALWAYS**:
1. Add return type annotations to all functions and methods (including `-> None` for void functions)
2. Add parameter type hints to all function/method parameters
3. Add type hints for class attributes and variables where type inference isn't clear
4. Import required types from `typing` or `typing_extensions`
5. Follow the project's MyPy configuration which enforces `disallow_untyped_defs = true`
6. Always try to find the most concise solution that meets type hinting requirements
7. Never import in functions or methods; all imports must be at the module level

## Type Hint Examples
```python
# Function with parameters and return type
def validate_path(path: Optional[Path]) -> Path | None:
    """Validate file path."""
    return path if path and path.exists() else None

# Test method (always -> None)
def test_validation() -> None:
    """Test path validation."""
    assert validate_path(None) is None

# Fixture with proper return type
@pytest.fixture
def temp_file() -> Generator[Path, None, None]:
    """Create temporary file."""
    with tempfile.NamedTemporaryFile() as f:
        yield Path(f.name)

# Class method with type hints
def __init__(self, config: Dict[str, Any]) -> None:
    """Initialize with models."""
    self.config = config
```

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
