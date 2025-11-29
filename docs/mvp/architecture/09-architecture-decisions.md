# 9. Architecture Decisions (MVP)

## 9.1 MVP Architecture Decisions Overview

### MVP ADR Status

| ADR | Title | Status | Impact |
|-----|-------|--------|--------|
| **ADR-001** | [Hexagonal Pipeline Architecture](decisions/ADR-001-hexagonal-pipeline-architecture.md) | ✅ Accepted | Clean separation of concerns |
| **ADR-002** | [4-Layer Validation Framework](decisions/ADR-002-4-layer-validation-framework.md) | ✅ Accepted | Comprehensive input validation |
| **ADR-003** | [Field Name Standardization](decisions/ADR-003-field-name-standardization.md) | ✅ Accepted | Consistent naming conventions |
| **ADR-004** | [3 Bounded Context Architecture](decisions/ADR-004-3-bounded-context-architecture.md) | ✅ Accepted | Domain separation |
| **ADR-005** | [Type Hints Mandatory](decisions/ADR-005-type-hints-mandatory.md) | ✅ Accepted | Code quality and safety |
| **ADR-006** | [SimPy for Discrete Event Simulation](decisions/ADR-006-simpy-discrete-event-simulation.md) | ✅ Accepted | Proven simulation framework |
| **ADR-007** | [File-Based Data Storage](decisions/ADR-007-file-based-data-storage.md) | ✅ Accepted | Simple deployment |
| **ADR-008** | [Pydantic for Data Validation](decisions/ADR-008-pydantic-data-validation.md) | ✅ Accepted | Type safety and validation |
| **ADR-009** | [Matplotlib for Visualization](decisions/ADR-009-matplotlib-visualization.md) | ✅ Accepted | Simple offline charts |
| **ADR-010** | [Layered Architecture](decisions/ADR-010-layered-architecture.md) | ✅ Accepted | Rapid development |
| **ADR-011** | [3 Bounded Contexts](decisions/ADR-011-3-bounded-contexts.md) | ✅ Accepted | Minimal viable domain decomposition |
| **ADR-012** | [Direct Method Calls](decisions/ADR-012-direct-method-calls.md) | ✅ Accepted | Simple integration |
| **ADR-013** | [Hexagonal Architecture for Data Sources](decisions/ADR-013-hexagonal-data-sources.md) | ✅ Accepted | Multi-format input support |

**Note**: Full version architectural decisions (ADR-001 through ADR-018) are documented in [../../full-version/architecture/decisions/](../../full-version/architecture/decisions/).

## 9.2 MVP Architecture Decisions

All MVP architectural decisions are documented as separate ADR files in the [decisions](decisions/) directory. This section provides an overview and links to the detailed decisions.

### Architecture Pattern Decisions
- **[ADR-001: Hexagonal Pipeline Architecture](decisions/ADR-001-hexagonal-pipeline-architecture.md)** - Clean separation of concerns
- **[ADR-004: 3 Bounded Context Architecture](decisions/ADR-004-3-bounded-context-architecture.md)** - Domain separation
- **[ADR-010: Layered Architecture](decisions/ADR-010-layered-architecture.md)** - Simple architecture for rapid development
- **[ADR-011: 3 Bounded Contexts](decisions/ADR-011-3-bounded-contexts.md)** - Minimal viable domain decomposition
- **[ADR-012: Direct Method Calls](decisions/ADR-012-direct-method-calls.md)** - Simple integration between contexts

### Technology Decisions
- **[ADR-006: SimPy for Discrete Event Simulation](decisions/ADR-006-simpy-discrete-event-simulation.md)** - Proven simulation framework
- **[ADR-007: File-Based Data Storage](decisions/ADR-007-file-based-data-storage.md)** - Simple deployment without database
- **[ADR-008: Pydantic for Data Validation](decisions/ADR-008-pydantic-data-validation.md)** - Type safety and validation
- **[ADR-009: Matplotlib for Visualization](decisions/ADR-009-matplotlib-visualization.md)** - Simple offline charts

### Quality & Standards Decisions
- **[ADR-002: 4-Layer Validation Framework](decisions/ADR-002-4-layer-validation-framework.md)** - Comprehensive input validation
- **[ADR-003: Field Name Standardization](decisions/ADR-003-field-name-standardization.md)** - Consistent naming conventions
- **[ADR-005: Type Hints Mandatory](decisions/ADR-005-type-hints-mandatory.md)** - Code quality and safety

### Integration Decisions
- **[ADR-013: Hexagonal Architecture for Data Sources](decisions/ADR-013-hexagonal-data-sources.md)** - Multi-format input supportr testing
- **Maintainability**: Clear separation between data access and business logic
- **Extensibility**: New data sources without changing core logic
- **Type safety**: Consistent DTOs across all adapters

**Implementation:**
- **DataSourcePort**: Interface defining adapter contract
- **JsonDataSourceAdapter**: Wraps existing JSON functionality
- **CsvDataSourceAdapter**: New CSV directory support
- **DataSourceFactory**: Auto-detects source type
- **ScenarioLoader**: Orchestrates using adapters

**Alternatives Considered:**
- **Hexagonal Architecture** ✅ Chosen
- **Direct CSV parsing**: Tight coupling, hard to test
- **Single JSON format**: Doesn't meet CSV requirement
- **Full hexagonal everywhere**: Too complex for MVP timeline

**Consequences:**
- **Positive**: Multi-format support, future-ready, testable, maintainable
- **Negative**: Additional complexity (justified by requirements)
- **Benefit**: Foundation for full hexagonal architecture migration

**CSV Directory Structure:**
```
csv_scenario/
├── scenario.csv      # Basic metadata (ID, dates, seed)
├── trains.csv        # Train schedule with arrival times
├── wagons.csv        # Wagon data linked to trains
├── workshops.csv     # Workshop configuration
├── tracks.csv        # Track definitions
├── routes.csv        # Route definitions
└── locomotives.csv   # Locomotive fleet data
```

**Usage Examples:**
```python
# Auto-detect source type
loader = ScenarioLoader()
scenario = loader.load_scenario('path/to/csv_directory')  # CSV
scenario = loader.load_scenario('path/to/scenario.json')  # JSON

# Use specific adapter
csv_adapter = CsvDataSourceAdapter()
scenario = csv_adapter.load_scenario('csv_directory')
```

---

## 9.3 Rejected Alternatives

### Rejected Architecture Options

| Alternative | Reason for Rejection | MVP Decision |
|-------------|---------------------|--------------|
| **Hexagonal Architecture** | Too complex for 5-week timeline | Layered Architecture |
| **Microservices** | Deployment complexity | Monolith |
| **Event-driven** | Implementation effort | Direct calls |
| **Web Frontend** | No frontend developer | Matplotlib |
| **Database** | Installation complexity | Files |

### Rejected Technology Options

| Technology | Reason for Rejection | MVP Alternative |
|-------------|---------------------|-----------------|
| **FastAPI** | Web API not required | Direct Python calls |
| **PostgreSQL** | Database setup too complex | CSV/JSON files |
| **Docker** | Container overhead | Native Python |
| **Vue.js** | Frontend development | Matplotlib PNG |
| **WebSocket** | Real-time not required | Batch processing |

---

## 9.4 Migration Path

### MVP → Full Version Evolution

| Aspect | MVP (Current) | Transition (Prepared) | Full Version (Future) |
|--------|---------------|----------------------|----------------------|
| **Architecture** | Layered within contexts | Interface preparation | Hexagonal architecture |
| **Integration** | Direct method calls | Repository pattern | Event-driven |
| **Storage** | File-based (JSON/CSV) | Repository abstraction | Database + Event Store |
| **Visualization** | Matplotlib (PNG) | JSON data export | Web frontend (interactive) |
| **Contexts** | 3 bounded contexts | Interface boundaries | Multiple contexts (TBD) |
| **Deployment** | Desktop application | Containerization prep | Cloud-ready web app |

**Migration Strategy:**
- MVP decisions prioritize rapid development (5-week timeline)
- Transition preparations embedded in MVP (repository pattern, interfaces)
- Full version evolution planned but not blocking MVP delivery

---


