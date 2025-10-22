# 5. Bausteinsicht (MVP)

## 5.1 MVP System-Überblick

### MVP Container Diagramm

```mermaid
graph TB
    subgraph "PopUpSim MVP"
        Main[main.py<br/>Entry Point]
        Core[Core Logic<br/>Business Layer]
        IO[File I/O<br/>Data Layer]
    end

    subgraph "File System"
        Input[Input Files<br/>JSON/CSV]
        Output[Output Files<br/>CSV/PNG]
    end

    Main --> Core
    Core --> IO
    IO --> Input
    IO --> Output

    classDef container fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef files fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#fff

    class Main,Core,IO container
    class Input,Output files
```

## 5.2 MVP Layered Architecture

### MVP Layer Struktur

```mermaid
graph TB
    subgraph "MVP Layers"
        subgraph "Presentation"
            CLI[CLI Interface]
        end

        subgraph "Business Logic"
            ConfigService[Configuration Service]
            WorkshopService[Workshop Service]
            SimulationService[Simulation Service]
        end

        subgraph "Data Access"
            JSONReader[JSON Reader]
            CSVWriter[CSV Writer]
        end

        subgraph "Infrastructure"
            SimPy[SimPy Framework]
            Matplotlib[Matplotlib]
        end
    end

    CLI --> ConfigService
    CLI --> SimulationService
    ConfigService --> JSONReader
    WorkshopService --> SimPy
    SimulationService --> CSVWriter
    SimulationService --> Matplotlib

    classDef presentation fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef business fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    classDef data fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#fff
    classDef infrastructure fill:#9e9e9e,stroke:#616161,stroke-width:2px,color:#fff

    class CLI presentation
    class ConfigService,WorkshopService,SimulationService business
    class JSONReader,CSVWriter data
    class SimPy,Matplotlib infrastructure
```

## 5.3 MVP Context-Struktur

### Configuration Context (MVP)

```python
class ConfigurationService:
    def load_scenario(self, path: str) -> ScenarioConfig:
        # Load JSON/CSV files
        pass

    def validate_config(self, config: ScenarioConfig) -> List[str]:
        # Basic validation
        pass
```

### Workshop Context (MVP)

```python
class WorkshopService:
    def setup_workshop(self, config: WorkshopConfig) -> Workshop:
        # Create workshop with stations
        pass

    def run_simulation(self, env: simpy.Environment) -> None:
        # SimPy processes
        pass
```

### Simulation Control Context (MVP)

```python
class SimulationService:
    def orchestrate_simulation(self) -> SimulationResults:
        # Coordinate all contexts
        pass

    def generate_output(self, results: SimulationResults) -> None:
        # CSV + Matplotlib output
        pass
```

---

**Navigation:** [← MVP Lösungsstrategie](04-solution-strategy.md) | [MVP Laufzeitsicht →](06-runtime.md)
