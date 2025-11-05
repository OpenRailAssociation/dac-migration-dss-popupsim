# 7. Verteilungssicht (MVP)

## 7.1 MVP Deployment-Überblick

### MVP Desktop Application

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "PopUpSim MVP"
            Python[Python 3.11+<br/>Runtime Environment]
            App[PopUpSim Application<br/>main.py + src/]
            Config[Configuration Files<br/>config/]
            Output[Output Directory<br/>output/]
        end

        subgraph "Dependencies"
            SimPy[SimPy Framework]
            Matplotlib[Matplotlib]
            Pandas[Pandas]
        end
    end

    App --> Python
    App --> Config
    App --> Output
    Python --> SimPy
    Python --> Matplotlib
    Python --> Pandas

    classDef app fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef deps fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#fff
    classDef files fill:#9e9e9e,stroke:#616161,stroke-width:2px,color:#fff

    class Python,App app
    class SimPy,Matplotlib,Pandas deps
    class Config,Output files
```

## 7.2 MVP Installation

### MVP Setup Process

| Schritt | Kommando | Beschreibung |
|---------|----------|--------------|
| **1. Python Setup** | `python --version` | Python 3.11+ erforderlich |
| **2. uv Installation** | `pip install uv` | uv Paketmanager installieren |
| **3. Dependencies** | `uv sync` | Pakete installieren und Lock-Datei erstellen |
| **4. Test Run** | `uv run python main.py --help` | Installation testen |

### MVP pyproject.toml

```toml
[project]
name = "popupsim-mvp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "simpy>=4.0.1",
    "matplotlib>=3.7.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 7.3 MVP Verzeichnisstruktur

### MVP File Layout

```
popupsim-mvp/
├── main.py                     # Entry Point
├── pyproject.toml              # uv Dependencies
├── uv.lock                     # uv Lock File
├── README.md                   # Setup Instructions
├── config/                     # Configuration Files
│   ├── scenario.json          # Simulation Parameters
│   ├── workshop_config.csv    # Workshop Setup
│   └── train_schedule.csv     # Train Schedule
├── src/                        # Source Code
│   ├── __init__.py
│   ├── configuration/         # Configuration Context
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── models.py
│   ├── workshop/              # Workshop Context
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── models.py
│   ├── simulation/            # Simulation Control Context
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── output.py
│   └── shared/                # Shared Utilities
│       ├── __init__.py
│       └── file_utils.py
├── output/                     # Generated Results
│   ├── simulation_results.csv
│   ├── kpi_charts.png
│   └── simulation_log.json
├── tests/                      # Unit Tests
│   ├── __init__.py
│   ├── test_configuration.py
│   ├── test_workshop.py
│   └── test_simulation.py
└── docs/                       # Documentation
    └── mvp_usage.md
```

## 7.4 MVP Execution Environment

### MVP Runtime Requirements

| Komponente | Minimum | Empfohlen | Zweck |
|------------|---------|-----------|-------|
| **Python** | 3.13 | 3.12 | Runtime Environment |
| **RAM** | 2 GB | 4 GB | Simulation Data |
| **CPU** | 2 Cores | 4 Cores | SimPy Processing |
| **Storage** | 500 MB | 1 GB | Code + Results |
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest | Cross-Platform |

### MVP Command Line Interface

```bash
# Einfache Ausführung
uv run python main.py

# Mit benutzerdefinierter Konfiguration
uv run python main.py --config custom_config/

# Mit Ausgabeverzeichnis
uv run python main.py --output results/

# Debug-Modus
uv run python main.py --debug --verbose

# Hilfe
uv run python main.py --help
```

## 7.5 MVP Configuration Management

### MVP Config File Locations

```mermaid
graph TB
    subgraph "Configuration Sources"
        Default[Default Config<br/>Built-in Values]
        Files[Config Files<br/>config/ directory]
        CLI[Command Line<br/>Arguments]
    end

    subgraph "Configuration Merge"
        Merger[Config Merger<br/>Priority Order]
    end

    subgraph "Final Config"
        Runtime[Runtime Configuration<br/>Used by Simulation]
    end

    Default --> Merger
    Files --> Merger
    CLI --> Merger
    Merger --> Runtime

    classDef source fill:#e3f2fd
    classDef process fill:#e8f5e8
    classDef result fill:#fff3e0

    class Default,Files,CLI source
    class Merger process
    class Runtime result
```

### MVP Configuration Priority

1. **Command Line Arguments** (Highest Priority)
2. **Config Files** (config/ directory)
3. **Default Values** (Built-in)

## 7.6 MVP Output Management

### MVP Result Files

```mermaid
graph TB
    subgraph "MVP Output Generation"
        Simulation[Simulation Results]

        subgraph "Output Formats"
            CSV[CSV Files<br/>Structured Data]
            PNG[PNG Charts<br/>Matplotlib Plots]
            JSON[JSON Logs<br/>Event Timeline]
        end

        subgraph "Output Locations"
            OutputDir[output/<br/>Default Directory]
            CustomDir[Custom Directory<br/>--output parameter]
        end
    end

    Simulation --> CSV
    Simulation --> PNG
    Simulation --> JSON

    CSV --> OutputDir
    PNG --> OutputDir
    JSON --> OutputDir

    CSV -.-> CustomDir
    PNG -.-> CustomDir
    JSON -.-> CustomDir

    classDef simulation fill:#4caf50,stroke:#2e7d32
    classDef format fill:#ff9800,stroke:#e65100
    classDef location fill:#9e9e9e,stroke:#616161

    class Simulation simulation
    class CSV,PNG,JSON format
    class OutputDir,CustomDir location
```

## 7.7 MVP Error Handling & Logging

### MVP Log Configuration

```python
# MVP Logging Setup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/simulation.log'),
        logging.StreamHandler()  # Konsolenausgabe
    ]
)
```

### MVP Error Recovery

| Fehlertyp | MVP Verhalten | Wiederherstellungsaktion |
|-----------|---------------|-------------------------|
| **Konfigurationsfehler** | Beenden mit Fehlermeldung | Konfigurationsdateien korrigieren |
| **Simulationsfehler** | Teilergebnisse speichern | Systemressourcen prüfen |
| **Ausgabefehler** | Fortfahren ohne fehlgeschlagene Ausgabe | Berechtigungen prüfen |
| **Abhängigkeitsfehler** | Beenden mit Installationshilfe | Fehlende Pakete installieren |

## 7.8 MVP Performance Monitoring

### MVP Resource Usage

```mermaid
graph TB
    subgraph "MVP Performance Metrics"
        subgraph "Memory Usage"
            ConfigMem[Config Loading<br/>~1 MB]
            SimMem[Simulation Runtime<br/>~10-50 MB]
            OutputMem[Output Generation<br/>~5 MB]
        end

        subgraph "CPU Usage"
            SetupCPU[Setup Phase<br/>Low CPU]
            SimCPU[Simulation Phase<br/>High CPU]
            OutputCPU[Output Phase<br/>Medium CPU]
        end

        subgraph "Disk I/O"
            ReadIO[Config Reading<br/>Sequential]
            WriteIO[Result Writing<br/>Sequential]
        end
    end

    classDef memory fill:#e3f2fd
    classDef cpu fill:#e8f5e8
    classDef disk fill:#fff3e0

    class ConfigMem,SimMem,OutputMem memory
    class SetupCPU,SimCPU,OutputCPU cpu
    class ReadIO,WriteIO disk
```

## 7.9 MVP Distribution Strategy

### MVP Packaging Options

| Option | Vorteile | Nachteile | Anwendungsfall |
|--------|----------|-----------|----------------|
| **Source Code** | Einfache Entwicklung, volle Kontrolle | Benötigt Python-Setup | Entwicklungsteam |
| **Zip-Archiv** | Einfache Verteilung | Benötigt noch Python | Internes Testen |
| **PyInstaller** | Einzelne ausführbare Datei | Große Dateigröße | Endbenutzer (Zukunft) |
| **Docker** | Konsistente Umgebung | Overhead | Cloud-Deployment (Zukunft) |

### MVP Distribution Flow

```mermaid
graph LR
    A[Source Code<br/>Git Repository] --> B[Zip Archive<br/>Release Package]
    B --> C[PyInstaller<br/>Executable]
    C --> D[Docker Image<br/>Container]

    A -.->|MVP Current| B
    B -.->|Future| C
    C -.->|Future| D

    classDef current fill:#4caf50,stroke:#2e7d32
    classDef future fill:#ff9800,stroke:#e65100

    class A,B current
    class C,D future
```

---

**Navigation:** [← MVP Laufzeitsicht](06-runtime.md) | [MVP Querschnittliche Konzepte →](08-concepts.md)
