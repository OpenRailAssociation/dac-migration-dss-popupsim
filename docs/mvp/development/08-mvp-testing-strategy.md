# 8. MVP Testing Strategy

## Overview

**Note:** See [Architecture Section 8.6](../architecture/08-concepts.md#86-testing-concept) for testing concept.

This document describes the testing approach for the MVP.

## Testing Pyramid

```
        ┌─────────────────┐
        │  System Tests   │  ← Few, slow
        │   (End-to-End)  │
        ├─────────────────┤
        │ Integration     │  ← Some, medium
        │    Tests        │
        ├─────────────────┤
        │   Unit Tests    │  ← Many, fast
        │                 │
        └─────────────────┘
```

## Unit Tests

### Domain Logic Tests

```python
import pytest
from domain.models import Wagon, WorkshopTrack

def test_wagon_waiting_time() -> None:
    wagon = Wagon(
        id="W001",
        train_id="T001",
        arrival_time=10.0,
        retrofit_start_time=15.0
    )
    assert wagon.waiting_time == 5.0

def test_track_availability() -> None:
    track = WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=3
    )
    assert track.is_available() == True

    track.current_wagons = 5
    assert track.is_available() == False
```

### Configuration Tests

```python
import pytest
from pydantic import ValidationError
from models.models import ScenarioConfig, Workshop, WorkshopTrack


def test_valid_scenario_config() -> None:
    config = ScenarioConfig(
        scenario_id="test",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        workshop=Workshop(tracks=[
            WorkshopTrack(
                id="TRACK01",
                function=TrackFunction.WERKSTATTGLEIS,
                capacity=5,
                retrofit_time_min=30
            )
        ]),
        train_schedule_file="schedule.csv"
    )
    assert config.scenario_id == "test"


def test_invalid_date_range() -> None:
    with pytest.raises(ValidationError):
        ScenarioConfig(
            scenario_id="test",
            start_date=date(2025, 1, 2),
            end_date=date(2025, 1, 1),  # Before start_date
            workshop=Workshop(tracks=[]),
            train_schedule_file="schedule.csv"
        )
```

## Integration Tests

### SimPy Integration Tests

```python
import simpy
from simulation.simpy_adapter import SimPyEnvironmentAdapter, WorkshopSimPyAdapter

def test_simple_simulation() -> None:
    """Test with SimPy environment"""
    env = SimPyEnvironmentAdapter()

    workshop = Workshop(
        tracks=[
            WorkshopTrack(
                id="TRACK01",
                capacity=2,
                retrofit_time_min=30
            )
        ]
    )

    adapter = WorkshopSimPyAdapter(
        workshop=workshop,
        env=env,
        event_logger=EventLogger()
    )

    # Create test wagon
    wagon = Wagon(id="W001", train_id="T001", needs_retrofit=True)

    # Start retrofit process
    env.process(adapter.retrofit_process(wagon))

    # Run simulation
    env.run(until=60)

    # Assertions
    assert wagon.retrofit_end_time is not None
    assert wagon.needs_retrofit == False
```

### File I/O Tests

```python
import pytest
from pathlib import Path
from models.services import ConfigurationService


def test_load_scenario_from_json(tmp_path: Path) -> None:
    # Create test scenario file
    scenario_file = tmp_path / "scenario.json"
    scenario_file.write_text('''
    {
        "scenario_id": "test",
        "start_date": "2025-01-01",
        "end_date": "2025-01-02",
        "workshop": {
            "tracks": [
                {
                    "id": "TRACK01",
                    "function": "WERKSTATTGLEIS",
                    "capacity": 5,
                    "retrofit_time_min": 30
                }
            ]
        },
        "train_schedule_file": "schedule.csv"
    }
    ''')

    # Load and validate
    service = ConfigurationService()
    config = service.load_scenario_from_file(scenario_file)

    assert config.scenario_id == "test"
    assert len(config.workshop.tracks) == 1
```

## System Tests

### End-to-End Simulation Test

```python
def test_complete_simulation_flow(tmp_path: Path) -> None:
    """Test complete simulation from config to results"""
    # 1. Setup test models
    config_path = tmp_path / "config"
    config_path.mkdir()

    # Create scenario.json
    (config_path / "scenario.json").write_text('''
    {
        "scenario_id": "e2e_test",
        "start_date": "2025-01-01",
        "end_date": "2025-01-01",
        "workshop": {
            "tracks": [
                {
                    "id": "TRACK01",
                    "function": "WERKSTATTGLEIS",
                    "capacity": 3,
                    "retrofit_time_min": 30
                }
            ]
        },
        "train_schedule_file": "train_schedule.csv"
    }
    ''')

    # Create train_schedule.csv
    (config_path / "train_schedule.csv").write_text('''
train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2025-01-01,08:00,W001,15.5,true,true
TRAIN001,2025-01-01,08:00,W002,15.5,false,true
    ''')

    # 2. Run simulation
    app = PopUpSimApplication()
    results = app.run_complete_analysis(str(config_path / "scenario.json"))

    # 3. Verify results
    assert results.simulation_results.total_wagons_processed == 2
    assert results.simulation_results.throughput_per_hour > 0

    # 4. Verify output files
    output_path = tmp_path / "results"
    assert (output_path / "summary.csv").exists()
    assert (output_path / "wagons.csv").exists()
```

## Test Fixtures

### Common Fixtures

```python
import pytest
from datetime import date

@pytest.fixture
def sample_workshop() -> Workshop:
    return Workshop(
        tracks=[
            WorkshopTrack(
                id="TRACK01",
                function=TrackFunction.WERKSTATTGLEIS,
                capacity=5,
                retrofit_time_min=30
            )
        ]
    )

@pytest.fixture
def sample_scenario_config() -> ScenarioConfig:
    return ScenarioConfig(
        scenario_id="test_scenario",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        workshop=Workshop(tracks=[]),
        train_schedule_file="schedule.csv"
    )

@pytest.fixture
def sample_wagons() -> list[Wagon]:
    return [
        Wagon(id="W001", train_id="T001", needs_retrofit=True),
        Wagon(id="W002", train_id="T001", needs_retrofit=True),
        Wagon(id="W003", train_id="T002", needs_retrofit=False),
    ]
```

## Test Coverage

### Coverage Goals
- **Domain Logic**: > 90%
- **Configuration**: > 85%
- **Simulation**: > 80%
- **Overall**: > 80%

### Running Coverage

```bash
# Run tests with coverage
uv run pytest --cov=backend/src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Performance Tests

### Benchmark Tests

```python
import pytest
import time

def test_simulation_performance() -> None:
    """Ensure simulation completes in reasonable time"""
    start_time = time.time()

    # Run simulation with 100 wagons
    config = create_test_config(wagon_count=100)
    service = SimulationService(config)
    results = service.run()

    duration = time.time() - start_time

    # Should complete in less than 10 seconds
    assert duration < 10.0
```

## Test Organization

### Directory Structure

```
backend/tests/
├── unit/
│   ├── test_domain_models.py
│   ├── test_configuration.py
│   └── test_services.py
├── integration/
│   ├── test_simpy_integration.py
│   ├── test_file_io.py
│   └── test_kpi_calculation.py
├── system/
│   └── test_end_to_end.py
└── conftest.py  # Shared fixtures
```

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Fixtures: Descriptive names without `test_` prefix

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest backend/tests/unit/test_domain_models.py

# Run specific test
uv run pytest backend/tests/unit/test_domain_models.py::test_wagon_waiting_time

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=backend/src

# Run only fast tests (skip slow integration tests)
uv run pytest -m "not slow"
```

## Test Markers

```python
import pytest

@pytest.mark.slow
def test_large_simulation() -> None:
    """Slow test - run with pytest -m slow"""
    pass

@pytest.mark.integration
def test_simpy_integration() -> None:
    """Integration test"""
    pass

@pytest.mark.unit
def test_domain_logic() -> None:
    """Unit test"""
    pass
```

## CI/CD Integration

Tests run automatically on every push via GitHub Actions. See `.github/workflows/python-backend.yml`.
