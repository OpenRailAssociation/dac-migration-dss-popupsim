# 8. MVP Testing Strategy

## Overview

**Location:** `popupsim/backend/tests/`

**Status:** 378 tests passing, 54% coverage

## Test Organization

```
tests/
├── unit/                       # 318 unit tests
│   ├── contexts/
│   │   ├── configuration/      # Config loading & validation
│   │   ├── retrofit_workflow/
│   │   │   ├── application/    # Coordinators, services
│   │   │   ├── domain/         # Domain services, aggregates
│   │   │   └── infrastructure/ # Resource managers
│   │   └── railway_infrastructure/
│   └── shared/                 # Shared utilities
└── validation/                 # 60 validation tests
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
    
    assert service.can_form_batch(wagons, min_size=1, max_size=10)
```

### Integration Tests

Test context interactions:

```python
def test_configuration_loading() -> None:
    """Test file loading."""
    builder = ConfigurationBuilder(Path("test_scenario"))
    scenario = builder.build()
    
    assert scenario.id == "test"
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
uv run pytest popupsim/backend/tests/unit/configuration/

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

**Current Coverage:** 54.34% (exceeds 40% requirement)

**Target Coverage by Component:**
- **Domain services:** > 90% (currently 85-98%)
- **Coordinators:** > 80% (currently 70-88%)
- **Infrastructure:** > 70% (currently 57-98%)
- **Overall:** > 40% ✅ (currently 54%)

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

# All tests (378/378 passing required)
uv run pytest

# Run all checks
uv run ruff format . && uv run ruff check . && uv run mypy popupsim/backend/src/ && uv run pylint popupsim/backend/src/ && uv run pytest
```

**MyPy Configuration:**
```toml
[tool.mypy]
disallow_untyped_defs = true  # All functions must have type hints
strict = true
```

## Best Practices

### ✅ Do's
- Test domain logic without SimPy
- Use fixtures for common test data
- Test error cases
- Keep tests fast
- Include type hints in all test functions
- Use descriptive test names

### ❌ Don'ts
- Don't test external libraries
- Don't use real file I/O in unit tests
- Don't create complex test scenarios
- Don't skip type hints (mypy strict mode enforced)

---
