# ADR-010: Layered Architecture

**Status:** Accepted - 2025-01-15

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

## Consequences

- **Positive**: Rapid development, clear structure
- **Negative**: Less framework independence than hexagonal
- **Migration**: Interface preparation for hexagonal transition