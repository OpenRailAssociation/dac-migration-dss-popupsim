# ADR-010: Layered Architecture

**Status:** IMPLEMENTED - 2025-01-15

## Context

Need simple architecture for rapid MVP development (5-week timeline) that can evolve to hexagonal architecture.

## Decision

Use **layered architecture** within each bounded context:
- Presentation Layer: CLI + File I/O
- Business Logic Layer: Domain services
- Data Access Layer: File operations
- Infrastructure Layer: SimPy, Matplotlib, Pydantic

## Rationale

- **Fast development**: Simple, well-understood pattern
- **Team experience**: Familiar to all developers
- **Clear separation**: Easy to test business logic
- **Migration ready**: Foundation for hexagonal architecture

## Alternatives Considered

- **Layered** — Chosen
- **Hexagonal**: Too complex for 5-week MVP
- **Microservices**: Deployment overhead
- **Monolithic spaghetti**: Unmaintainable

## Implementation in MVP

### Layer Structure per Context
```
contexts/configuration/
├── application/     # DTOs, application services (Presentation)
├── domain/         # Models, business logic
└── infrastructure/ # File I/O, adapters (Data Access)

contexts/external_trains/
├── application/     # ExternalTrainsContext, ports
├── domain/         # Train schedule, entities, events
└── infrastructure/ # Adapters

contexts/railway_infrastructure/
├── application/     # RailwayInfrastructureContext, event handlers
├── domain/         # Track aggregates, services, repositories
└── infrastructure/ # DI container, adapters

contexts/retrofit_workflow/
├── application/     # Coordinators, application services, event export
├── domain/         # Entities, domain services, business rules
└── infrastructure/ # SimPy resources, CSV exporters, routing
```

> **Note:** The reporting/analytics concern lives inside `contexts/retrofit_workflow`
> (event collection + CSV/JSON export). There is no separate `analytics/` package. The
> web dashboard (`popupsim/frontend/`) consumes these exported files.

### Dependency Direction
```
Presentation → Business Logic → Data Access
Application  → Domain         → Infrastructure
```

## Consequences

### Achieved
- **Rapid Development**: 5-week MVP timeline met
- **Clear Structure**: Consistent layering across all contexts
- **Testable Business Logic**: Domain layer isolated from infrastructure
- **Migration Ready**: Clean interfaces prepared for hexagonal transition
- **Team Productivity**: Familiar pattern, easy to understand

### Files Implementing This Decision
- All contexts follow consistent layered structure
- Domain layers contain pure business logic
- Infrastructure layers handle external dependencies