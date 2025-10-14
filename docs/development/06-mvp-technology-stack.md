# PopUpSim MVP - Technology Stack

## Übersicht

Diese Datei definiert den kompletten Technology Stack für den MVP mit Begründungen für jede Technologie-Entscheidung.

---

## Core Technologies

### Python 3.13
**Verwendung:** Hauptprogrammiersprache
**Begründung:**
- Experimenteller Free-Threaded Mode (nogil)
- Verbesserte Performance (JIT-Compiler in Entwicklung)
- Erweiterte Type Hints und Error Messages
- Alle Features von 3.11/3.12 verfügbar
- Zukunftssicher für langfristige Entwicklung

**Alternativen erwogen:**
- Python 3.11: Stabil, aber weniger Performance
- Python 3.12: Gute Balance, aber 3.13 bietet mehr

---

## Dependency Management

### uv
**Verwendung:** Package Manager und Virtual Environment
**Begründung:**
- 10-100x schneller als pip
- Integriertes Virtual Environment Management
- Kompatibel mit pyproject.toml
- Lock-File für reproduzierbare Builds

**Installation:**
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verwendung:**
```bash
# Projekt initialisieren
uv init

# Dependencies installieren
uv add pydantic simpy pandas matplotlib pytest

# Virtual Environment aktivieren
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Script ausführen
uv run python main.py
```

**pyproject.toml:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "PopUp-Sim"
description = "Freight rail transport simulation tool for Digital Automatic Coupler retrofit"
version = "0.1.0"
license = "Apache-2.0"
readme = "README.md"
requires-python = ">=3.13"
authors = [
    { name = "Jan-Hendrik Wendisch", email = "jan-hendrik.wendisch@deutschebahn.com" },
    { name = "Volker Kuehn", email = "volker.kuehn@deutschebahn.com" }
]
keywords = ["railway", "digital automatic coupler", "simulation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
]
dependencies = []

[tool.hatch.build.targets.wheel]
packages = ["backend/src"]

[dependency-groups]
dev = [
    "mypy>=1.18.1",
    "pre-commit>=4.3.0",
    "pre-commit-hooks>=6.0.0",
    "pylint>=3.3.8",
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
    "pytest-mock>=3.15.1",
    "ruff>=0.13.0",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.format]
quote-style = "single"
indent-style = "tab"
docstring-code-format = true

[tool.ruff.lint]
select = ["F", "B", "S", "C4", "DTZ", "ARG", "I", "SIM", "N", "C90", "PLR09", "RUF"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 5
max-branches = 12
max-returns = 6
max-statements = 50

[tool.pylint.format]
max-line-length = 120

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
files = ["backend/src", "backend/tests"]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--cov=popup_sim",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=90",
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (external APIs)",
    "pending: Tests written before implementation (TDD)",
]

[tool.coverage.run]
source = ["backend/src"]
omit = ["backend/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
show_missing = true
```

---

## Core Libraries

### Pydantic 2.5+
**Verwendung:** Data Validation und Models
**Begründung:**
- Type-safe Data Models
- Automatische Validierung
- JSON Schema Generation
- Exzellente Performance (Rust-basiert)
- IDE-Unterstützung

**Beispiel:**
```python
from pydantic import BaseModel, Field

class WorkshopTrackConfig(BaseModel):
    id: str = Field(pattern=r"^TRACK\d{2}$")
    capacity: int = Field(gt=0, le=20)
    retrofit_time_min: int = Field(ge=10, le=300)
```

**Alternativen erwogen:**
- Dataclasses: Keine Validierung
- attrs: Weniger Features
- marshmallow: Langsamer

---

### SimPy 4.1+
**Verwendung:** Discrete Event Simulation Engine
**Begründung:**
- Etablierte Python DES Library
- Generator-basierte Processes
- Resource Management
- Gute Dokumentation
- Aktive Community

**Beispiel:**
```python
import simpy

def process(env):
    yield env.timeout(10)
    print(f"Done at {env.now}")

env = simpy.Environment()
env.process(process(env))
env.run()
```

**Alternativen erwogen:**
- Salabim: Weniger bekannt
- Custom DES: Zu viel Aufwand für MVP

---

### Pandas 2.1+
**Verwendung:** Data Analysis und CSV Export
**Begründung:**
- Standard für Data Analysis in Python
- Einfache CSV/Excel I/O
- Aggregation und Grouping
- Integration mit Matplotlib

**Beispiel:**
```python
import pandas as pd

df = pd.DataFrame([
    {"wagon_id": "W001", "waiting_time": 12.5},
    {"wagon_id": "W002", "waiting_time": 8.3}
])

df.to_csv("results.csv", index=False)
```

**Alternativen erwogen:**
- Polars: Zu neu, weniger bekannt
- Native CSV: Zu viel manueller Code

---

### Matplotlib 3.8+
**Verwendung:** Visualisierung und Charts
**Begründung:**
- Standard für Plotting in Python
- Viele Chart-Typen
- Export zu PNG/PDF
- Integration mit Pandas

**Beispiel:**
```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(timestamps, throughput)
plt.xlabel("Time (hours)")
plt.ylabel("Throughput (wagons/hour)")
plt.title("Throughput over Time")
plt.savefig("throughput.png")
```

**Alternativen erwogen:**
- Plotly: Zu komplex für MVP
- Seaborn: Wrapper um Matplotlib, nicht nötig

---

## Development Tools

### pytest 7.4+
**Verwendung:** Testing Framework
**Begründung:**
- Standard für Python Testing
- Fixtures für Setup/Teardown
- Parametrized Tests
- Coverage Integration

**Beispiel:**
```python
import pytest

def test_wagon_waiting_time():
    wagon = Wagon(
        id="W001",
        arrival_time=10.0,
        retrofit_start_time=15.0
    )
    assert wagon.waiting_time == 5.0

@pytest.fixture
def workshop():
    return Workshop(id="test", tracks=[...])

def test_workshop_capacity(workshop):
    assert len(workshop.tracks) > 0
```

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

---

### Black
**Verwendung:** Code Formatter
**Begründung:**
- Opinionated Formatter (keine Diskussionen)
- Konsistenter Code-Stil
- IDE-Integration

**Verwendung:**
```bash
uv run black src/ tests/
```

---

### Ruff
**Verwendung:** Linter (ersetzt Flake8, isort, etc.)
**Begründung:**
- 10-100x schneller als Flake8
- Kombiniert mehrere Tools
- Auto-Fix für viele Issues

**Verwendung:**
```bash
uv run ruff check src/ tests/
uv run ruff check --fix src/ tests/
```

---

### mypy
**Verwendung:** Static Type Checker
**Begründung:**
- Findet Type-Fehler vor Runtime
- Bessere IDE-Unterstützung
- Dokumentation durch Types

**Verwendung:**
```bash
uv run mypy src/
```

---

## File Formats

### JSON
**Verwendung:** Konfigurationsdateien (scenario.json)
**Begründung:**
- Hierarchische Struktur
- Native Python Support
- Lesbar für Menschen
- Validierung mit JSON Schema

**Beispiel:**
```json
{
  "duration_hours": 8,
  "random_seed": 42,
  "workshop": {
    "tracks": [...]
  }
}
```

---

### CSV
**Verwendung:** Tabellarische Daten (tracks, results)
**Begründung:**
- Einfach zu editieren (Excel)
- Standard für Data Exchange
- Pandas Integration

**Beispiel:**
```csv
track_id,capacity,retrofit_time_min
TRACK01,5,30
TRACK02,3,45
```

---

## Project Structure

```
popupsim-mvp/
├── pyproject.toml          # uv configuration
├── uv.lock                 # Lock file
├── README.md
├── .gitignore
├── .python-version         # 3.13
│
├── src/
│   ├── __init__.py
│   ├── main.py             # Entry point
│   │
│   ├── configuration/      # Configuration Context
│   │   ├── __init__.py
│   │   ├── models.py       # Pydantic models
│   │   ├── service.py      # Configuration service
│   │   └── validation.py   # Validation logic
│   │
│   ├── workshop/           # Workshop Context
│   │   ├── __init__.py
│   │   ├── models.py       # Domain models
│   │   ├── service.py      # Workshop service
│   │   └── simpy_adapter.py # SimPy integration
│   │
│   └── simulation/         # Simulation Control Context
│       ├── __init__.py
│       ├── service.py      # Simulation orchestration
│       ├── kpi_service.py  # KPI calculation
│       └── output_service.py # Output generation
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # pytest fixtures
│   │
│   ├── unit/
│   │   ├── test_configuration.py
│   │   ├── test_workshop.py
│   │   └── test_simulation.py
│   │
│   └── integration/
│       └── test_end_to_end.py
│
├── config/
│   └── examples/
│       ├── small_scenario/
│       ├── medium_scenario/
│       └── large_scenario/
│
└── docs/
    └── architecture/
        └── mvp/
```

---

## Development Workflow

### Setup
```bash
# 1. Clone Repository
git clone <repo-url>
cd popupsim-mvp

# 2. Install uv (falls nicht installiert)
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install Dependencies
uv sync

# 4. Activate Virtual Environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
```

### Development
```bash
# Run Tests
uv run pytest

# Run with Coverage
uv run pytest --cov=src --cov-report=html

# Format Code
uv run black src/ tests/

# Lint Code
uv run ruff check src/ tests/

# Type Check
uv run mypy src/

# Run Simulation
uv run python src/main.py --config config/examples/small_scenario --output results/
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest
```

---

## CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Set up Python
      run: uv python install 3.13

    - name: Install dependencies
      run: uv sync

    - name: Run tests
      run: uv run pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Performance Targets

| Metric | MVP Target | Vollversion Target |
|--------|------------|-------------------|
| **Simulation Speed** | 1000 Wagen < 30s | 10000 Wagen < 10s |
| **Memory Usage** | < 500 MB | < 2 GB |
| **Startup Time** | < 2s | < 1s |
| **Test Coverage** | > 80% | > 90% |
| **Type Coverage** | > 90% | 100% |

---

## Migration Path (Post-MVP)

### Vollversion: Zusätzliche Libraries

```toml
[project.optional-dependencies]
full = [
    "fastapi>=0.104.0",      # REST API
]
```

---

**Navigation:** [← Data Flow](05-mvp-data-flow.md) | [File Formats →](07-mvp-file-formats.md)
