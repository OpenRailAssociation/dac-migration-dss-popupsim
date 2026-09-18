# ADR-004: 3-Bounded Context Architecture

## Status
**SUPERSEDED** - Originally accepted January 2025; superseded by the current 4-bounded-context design.

> [!IMPORTANT]
> This ADR describes the original 3-context split (Configuration, Workshop Operations,
> Analysis & Reporting) with `workshop_operations/` and `analytics/` packages. **The code
> no longer implements this design.** The system now has **4 bounded contexts** and the
> reporting/analytics concern was folded into the Retrofit Workflow context.
>
> Current contexts (see [`../05-building-blocks.md`](../05-building-blocks.md)):
> 1. **Configuration** (`contexts/configuration/`)
> 2. **External Trains** (`contexts/external_trains/`)
> 3. **Railway Infrastructure** (`contexts/railway_infrastructure/`)
> 4. **Retrofit Workflow** (`contexts/retrofit_workflow/`) — includes simulation execution and reporting/export
>
> The content below is retained for historical context only. Package paths such as
> `workshop_operations/` and `analytics/` do not exist in the current codebase.

## Context

PopUpSim required clear architectural boundaries to manage complexity of freight rail simulation with multiple concerns: configuration management, simulation execution, and analytics reporting.

### Domain Complexity
- **Configuration**: Complex scenario loading, validation, and parsing
- **Simulation**: Discrete event simulation with 5 process coordinators
- **Analytics**: KPI calculation, metrics collection, and reporting
- **Cross-Cutting**: Validation, resource management, event handling

### Requirements
- Clear separation of concerns
- Independent development and testing
- Scalable architecture for future growth
- Clean interfaces between contexts
- Domain-driven design principles

## Decision

Implement **3-Bounded Context Architecture** based on Domain-Driven Design principles:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Configuration  │───▶│ Workshop Ops     │───▶│   Analytics     │
│    Context      │    │    Context       │    │   Context       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Context Definitions

#### 1. Configuration Context
- **Responsibility**: Input validation, parsing, scenario building
- **Core Concepts**: Scenario, ValidationPipeline, ScenarioService
- **Architecture**: Hexagonal with 4-layer validation
- **Technology**: Pydantic, JSON/CSV adapters

#### 2. Workshop Operations Context  
- **Responsibility**: Discrete event simulation execution
- **Core Concepts**: WorkshopOrchestrator, 5 Process Coordinators, Resource Management
- **Architecture**: Layered with domain services
- **Technology**: SimPy, resource pools, capacity managers

#### 3. Analytics Context
- **Responsibility**: Metrics collection, KPI calculation, reporting
- **Core Concepts**: KPICalculator, MetricCollectors, Visualizer
- **Architecture**: Event-driven with observers
- **Technology**: Matplotlib, CSV export, statistical analysis

## Alternatives Considered

### Alternative 1: Monolithic Architecture
- **Pros**: Simple, single deployment unit
- **Cons**: Poor separation of concerns, difficult to test, scalability issues
- **Rejected**: Not suitable for complex domain with multiple concerns

### Alternative 2: Microservices Architecture
- **Pros**: Independent deployment, technology diversity
- **Cons**: Over-engineered for MVP, network complexity, operational overhead
- **Rejected**: Premature optimization for current requirements

### Alternative 3: 2-Context Architecture (Config + Simulation)
- **Pros**: Simpler than 3-context, clear separation
- **Cons**: Analytics mixed with simulation, unclear reporting boundaries
- **Rejected**: Analytics deserves separate context due to complexity

### Alternative 4: 4+ Context Architecture
- **Pros**: Very fine-grained separation
- **Cons**: Over-engineered, too many boundaries, coordination complexity
- **Rejected**: Unnecessary complexity for current domain size

## Implementation

### Context Boundaries

#### Configuration Context (`configuration/`)
```
├── application/     # Services, DTOs, pipelines
├── domain/         # Models, factories, ports
└── infrastructure/ # Adapters, file I/O
```

#### Workshop Operations Context (`workshop_operations/`)
```
├── application/     # Orchestrator, coordinators
├── domain/         # Entities, services, value objects
└── infrastructure/ # Resources, simulation, routing
```

#### Analytics Context (`analytics/`)
```
├── application/     # Services, aggregators
├── domain/         # Collectors, models, observers
└── infrastructure/ # Exporters, visualization
```

### Shared Infrastructure (`shared/`)
```
├── validation/     # 4-layer validation framework
└── i18n/          # Internationalization
```

### Context Interactions

#### Data Flow
```
Configuration → Validation → Workshop Simulation → Analytics → Export
```

#### Interface Contracts
- **Configuration → Workshop**: Validated Scenario domain object
- **Workshop → Analytics**: Simulation metrics and events
- **Analytics → External**: CSV files, PNG charts

### Context Independence
- Each context can be developed independently
- Clear interface contracts between contexts
- Separate test suites for each context
- Independent technology choices within contexts

## Consequences

### Positive
- **Clear Boundaries**: Each context has well-defined responsibilities
- **Independent Development**: Teams can work on contexts independently
- **Testability**: Each context can be tested in isolation
- **Scalability**: Contexts can evolve independently
- **Technology Flexibility**: Different tech stacks per context
- **Domain Alignment**: Architecture reflects business domains

### Negative
- **Coordination Overhead**: Need to manage interfaces between contexts
- **Initial Complexity**: More complex than monolithic approach
- **Integration Testing**: Need to test context interactions

### Context Characteristics

#### Configuration Context
- Hexagonal architecture with a 4-layer validation framework
- DTO → domain transformation
- Pluggable data source adapters

#### Workshop Operations Context
- Domain model with aggregates
- Multiple process coordinators
- Resource management abstraction
- SimPy integration

#### Analytics Context
- Event-driven design
- Observer pattern for metrics
- Specification pattern for bottleneck detection
- Multiple export formats

## Validation

### Architecture Characteristics
- **Maintainability**: Clear separation, consistent patterns
- **Testability**: Contexts can be tested independently
- **Extensibility**: Features can be added within a context
- **Performance**: Adequate for the MVP; optimization opportunities remain

### Context Cohesion
- **Configuration**: High cohesion around scenario management
- **Workshop Operations**: High cohesion around simulation execution  
- **Analytics**: High cohesion around metrics and reporting

### Context Coupling
- **Low Coupling**: Clean interfaces, minimal dependencies
- **Data Coupling**: Only essential data passed between contexts
- **No Temporal Coupling**: Contexts don't depend on execution timing

## Compliance

This decision supports:
- **Domain-Driven Design**: Clear bounded contexts aligned with business domains
- **Clean Architecture**: Proper dependency direction and separation
- **SOLID Principles**: Single responsibility, open/closed, dependency inversion

## References

- [Building Blocks Documentation](../05-building-blocks.md)
- [Solution Strategy](../04-solution-strategy.md)

---

**Decision Date**: January 2025  
**Decision Makers**: Architecture Team  
**Implementation Status**: Complete