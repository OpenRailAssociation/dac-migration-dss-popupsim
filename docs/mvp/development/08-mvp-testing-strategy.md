# 8. MVP Testing Strategy

## Overview

**Location:** `popupsim/backend/tests/`

**Status:** 374 tests passing

## Test Organization

```
tests/
├── unit/
│   ├── configuration/          # Configuration Context tests
│   ├── retrofit_workflow/      # Retrofit Workflow tests
│   ├── railway_infrastructure/ # Railway Infrastructure tests
│   └── external_trains/        # External Trains tests
├── integration/                # Cross-context tests
└── conftest.py                 # Pytest configuration
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

- **Domain services:** > 90%
- **Coordinators:** > 80%
- **Infrastructure:** > 70%
- **Overall:** > 80%

## Best Practices

### ✅ Do's
- Test domain logic without SimPy
- Use fixtures for common test data
- Test error cases
- Keep tests fast

### ❌ Don'ts
- Don't test external libraries
- Don't use real file I/O in unit tests
- Don't create complex test scenarios

---
