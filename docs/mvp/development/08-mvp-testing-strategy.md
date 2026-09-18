# 8. MVP Testing Strategy

## Overview

**Location:** `popupsim/backend/tests/`

**Status:** run `uv run pytest` for the current test count and `uv run pytest --cov=popupsim/backend/src/`
for coverage. A minimum of 40% coverage is enforced.

## Test Organization

```
popupsim/backend/tests/
├── conftest.py
├── fixtures/                   # JSON/CSV test fixtures
├── unit/
│   ├── contexts/
│   │   ├── configuration/      # Config loading & validation
│   │   ├── retrofit_workflow/  # application/, domain/, infrastructure/
│   │   ├── railway_infrastructure/
│   │   └── optimizer_search/
│   ├── frontend/               # Dashboard component tests
│   └── shared/                 # Shared utilities
└── validation/                 # Scenario/timeline validation tests
    ├── test_retrofit_workflow_scenarios.py
    ├── test_layered_scenarios.py
    ├── test_layered_timelines.py
    └── test_scenario_builder.py
```

## Test Types

### Unit Tests

Test individual components without external dependencies:

```python
def test_batch_formation() -> None:
    """Test domain service."""
    service = BatchFormationService()
    wagons = [Wagon(...) for _ in range(5)]

    batch = service.form_batch_for_workshop(wagons, ...)
    assert len(batch.wagon_ids) == 5
```

### Integration Tests

Test context interactions:

```python
def test_configuration_loading() -> None:
    """Test file loading."""
    builder = ConfigurationBuilder(Path('test_scenario'))
    scenario = builder.build()

    assert scenario.id == 'test'
    assert len(scenario.workshops) > 0
```

### Simulation Tests

Test with SimPy:

```python
def test_collection_coordinator() -> None:
    """Test coordinator with SimPy."""
    env = simpy.Environment()
    coordinator = CollectionCoordinator(...)
    coordinator.start()
    
    env.run(until=100)
    
    assert len(coordinator.processed_batches) > 0
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific context
uv run pytest popupsim/backend/tests/unit/contexts/configuration/

# With coverage
uv run pytest --cov=popupsim/backend/src/

# Verbose
uv run pytest -v
```

## Test Fixtures

**File:** `tests/conftest.py`

```python
import pytest
from pathlib import Path

@pytest.fixture
def test_scenario_path() -> Path:
    """Path to test scenario."""
    return Path("tests/fixtures/test_scenario")

@pytest.fixture
def sample_scenario() -> Scenario:
    """Sample scenario for testing."""
    return Scenario(
        id="test",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        ...
    )
```

## Coverage Goals

A minimum of **40% overall coverage** is enforced (the build fails below it). Check the
current number with:

```bash
uv run pytest --cov=popupsim/backend/src/
```

**Target coverage by component (aspirational):**
- **Domain services:** highest priority — pure logic, easy to test
- **Coordinators / application services:** medium
- **Infrastructure:** lower (harder to unit-test in isolation)

## Quality Standards

All code must pass:

```bash
# Code formatting
uv run ruff format .

# Linting (0 errors required)
uv run ruff check .

# Type checking (0 errors required, strict mode)
uv run mypy popupsim/backend/src/

# Static analysis
uv run pylint popupsim/backend/src/

# All tests (must pass)
uv run pytest

# Run all checks
uv run ruff format . && uv run ruff check . && uv run mypy popupsim/backend/src/ && uv run pylint popupsim/backend/src/ && uv run pytest
```

**MyPy Configuration:**
```toml
[tool.mypy]
disallow_untyped_defs = true  # All functions must have type hints
```

(Some third-party/legacy modules relax `disallow_untyped_defs` via per-module overrides — see
`pyproject.toml`.)

## Best Practices

### Do's
- Test domain logic without SimPy
- Use fixtures for common test data
- Test error cases
- Keep tests fast
- Include type hints in all test functions
- Use descriptive test names

### Don'ts
- Don't test external libraries
- Don't use real file I/O in unit tests
- Don't create complex test scenarios
- Don't skip type hints (mypy strict mode enforced)

---
