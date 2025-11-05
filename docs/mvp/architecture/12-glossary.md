# 12. Glossary (MVP)

## 12.1 MVP Domain Terms

### Railway Operations (MVP)

| Term | MVP Definition | Example |
|---------|----------------|----------|
| **DAC** | Digital Automatic Coupler - New coupling technology | Replaces screw coupling |
| **Pop-Up Workshop** | Temporary retrofit workshop for DAC migration | Multiple retrofit stations on workshop track, 3 weeks operation |
| **Retrofit** | Conversion from screw coupling to DAC | ~30 minutes per wagon |
| **Parking Track** | Track where wagons are parked | Capacity: Total length - 25m |
| **Workshop Track** | Track where wagons are retrofitted (`werkstattgleis`) | Capacity: Number of retrofit stations + one locomotive |
| **Feeder Track** | Track feeding wagons into workshop (`werkstattzufuehrung`) | Capacity: Varies by layout |
| **Exit Track** | Track for retrofitted wagons leaving workshop (`werkstattabfuehrung`) | Capacity: Varies by layout |
| **Collection Track** | Track for intermediate wagon storage (`sammelgleis`) | Capacity: Varies (synthetic examples: 20-50 wagons) |
| **Parking Track** | Track for temporary wagon storage (`parkgleis`) | Capacity: Varies by layout |
| **Station Head Track** | Station head tracks (`bahnhofskopf`) | Capacity: Varies by layout |
| **Retrofit Station** | Workplace for DAC retrofit | 1-2 workers per station |
| **Wagon** | Freight wagon (railway vehicle) | Various types, different retrofit times |
| **Wagon Group** | Multiple coupled freight wagons | Wagon group of 3 wagons |
| **Train** | Composition of multiple wagons | 10-30 or more wagons per train |

### Simulation (MVP)

| Term | MVP Definition | Usage |
|------|----------------|-------|
| **Discrete Event Simulation** | Event-driven simulation with SimPy | Time jumps between events |
| **SimPy** | Python framework for discrete event simulation | Core of MVP simulation |
| **Event** | Simulation event (arrival, start, end) | `TrainArrival`, `RetrofitComplete` |
| **Process** | SimPy process for business logic | `retrofit_process()` |
| **Environment** | SimPy simulation environment | Time control and event queue |
| **Determinism** | Reproducible simulation results | Same inputs → same results |

## 12.2 MVP Architecture Terms

### Layered Architecture (MVP)

| Term | MVP Definition | Layer |
|---------|----------------|-------|
| **Presentation Layer** | CLI and file output | Top layer |
| **Business Logic Layer** | Domain services and business logic | Core layer |
| **Data Access Layer** | File I/O (JSON/CSV) | Data layer |
| **Infrastructure Layer** | SimPy, Matplotlib, file system | Bottom layer |
| **Service** | Business logic component | `ConfigurationService`, `SimulationDomainService` |
| **Model** | Data model/entity | `Workshop`, `Station`, `Wagon` |

### Bounded Context (MVP)

| Term | MVP Definition | Responsibility |
|---------|----------------|---------------|
| **Configuration Context** | JSON/CSV import and validation | Scenario setup |
| **Simulation Domain Context** | DAC retrofit and SimPy integration | Core business logic |
| **Simulation Control Context** | Orchestration and output generation | Overall control |
| **Context** | Domain section with clear boundaries | Bounded context per DDD |
| **Domain Model** | Domain data model of a context | Entities, value objects |

### Architecture Patterns (MVP)

| Term | MVP Definition | Usage |
|------|----------------|-------|
| **Repository Pattern** | Abstraction layer for data access | Planned for database migration |
| **Adapter Pattern** | Interface between incompatible interfaces | SimPy adapter for simulation engine |
| **Port** | Interface defining external dependency | Part of hexagonal architecture (future) |
| **Dependency Injection** | Passing dependencies to components | Prepared for hexagonal migration |
| **Service Layer** | Business logic orchestration | Current MVP architecture |

## 12.3 MVP Technical Terms

### Python/SimPy (MVP)

| Term | MVP Definition | Usage |
|---------|----------------|------------|
| **Pydantic** | Python library for data validation | Configuration models |
| **Matplotlib** | Python library for charts | Chart generation |
| **Pandas** | Python library for data processing | CSV processing (optional) |
| **Type Hints** | Python typing | Code documentation and IDE support |
| **Dataclass** | Python decorator for data classes | Domain models |
| **Virtual Environment** | Isolated Python environment | Dependency management |

### Development Tools (MVP)

| Term | MVP Definition | Purpose |
|------|----------------|----------|
| **uv** | Fast Python package manager | Dependency management and virtual environments |
| **Ruff** | Fast Python linter and formatter | Code formatting and linting |
| **MyPy** | Static type checker for Python | Type checking with `disallow_untyped_defs = true` |
| **Pylint** | Python code analysis tool | Static code analysis |
| **pytest** | Python testing framework | Unit and integration testing |
| **pytest-cov** | Coverage plugin for pytest | Test coverage measurement |

### File Formats (MVP)

| Term | MVP Definition | Structure |
|---------|----------------|----------|
| **JSON** | JavaScript Object Notation | Configuration files |
| **CSV** | Comma-Separated Values | Tabular data |
| **PNG** | Portable Network Graphics | Matplotlib charts |
| **uv.lock** | Python uv lockfile | Dependency lockfile |

## 12.4 MVP Quality Terms

### Performance (MVP)

| Term | MVP Definition | Target Value |
|---------|----------------|----------|
| **Throughput** | Processed wagons per hour | To be measured |
| **Latency** | Time until simulation start | To be measured |
| **Memory usage** | Application memory consumption | To be measured |
| **Execution time** | Total simulation duration | To be measured |
| **Scalability** | Maximum scenario size | To be measured |

### Testing (MVP)

| Term | MVP Definition | Tool |
|---------|----------------|------|
| **Unit Test** | Test of individual functions/classes | pytest |
| **Integration Test** | Test of component interaction | pytest |
| **End-to-End Test** | Test of complete simulation runs | Manual |
| **Test Coverage** | Percentage of tested code lines | pytest-cov |
| **Mock** | Simulated dependency for tests | unittest.mock |

## 12.5 MVP Process Terms

### Development (MVP)

| Term | MVP Definition | Duration |
|---------|----------------|-------|
| **MVP** | Minimum Viable Product | 5 weeks |
| **Sprint** | Development iteration | 1 week |
| **Milestone** | Important development step | End of each week |
| **Code Review** | Peer review of code changes | Continuous |
| **Refactoring** | Code improvement without functional change | As needed |

### Migration (MVP)

| Term | MVP Definition | Effort |
|---------|----------------|---------|
| **Technical Debt** | Deliberate simplifications for speed | Documented |
| **Migration Path** | Path from MVP to full version | Planned |
| **Interface Preparation** | Preparation for architecture migration | During MVP |
| **Hexagonal Architecture** | Target architecture of full version | Post-MVP |
| **Event-driven Architecture** | Target integration of full version | Post-MVP |

## 12.6 MVP KPI Terms

### Simulation KPIs (MVP)

| Term | MVP Definition | Calculation |
|---------|----------------|------------|
| **Throughput** | Retrofitted wagons per time unit | `wagons_processed / simulation_hours` |
| **Utilization** | Percentage usage of stations | `busy_time / total_time * 100` |
| **Waiting Time** | Average waiting time of wagons | `sum(waiting_times) / wagon_count` |
| **Queue Length** | Number of waiting wagons | `wagons_in_queue` |
| **Bottleneck** | Resource with highest utilization | Station with `max(utilization)` |

### Output KPIs (MVP)

| Term | MVP Definition | Format |
|---------|----------------|--------|
| **CSV Export** | Structured KPI data | `simulation_results.csv` |
| **Chart** | Visualized KPI data | `kpi_charts.png` |
| **Log** | Event timeline | `simulation_log.json` |
| **Summary** | Results summary | Console output |

## 12.7 MVP Error Terms

### Error Handling (MVP)

| Term | MVP Definition | Handling |
|---------|----------------|------------|
| **Configuration Error** | Error loading configuration | Immediate exit with error message |
| **Validation Error** | Invalid input data | List of all validation errors |
| **Simulation Error** | Runtime error during simulation | Graceful degradation |
| **Output Error** | Error during result generation | Continue without failed output |
| **Graceful Degradation** | Partial functionality on errors | Partial results |

## 12.8 MVP Abbreviations

### Technical Abbreviations

| Abbreviation | Full Form | Context |
|-----------|----------|---------|
| **MVP** | Minimum Viable Product | Development phase |
| **DDD** | Domain-Driven Design | Architecture approach |
| **CLI** | Command Line Interface | User interface |
| **I/O** | Input/Output | File operations |
| **API** | Application Programming Interface | Interface |
| **JSON** | JavaScript Object Notation | Data format |
| **CSV** | Comma-Separated Values | Data format |
| **PNG** | Portable Network Graphics | Image format |

### Domain Abbreviations

| Abbreviation | Full Form | Context |
|-----------|----------|---------|
| **DAC** | Digital Automatic Coupler | Railway technology |
| **KPI** | Key Performance Indicator | Performance metric |
| **SLA** | Service Level Agreement | Quality target |
| **ROI** | Return on Investment | Economic efficiency |

---


