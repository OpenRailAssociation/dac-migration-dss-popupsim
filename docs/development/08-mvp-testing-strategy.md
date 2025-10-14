# PopUpSim MVP - Testing Strategy

## Übersicht

Diese Datei definiert die Test-Strategie für den MVP mit Fokus auf pragmatisches Testing bei hoher Code-Qualität.

---

## Test-Pyramide MVP

```
                    ┌─────────────┐
                    │   Manual    │  5%
                    │   Testing   │
                    └─────────────┘
                  ┌─────────────────┐
                  │  Integration    │  15%
                  │     Tests       │
                  └─────────────────┘
              ┌───────────────────────┐
              │    Unit Tests         │  80%
              │  (Domain Logic)       │
              └───────────────────────┘
```

**Ziel:** 80% Test Coverage mit Fokus auf Business Logic

---

## Test-Kategorien

### 1. Unit Tests (80% der Tests)

**Zweck:** Teste Domain Logic isoliert ohne Dependencies

**Scope:**
- Pydantic Models
- Domain Logic (Wagon, Workshop, Track)
- KPI Calculations
- Validierungen

**Beispiel:**
```python
# tests/unit/test_wagon.py
import pytest
from src.workshop.models import Wagon

def test_wagon_waiting_time():
    """Test Wartezeit-Berechnung"""
    wagon = Wagon(
        id="W001",
        train_id="T001",
        arrival_time=10.0,
        retrofit_start_time=15.0
    )
    assert wagon.waiting_time == 5.0

def test_wagon_waiting_time_none_when_not_started():
    """Test Wartezeit ist None wenn noch nicht gestartet"""
    wagon = Wagon(
        id="W001",
        train_id="T001",
        arrival_time=10.0
    )
    assert wagon.waiting_time is None

def test_wagon_retrofit_duration():
    """Test Umrüstdauer-Berechnung"""
    wagon = Wagon(
        id="W001",
        train_id="T001",
        retrofit_start_time=10.0,
        retrofit_end_time=40.0
    )
    assert wagon.retrofit_duration == 30.0

@pytest.mark.parametrize("arrival,start,expected", [
    (0.0, 0.0, 0.0),
    (10.0, 15.0, 5.0),
    (100.0, 150.0, 50.0),
])
def test_wagon_waiting_time_parametrized(arrival, start, expected):
    """Test Wartezeit mit verschiedenen Werten"""
    wagon = Wagon(
        id="W001",
        train_id="T001",
        arrival_time=arrival,
        retrofit_start_time=start
    )
    assert wagon.waiting_time == expected
```

---

### 2. Integration Tests (15% der Tests)

**Zweck:** Teste Zusammenspiel mehrerer Komponenten

**Scope:**
- Configuration → Workshop
- Workshop → SimPy
- SimPy → KPI Calculation
- End-to-End Simulation

**Beispiel:**
```python
# tests/integration/test_simulation_flow.py
import pytest
from pathlib import Path
from src.configuration.service import ConfigurationService
from src.workshop.service import WorkshopService
from src.simulation.service import SimulationService

@pytest.fixture
def config_path():
    return Path("config/examples/small_scenario")

def test_configuration_to_workshop(config_path):
    """Test Configuration → Workshop Integration"""
    # 1. Lade Configuration
    config_service = ConfigurationService()
    config = config_service.load_scenario(config_path)

    # 2. Erstelle Workshop
    workshop_service = WorkshopService()
    workshop = workshop_service.setup_workshop(config.workshop)

    # 3. Assertions
    assert len(workshop.tracks) == len(config.workshop.tracks)
    assert workshop.tracks[0].id == config.workshop.tracks[0].id

def test_end_to_end_simulation(config_path):
    """Test komplette Simulation End-to-End"""
    # 1. Setup
    config_service = ConfigurationService()
    config = config_service.load_scenario(config_path)

    # 2. Run Simulation
    simulation_service = SimulationService(config)
    results = simulation_service.run()

    # 3. Assertions
    assert results.total_wagons_processed > 0
    assert results.throughput_per_hour > 0
    assert results.average_waiting_time >= 0
    assert 0 <= results.track_utilization <= 1
```

---

### 3. Manual Testing (5% der Tests)

**Zweck:** Explorative Tests und User Acceptance

**Scope:**
- Visualisierungen prüfen
- Output-Dateien manuell inspizieren
- Performance-Tests mit großen Szenarien

**Checkliste:**
```markdown
## Manual Test Checklist

### Configuration Loading
- [ ] scenario.json lädt korrekt
- [ ] Validierungsfehler werden angezeigt
- [ ] Beispiel-Szenarien funktionieren

### Simulation Execution
- [ ] Simulation startet ohne Fehler
- [ ] Progress wird angezeigt
- [ ] Simulation endet korrekt

### Output Generation
- [ ] Alle CSV-Dateien werden erstellt
- [ ] Charts sind lesbar und korrekt
- [ ] JSON-Output ist valide

### Performance
- [ ] Small Scenario < 5 Sekunden
- [ ] Medium Scenario < 30 Sekunden
- [ ] Large Scenario < 3 Minuten
```

---

## Test-Organisation

### Verzeichnisstruktur
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
│
├── unit/
│   ├── __init__.py
│   ├── test_configuration_models.py
│   ├── test_workshop_models.py
│   ├── test_wagon.py
│   ├── test_track.py
│   ├── test_kpi_service.py
│   └── test_validation.py
│
├── integration/
│   ├── __init__.py
│   ├── test_configuration_service.py
│   ├── test_workshop_service.py
│   ├── test_simulation_service.py
│   └── test_end_to_end.py
│
└── fixtures/
    ├── config/
    │   └── test_scenario.json
    └── expected_results/
        └── test_results.json
```

---

## Shared Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path
from src.configuration.models import ScenarioConfig, WorkshopConfig, WorkshopTrackConfig, TrainConfig
from src.workshop.models import Workshop, WorkshopTrack, Wagon, Train

@pytest.fixture
def test_config_path():
    """Path zu Test-Konfiguration"""
    return Path("tests/fixtures/config")

@pytest.fixture
def simple_track_config():
    """Einfache Track-Konfiguration"""
    return WorkshopTrackConfig(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30
    )

@pytest.fixture
def simple_workshop_config(simple_track_config):
    """Einfache Workshop-Konfiguration"""
    return WorkshopConfig(
        tracks=[simple_track_config]
    )

@pytest.fixture
def simple_scenario_config(simple_workshop_config):
    """Einfache Szenario-Konfiguration"""
    return ScenarioConfig(
        duration_hours=2,
        random_seed=42,
        workshop=simple_workshop_config,
        trains=TrainConfig(
            arrival_interval_minutes=60,
            wagons_per_train=5
        )
    )

@pytest.fixture
def simple_track():
    """Einfaches Track Domain Model"""
    return WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=0
    )

@pytest.fixture
def simple_workshop(simple_track):
    """Einfaches Workshop Domain Model"""
    return Workshop(
        id="workshop_001",
        tracks=[simple_track]
    )

@pytest.fixture
def simple_wagon():
    """Einfacher Wagon"""
    return Wagon(
        id="W001",
        train_id="T001",
        needs_retrofit=True
    )

@pytest.fixture
def processed_wagon():
    """Vollständig verarbeiteter Wagon"""
    return Wagon(
        id="W001",
        train_id="T001",
        arrival_time=10.0,
        retrofit_start_time=15.0,
        retrofit_end_time=45.0,
        track_id="TRACK01",
        needs_retrofit=False
    )
```

---

## Test-Beispiele pro Context

### Configuration Context

```python
# tests/unit/test_configuration_models.py
import pytest
from pydantic import ValidationError
from src.configuration.models import WorkshopTrackConfig

def test_track_config_valid():
    """Test valide Track-Konfiguration"""
    config = WorkshopTrackConfig(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30
    )
    assert config.id == "TRACK01"
    assert config.capacity == 5

def test_track_config_invalid_id():
    """Test ungültige Track-ID"""
    with pytest.raises(ValidationError) as exc_info:
        WorkshopTrackConfig(
            id="INVALID",
            capacity=5,
            retrofit_time_min=30
        )
    assert "string does not match regex" in str(exc_info.value)

def test_track_config_capacity_too_high():
    """Test Kapazität zu hoch"""
    with pytest.raises(ValidationError) as exc_info:
        WorkshopTrackConfig(
            id="TRACK01",
            capacity=100,
            retrofit_time_min=30
        )
    assert "less than or equal to 20" in str(exc_info.value)

def test_track_config_retrofit_time_too_low():
    """Test Umrüstzeit zu niedrig"""
    with pytest.raises(ValidationError) as exc_info:
        WorkshopTrackConfig(
            id="TRACK01",
            capacity=5,
            retrofit_time_min=5
        )
    assert "greater than or equal to 10" in str(exc_info.value)
```

---

### Workshop Context

```python
# tests/unit/test_track.py
import pytest
from src.workshop.models import WorkshopTrack

def test_track_is_available_when_empty():
    """Test Track ist verfügbar wenn leer"""
    track = WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=0
    )
    assert track.is_available() is True

def test_track_is_available_when_not_full():
    """Test Track ist verfügbar wenn nicht voll"""
    track = WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=3
    )
    assert track.is_available() is True

def test_track_is_not_available_when_full():
    """Test Track ist nicht verfügbar wenn voll"""
    track = WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=5
    )
    assert track.is_available() is False

@pytest.mark.parametrize("capacity,current,expected", [
    (5, 0, True),
    (5, 4, True),
    (5, 5, False),
    (1, 0, True),
    (1, 1, False),
])
def test_track_availability_parametrized(capacity, current, expected):
    """Test Track-Verfügbarkeit mit verschiedenen Werten"""
    track = WorkshopTrack(
        id="TRACK01",
        capacity=capacity,
        retrofit_time_min=30,
        current_wagons=current
    )
    assert track.is_available() is expected
```

---

### Simulation Control Context

```python
# tests/unit/test_kpi_service.py
import pytest
from src.simulation.kpi_service import KPIService
from src.workshop.models import Wagon

@pytest.fixture
def kpi_service():
    return KPIService()

@pytest.fixture
def sample_wagons():
    return [
        Wagon(
            id="W001",
            train_id="T001",
            arrival_time=10.0,
            retrofit_start_time=10.0,
            retrofit_end_time=40.0,
            track_id="TRACK01"
        ),
        Wagon(
            id="W002",
            train_id="T001",
            arrival_time=10.0,
            retrofit_start_time=15.0,
            retrofit_end_time=45.0,
            track_id="TRACK01"
        ),
        Wagon(
            id="W003",
            train_id="T001",
            arrival_time=10.0,
            retrofit_start_time=40.0,
            retrofit_end_time=70.0,
            track_id="TRACK02"
        ),
    ]

def test_calculate_throughput(kpi_service, sample_wagons):
    """Test Durchsatz-Berechnung"""
    throughput = kpi_service.calculate_throughput(sample_wagons, duration_hours=2.0)
    assert throughput == 1.5  # 3 wagons / 2 hours

def test_calculate_average_waiting_time(kpi_service, sample_wagons):
    """Test durchschnittliche Wartezeit"""
    avg_waiting = kpi_service.calculate_average_waiting_time(sample_wagons)
    # W001: 0 min, W002: 5 min, W003: 30 min → Avg: 11.67 min
    assert pytest.approx(avg_waiting, 0.01) == 11.67

def test_calculate_waiting_times_empty_list(kpi_service):
    """Test Wartezeit-Berechnung mit leerer Liste"""
    avg_waiting = kpi_service.calculate_average_waiting_time([])
    assert avg_waiting == 0.0
```

---

## SimPy Integration Tests

```python
# tests/integration/test_simpy_integration.py
import pytest
import simpy
from src.workshop.models import Workshop, WorkshopTrack, Wagon
from src.workshop.simpy_adapter import WorkshopSimPyAdapter, SimPyEnvironmentAdapter

def test_simple_retrofit_process():
    """Test einfacher Retrofit-Prozess mit SimPy"""
    # Setup
    env = SimPyEnvironmentAdapter()

    track = WorkshopTrack(
        id="TRACK01",
        capacity=2,
        retrofit_time_min=30,
        current_wagons=0,
        resource=simpy.Resource(env.simpy_env, capacity=2)
    )

    workshop = Workshop(id="test", tracks=[track])
    adapter = WorkshopSimPyAdapter(workshop=workshop, env=env)

    wagon = Wagon(id="W001", train_id="T001")

    # Run
    env.process(adapter.retrofit_process(wagon))
    env.run(until=60)

    # Assert
    assert wagon.retrofit_end_time is not None
    assert wagon.needs_retrofit is False
    assert wagon.track_id == "TRACK01"
    assert wagon.retrofit_duration == 30.0

def test_multiple_wagons_parallel():
    """Test mehrere Wagen parallel"""
    env = SimPyEnvironmentAdapter()

    track = WorkshopTrack(
        id="TRACK01",
        capacity=3,
        retrofit_time_min=30,
        resource=simpy.Resource(env.simpy_env, capacity=3)
    )

    workshop = Workshop(id="test", tracks=[track])
    adapter = WorkshopSimPyAdapter(workshop=workshop, env=env)

    wagons = [
        Wagon(id=f"W{i:03d}", train_id="T001")
        for i in range(3)
    ]

    # Starte alle Prozesse
    for wagon in wagons:
        env.process(adapter.retrofit_process(wagon))

    env.run(until=60)

    # Alle sollten fertig sein (parallel verarbeitet)
    for wagon in wagons:
        assert wagon.retrofit_end_time is not None
        assert wagon.retrofit_end_time <= 30.0  # Alle parallel, also nach 30 min fertig

def test_wagon_queuing_when_track_full():
    """Test Warteschlange wenn Track voll"""
    env = SimPyEnvironmentAdapter()

    track = WorkshopTrack(
        id="TRACK01",
        capacity=1,  # Nur 1 Wagen gleichzeitig
        retrofit_time_min=30,
        resource=simpy.Resource(env.simpy_env, capacity=1)
    )

    workshop = Workshop(id="test", tracks=[track])
    adapter = WorkshopSimPyAdapter(workshop=workshop, env=env)

    wagons = [
        Wagon(id="W001", train_id="T001"),
        Wagon(id="W002", train_id="T001"),
    ]

    # Starte beide Prozesse gleichzeitig
    for wagon in wagons:
        env.process(adapter.retrofit_process(wagon))

    env.run(until=100)

    # W001 sollte bei 30 min fertig sein
    assert wagons[0].retrofit_end_time == 30.0

    # W002 sollte warten müssen und bei 60 min fertig sein
    assert wagons[1].waiting_time == 30.0
    assert wagons[1].retrofit_end_time == 60.0
```

---

## Coverage-Ziele

### Gesamt-Coverage
```bash
uv run pytest --cov=src --cov-report=html --cov-report=term-missing
```

**Ziele:**
- Gesamt: > 80%
- Configuration Context: > 90%
- Workshop Context: > 85%
- Simulation Control Context: > 75%

### Coverage-Ausnahmen
```python
# .coveragerc
[run]
omit =
    */tests/*
    */conftest.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: uv sync

    - name: Run tests with coverage
      run: uv run pytest --cov=src --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

    - name: Check coverage threshold
      run: |
        uv run coverage report --fail-under=80
```

---

## Performance Tests

```python
# tests/performance/test_performance.py
import pytest
import time
from pathlib import Path
from src.simulation.service import SimulationService
from src.configuration.service import ConfigurationService

@pytest.mark.performance
def test_small_scenario_performance():
    """Test Small Scenario < 5 Sekunden"""
    config_service = ConfigurationService()
    config = config_service.load_scenario(Path("config/examples/small_scenario"))

    simulation_service = SimulationService(config)

    start = time.time()
    results = simulation_service.run()
    duration = time.time() - start

    assert duration < 5.0, f"Small scenario took {duration:.2f}s (should be < 5s)"

@pytest.mark.performance
def test_medium_scenario_performance():
    """Test Medium Scenario < 30 Sekunden"""
    config_service = ConfigurationService()
    config = config_service.load_scenario(Path("config/examples/medium_scenario"))

    simulation_service = SimulationService(config)

    start = time.time()
    results = simulation_service.run()
    duration = time.time() - start

    assert duration < 30.0, f"Medium scenario took {duration:.2f}s (should be < 30s)"
```

**Ausführung:**
```bash
# Nur Performance Tests
uv run pytest -m performance

# Alle Tests außer Performance
uv run pytest -m "not performance"
```

---

**Navigation:** [← File Formats](07-mvp-file-formats.md) | [Deployment →](09-mvp-deployment.md)
