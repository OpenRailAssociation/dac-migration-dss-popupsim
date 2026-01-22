# ADR-004: 3-Bounded Context Architecture

## Status
**ACCEPTED** - Implemented January 2025

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

### Context Quality Assessment

#### Configuration Context: 9.5/10
- Excellent hexagonal architecture
- 4-layer validation framework
- Clean DTO → Domain transformation
- Pluggable data source adapters

#### Workshop Operations Context: 9.0/10
- Rich domain model with aggregates
- 5 specialized process coordinators
- Resource management abstraction
- Clean SimPy integration

#### Analytics Context: 9.0/10
- Event-driven architecture
- Observer pattern for metrics
- Specification pattern for bottlenecks
- Multiple export formats

## Validation

### Architecture Metrics
- **Maintainability**: 9.5/10 - Clear separation, consistent patterns
- **Testability**: 9.0/10 - Independent context testing
- **Extensibility**: 9.5/10 - Easy to add features within contexts
- **Performance**: 8.5/10 - Good for MVP, optimization opportunities

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
**Implementation Status**: ✅ Complete