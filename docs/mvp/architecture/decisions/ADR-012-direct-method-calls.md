# ADR-012: Direct Method Calls Between Contexts

**Status:** Accepted - 2025-01-15

## Context

Need integration strategy between bounded contexts. Full version will use event-driven architecture.

## Decision

Use **direct method calls** between contexts (synchronous).

## Rationale

- **Simplest approach**: No message bus, no events
- **Synchronous workflow**: Matches file-based processing
- **Easy debugging**: Clear call chain
- **Fast development**: Minimal infrastructure

## Alternatives Considered

- **Direct calls** ✅ Chosen
- **Event bus**: Too complex for MVP
- **Message queue**: Infrastructure overhead
- **REST API**: Unnecessary for single process

## Consequences

- **Positive**: Fast development, easy debugging
- **Negative**: Tight coupling (acceptable for MVP)
- **Migration**: Interface preparation for event-driven architecture