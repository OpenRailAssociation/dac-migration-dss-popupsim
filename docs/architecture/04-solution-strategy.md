# 4. Lösungsstrategie (MVP)

## 4.1 MVP Architekturmuster

### Layered Architecture (MVP)

**Entscheidung:** Einfache Layered Architecture für schnelle MVP-Entwicklung

```mermaid
graph TB
    subgraph "MVP Layered Architecture"
        subgraph "Presentation Layer"
            CLI[Command Line Interface]
            FileOutput[File Output CSV/PNG]
        end

        subgraph "Business Logic Layer"
            ConfigService[Configuration Service]
            WorkshopService[Workshop Service]
            SimulationService[Simulation Service]
        end

        subgraph "Data Access Layer"
            FileReader[File Reader JSON/CSV]
            FileWriter[File Writer CSV/JSON]
        end

        subgraph "Infrastructure Layer"
            SimPy[SimPy Framework]
            Matplotlib[Matplotlib]
            FileSystem[File System]
        end
    end

    CLI --> ConfigService
    CLI --> SimulationService
    ConfigService --> FileReader
    WorkshopService --> SimPy
    SimulationService --> FileWriter
    FileOutput --> Matplotlib

    classDef presentation fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef business fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    classDef data fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#fff
    classDef infrastructure fill:#9e9e9e,stroke:#616161,stroke-width:2px,color:#fff

    class CLI,FileOutput presentation
    class ConfigService,WorkshopService,SimulationService business
    class FileReader,FileWriter data
    class SimPy,Matplotlib,FileSystem infrastructure
```

## 4.2 MVP Bounded Context Strategie

### 3 Vereinfachte Contexts (MVP)

```mermaid
graph TB
    subgraph "MVP PopUpSim - 3 Contexts"
        CC[Configuration Context<br/>JSON/CSV Import]
        WS[Workshop Context<br/>DAK-Umrüstung + SimPy]
        SC[Simulation Control Context<br/>Orchestration + Output]
    end

    CC -->|Direct Calls| WS
    WS -->|Direct Calls| SC

    classDef context fill:#e1f5fe,stroke:#01579b,stroke-width:2px

    class CC,WS,SC context
```

## 4.3 Migration Path: MVP → Vollversion

```mermaid
graph LR
    A[MVP Phase:<br/>Layered Architecture] --> B[Transition Phase:<br/>Hexagonal Preparation]
    B --> C[Full Version:<br/>Hexagonal + Events]

    A1[3 Contexts<br/>Direct Calls] --> B1[Interface Preparation]
    B1 --> C1[7 Contexts<br/>Event-driven]

    A2[File System<br/>CSV/JSON] --> B2[Repository Pattern]
    B2 --> C2[Database<br/>Event Store]
```

---

**Navigation:** [← MVP Kontextabgrenzung](03-context.md) | [MVP Bausteinsicht →](05-building-blocks.md)
