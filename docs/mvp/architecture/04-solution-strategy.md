# 4. Solution Strategy (MVP)

## 4.1 Top-Level Decomposition

**Primary Decomposition:** Domain-driven design with 3 bounded contexts.

**Rationale:** Separating concerns by domain responsibility enables:
- Clear ownership of functionality
- Independent development and testing
- Easier migration to full version with all necessary contexts
- Maintainable codebase despite tight MVP timeline

```mermaid
graph TB
    subgraph "PopUpSim MVP - 3 Bounded Contexts"
        CC["<b>Configuration Context</b><br/>Responsibility: Input validation & parsing<br/>Technology: Pydantic + Pandas<br/>Input: JSON/CSV files<br/>Output: Validated domain objects"]

        SD["<b>Workshop Operations Context</b><br/>Responsibility: Simulation execution & analysis<br/>Technology: SimPy + Analysis Engine<br/>Input: Configuration objects<br/>Output: Simulation events & KPI data"]

        SC["<b>Analysis & Reporting Context</b><br/>Responsibility: Orchestration & output formatting<br/>Technology: Matplotlib + CSV export<br/>Input: Simulation events & KPI data<br/>Output: Aggregated reports & charts"]
    end

    CC -->|"Direct method calls<br/>(validated config objects)"| SD
    SD -->|"Direct method calls<br/>(simulation results)"| SC

    classDef context fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    class CC,SD,SC context
```

### Context Responsibilities

| Context | Core Responsibility | Key Components | MVP Simplification |
|---------|-------------------|----------------|--------------------|
| **Configuration** | Parse and validate input files | File readers, Pydantic models, validators | Single context vs. multiple specialized contexts in full version (under analysis) |
| **Workshop Operations** | Execute discrete event simulation and real-time analysis | SimPy processes, analysis engine, domain entities (wagons, tracks, workshops), business rules | Simplified domain model, direct calls vs. event-driven |
| **Analysis & Reporting** | Orchestrate simulation and aggregate output | KPI aggregators, output formatters, chart generators | File-based output vs. web interface in full version |

## 4.2 Technology Decisions

**Key Technology Choices:**

| Technology | Purpose | Rationale | ADR |
|------------|---------|-----------|-----|
| **SimPy** | Discrete event simulation | Proven in 3-Länderhack POC, deterministic, Python-native | [ADR MVP-001](09-architecture-decisions.md#adr-mvp-001-simpy-for-discrete-event-simulation) |
| **Pydantic** | Data validation | Type safety, excellent validation, matches project type hint requirements | [ADR MVP-003](09-architecture-decisions.md#adr-mvp-003-pydantic-for-data-validation) |
| **Matplotlib** | Visualization | Simple offline charts, no web server required, sufficient for MVP | [ADR MVP-004](09-architecture-decisions.md#adr-mvp-004-matplotlib-for-visualization) |
| **File-based storage** | Data persistence | Local deployment, small data volume, no database setup | [ADR MVP-002](09-architecture-decisions.md#adr-mvp-002-file-based-data-storage) |

## 4.3 Technical Architecture Pattern

**Decision:** Layered architecture within each bounded context ([ADR MVP-005](09-architecture-decisions.md#adr-mvp-005-layered-architecture))

**Rationale:** Simple layered structure enables:
- Rapid MVP development (5-week timeline)
- Clear separation of concerns within contexts
- Easy testing of business logic
- Foundation for hexagonal architecture in full version

```mermaid
graph TB
    subgraph "MVP Layered Architecture"
        subgraph "Presentation Layer"
            CLI[Command Line Interface]
            FileOutput[File Output CSV/PNG]
        end

        subgraph "Business Logic Layer"
            ConfigService[Configuration Service]
            DomainService[Simulation Domain Service]
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
    DomainService --> SimPy
    SimulationService --> FileWriter
    FileOutput --> Matplotlib

    classDef presentation fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef business fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    classDef data fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#fff
    classDef infrastructure fill:#9e9e9e,stroke:#616161,stroke-width:2px,color:#fff

    class CLI,FileOutput presentation
    class ConfigService,DomainService,SimulationService business
    class FileReader,FileWriter data
    class SimPy,Matplotlib,FileSystem infrastructure
```

### Layered Structure (Applied to Each Context)

| Layer | Responsibility | MVP Implementation |
|-------|----------------|--------------------|
| **Presentation** | User interaction, file I/O | Command line interface, file readers/writers |
| **Business Logic** | Domain logic, simulation rules | Services, domain entities, SimPy processes |
| **Data Access** | Data persistence | File system operations (JSON/CSV) |
| **Infrastructure** | External frameworks | SimPy, Matplotlib, Pydantic, Pandas |

## 4.4 Context Integration Strategy

**Decision:** Direct method calls between contexts ([ADR MVP-007](09-architecture-decisions.md#adr-mvp-007-direct-method-calls-between-contexts))

**Rationale:**
- Simplest integration for MVP (no message bus, no events)
- Synchronous execution matches file-based workflow
- Clear call chain: Configuration → Workshop Operations → Analysis & Reporting
- Easy to refactor to event-driven in full version

**Benefits:**
- Fast development and easy debugging
- No infrastructure overhead (no message bus, no event store)
- Clear execution flow for troubleshooting

**Limitations:**
- Tight coupling between contexts makes independent deployment impossible
- Cannot scale to distributed architecture
- Refactoring required for event-driven full version

## 4.5 Migration Path: MVP → Full Version

```mermaid
graph LR
    A[MVP Phase:<br/>Layered Architecture] --> B[Transition Phase:<br/>Hexagonal Preparation]
    B --> C[Full Version:<br/>Hexagonal + Events]

    A1[3 Contexts<br/>Direct Calls] --> B1[Interface Preparation]
    B1 --> C1[Multiple Contexts<br/>Event-driven<br/>Number contexts tbd]

    A2[File System<br/>CSV/JSON] --> B2[Repository Pattern]
    B2 --> C2[Event Store]
```

---


