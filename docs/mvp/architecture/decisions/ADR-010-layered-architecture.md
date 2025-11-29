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

- **Layered** ✅ Chosen
- **Hexagonal**: Too complex for 5-week MVP
- **Microservices**: Deployment overhead
- **Monolithic spaghetti**: Unmaintainable

## Implementation in MVP

### Layer Structure per Context
```
configuration/
├── application/     # Services, DTOs (Presentation)
├── domain/         # Models, business logic
└── infrastructure/ # File I/O, adapters (Data Access)

workshop_operations/
├── application/     # Orchestrator, coordinators
├── domain/         # Entities, services, business rules
└── infrastructure/ # SimPy, resources, routing

analytics/
├── application/     # KPI services, aggregators
├── domain/         # Collectors, models
└── infrastructure/ # Matplotlib, CSV export
```

### Dependency Direction
```
Presentation → Business Logic → Data Access
Application  → Domain         → Infrastructure
```

## Consequences

### Achieved
- ✅ **Rapid Development**: 5-week MVP timeline met
- ✅ **Clear Structure**: Consistent layering across all contexts
- ✅ **Testable Business Logic**: Domain layer isolated from infrastructure
- ✅ **Migration Ready**: Clean interfaces prepared for hexagonal transition
- ✅ **Team Productivity**: Familiar pattern, easy to understand

### Files Implementing This Decision
- All contexts follow consistent layered structure
- Domain layers contain pure business logic
- Infrastructure layers handle external dependencies