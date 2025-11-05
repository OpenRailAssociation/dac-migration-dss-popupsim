# 9. Architecture Decisions (MVP)

## 9.1 MVP Architecture Decisions Overview

### MVP ADR Status

| ADR | Title | Status | Impact |
|-----|-------|--------|--------|
| **MVP-001** | SimPy for Discrete Event Simulation | ✅ Accepted | Proven in 3-Länderhack POC |
| **MVP-002** | File-Based Data Storage | ✅ Accepted | No database installation required |
| **MVP-003** | Pydantic for Data Validation | ✅ Accepted | Type safety and validation |
| **MVP-004** | Matplotlib for Visualization | ✅ Accepted | Simple offline charts |
| **MVP-005** | Layered Architecture | ✅ Accepted | Rapid development |
| **MVP-006** | 3 Bounded Contexts | ✅ Accepted | Reduced complexity |
| **MVP-007** | Direct Method Calls | ✅ Accepted | Simple integration |

## 9.2 Technology Decisions

### ADR MVP-001: SimPy for Discrete Event Simulation

**Status:** Accepted - 2025-01-15

**Context:**
Need a discrete event simulation framework for modeling Pop-Up workshop operations with individual wagon tracking and resource management.

**Decision:**
Use **SimPy** as the simulation engine.

**Rationale:**
- **Proven in POC**: Successfully validated during 3-Länderhack 2024 hackathon
- **Python native**: Integrates seamlessly with Python ecosystem
- **Discrete event paradigm**: Perfect fit for workshop operations simulation
- **Deterministic**: Supports reproducible results with random seeds
- **Well-documented**: Mature library with good community support
- **Lightweight**: No heavy infrastructure requirements

**Alternatives Considered:**
- **SimPy** ✅ Chosen
- **Mesa**: Agent-based, overkill for our use case
- **Custom simulation**: Too much development effort
- **AnyLogic**: Commercial, not open source

**Consequences:**
- **Positive**: Fast development, proven approach, deterministic results
- **Negative**: Tight coupling to SimPy (mitigated by preparing abstraction layer)
- **Risk**: Framework limitations (acceptable for MVP scope)

---

### ADR MVP-002: File-Based Data Storage

**Status:** Accepted - 2025-01-15

**Context:**
Need data storage for configuration and results. Full version will use database, but MVP needs simplest approach.

**Decision:**
Use **file-based storage** with JSON/CSV formats.

**Rationale:**
- **Local deployment**: No server infrastructure needed
- **Small data volume**: Typical scenarios have <1000 wagons
- **Simple installation**: No database setup required
- **Transparency**: Human-readable formats
- **Version control**: Git-friendly text files
- **Portability**: Easy to share and backup

**Alternatives Considered:**
- **Files (JSON/CSV)** ✅ Chosen
- **SQLite**: Overkill for MVP data volume
- **PostgreSQL**: Requires installation and setup
- **In-memory only**: No persistence

**Consequences:**
- **Positive**: Zero installation complexity, transparent data
- **Negative**: Limited scalability (acceptable for MVP)
- **Migration**: Repository pattern prepared for database transition

---

### ADR MVP-003: Pydantic for Data Validation

**Status:** Accepted - 2025-01-15

**Context:**
Need robust input validation for JSON/CSV configuration files with clear error messages.

**Decision:**
Use **Pydantic** for data validation and parsing.

**Rationale:**
- **Type safety**: Excellent integration with Python type hints (matches project rules)
- **Validation**: Automatic validation with clear error messages
- **Performance**: Fast (Rust-based core in Pydantic v2)
- **JSON Schema**: Can generate schemas for documentation
- **IDE support**: Great autocomplete and type checking
- **Standard**: De facto standard in modern Python projects

**Alternatives Considered:**
- **Pydantic** ✅ Chosen
- **dataclasses**: No validation capabilities
- **attrs**: Less popular, fewer features
- **marshmallow**: Older, slower, less type-safe
- **cerberus**: Less Pythonic, no type hints

**Consequences:**
- **Positive**: Type-safe code, excellent validation, good error messages
- **Negative**: Additional dependency (minimal concern)
- **Benefit**: Enforces project's type hint requirements

---

### ADR MVP-004: Matplotlib for Visualization

**Status:** Accepted - 2025-01-15

**Context:**
Need visualization for simulation results. Full version will have web interface, but MVP needs simple charts.

**Decision:**
Use **Matplotlib** for generating static charts (PNG files).

**Rationale:**
- **Simple**: Easy to use, well-known library
- **Offline**: No web server required
- **Sufficient**: Meets MVP visualization needs
- **Python native**: Integrated in Python ecosystem
- **No frontend developer**: Backend team can handle it
- **Fast development**: Quick to implement basic charts

**Alternatives Considered:**
- **Matplotlib** ✅ Chosen
- **Plotly**: Interactive but requires web server
- **Bokeh**: Overkill for static charts
- **Seaborn**: Built on Matplotlib, no significant advantage
- **Custom web charts**: Requires frontend development

**Consequences:**
- **Positive**: Fast implementation, no web complexity
- **Negative**: Static charts only (acceptable for MVP)
- **Migration**: JSON data export prepared for web charts in full version

---

## 9.3 Architecture Decisions

### ADR MVP-005: Layered Architecture

**Status:** Accepted - 2025-01-15

**Context:**
Need simple architecture for rapid MVP development (5-week timeline) that can evolve to hexagonal architecture.

**Decision:**
Use **layered architecture** within each bounded context:
- Presentation Layer: CLI + File I/O
- Business Logic Layer: Domain services
- Data Access Layer: File operations
- Infrastructure Layer: SimPy, Matplotlib, Pydantic

**Rationale:**
- **Fast development**: Simple, well-understood pattern
- **Team experience**: Familiar to all developers
- **Clear separation**: Easy to test business logic
- **Migration ready**: Foundation for hexagonal architecture

**Alternatives Considered:**
- **Layered** ✅ Chosen
- **Hexagonal**: Too complex for 5-week MVP
- **Microservices**: Deployment overhead
- **Monolithic spaghetti**: Unmaintainable

**Consequences:**
- **Positive**: Rapid development, clear structure
- **Negative**: Less framework independence than hexagonal
- **Migration**: Interface preparation for hexagonal transition

---

### ADR MVP-006: 3 Bounded Contexts

**Status:** Accepted - 2025-01-15

**Context:**
Full version will have multiple bounded contexts. MVP needs minimal viable domain decomposition.

**Decision:**
Use **3 bounded contexts**:
1. **Configuration Context**: Input validation & parsing
2. **Simulation Domain Context**: Simulation execution & analysis (workshops, tracks, trains)
3. **Simulation Control Context**: Orchestration & output

**Rationale:**
- **Time constraint**: 5-week development with 3 developers
- **Clear ownership**: 1 context per developer
- **Essential separation**: Minimum viable domain boundaries
- **Extensible**: Can split into more contexts in full version

**Alternatives Considered:**
- **3 contexts** ✅ Chosen
- **1 monolith**: No domain separation
- **7+ contexts**: Too complex for MVP timeline
- **2 contexts**: Insufficient separation

**Consequences:**
- **Positive**: Fast development, clear responsibilities
- **Negative**: Less granular than full version
- **Migration**: Context splitting planned for full version

---

### ADR MVP-007: Direct Method Calls Between Contexts

**Status:** Accepted - 2025-01-15

**Context:**
Need integration strategy between bounded contexts. Full version will use event-driven architecture.

**Decision:**
Use **direct method calls** between contexts (synchronous).

**Rationale:**
- **Simplest approach**: No message bus, no events
- **Synchronous workflow**: Matches file-based processing
- **Easy debugging**: Clear call chain
- **Fast development**: Minimal infrastructure

**Alternatives Considered:**
- **Direct calls** ✅ Chosen
- **Event bus**: Too complex for MVP
- **Message queue**: Infrastructure overhead
- **REST API**: Unnecessary for single process

**Consequences:**
- **Positive**: Fast development, easy debugging
- **Negative**: Tight coupling (acceptable for MVP)
- **Migration**: Interface preparation for event-driven architecture

---

## 9.4 Rejected Alternatives

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

## 9.5 Migration Path

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


