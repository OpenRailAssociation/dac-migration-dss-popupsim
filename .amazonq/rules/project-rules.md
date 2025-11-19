# Amazon Q Rules for PopUp-Sim (DAC Migration DSS)

## Project Context
PopUp-Sim simulates the European freight rail industry's transition to Digital Automatic Couplers (DAC). Backend is Python-based in `popupsim/backend/`.

## Code Generation Requirements

### Type Hints (MANDATORY)
All code MUST include explicit type annotations:
- Functions: `def function_name() -> ReturnType:`
- Methods: `def method_name(self) -> ReturnType:`
- Test methods: `def test_something() -> None:`
- Fixtures: `@pytest.fixture def fixture_name() -> FixtureType:`
- Parameters: `def function(param: ParamType) -> ReturnType:`
- Variables when unclear: `variable_name: TypeHint = value`
- Import from `typing`: `List`, `Dict`, `Optional`, `Union`, `Iterator`, `Generator`
- Import from `typing_extensions` for newer features

### Quality Standards
- Format with Ruff
- MyPy enforces `disallow_untyped_defs = true`
- Pytest for all tests in `popupsim/backend/tests/unit/`
- No code without type hints

### Type Hint Examples
```python
from typing import Optional, Dict, Any, Generator
from pathlib import Path

def validate_path(path: Optional[Path]) -> Path | None:
    """Validate file path."""
    return path if path and path.exists() else None

def test_validation() -> None:
    """Test path validation."""
    assert validate_path(None) is None

@pytest.fixture
def temp_file() -> Generator[Path, None, None]:
    """Create temporary file."""
    with tempfile.NamedTemporaryFile() as f:
        yield Path(f.name)

def __init__(self, config: Dict[str, Any]) -> None:
    """Initialize with models."""
    self.config = config
```

## Development Commands
- Install: `uv pip install -r requirements.txt`
- Format: `uv run ruff format .`
- Lint: `uv run ruff check .`
- Type check: `uv run mypy backend/src/`
- Static analysis: `uv run pylint backend/src/`
- Test: `uv run pytest`
- All checks: `uv run ruff format . && uv run ruff check . && uv run mypy backend/src/ && uv run pylint backend/src/ && uv run pytest`

## Project Structure
- Backend: `popupsim/backend/src/` (entry: `main.py`)
- Tests: `popupsim/backend/tests/unit/`
- Config: `pyproject.toml`
- Python: 3.13+, uv for dependencies

## Conventions
- Feature branches: `feature/your-feature`
- PRs to `main`
- Pre-commit hooks: `uv run ./setup/dev/set_commit_msg_hooks.py`
