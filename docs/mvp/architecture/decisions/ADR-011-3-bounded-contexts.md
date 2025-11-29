# ADR-011: 3 Bounded Contexts

**Status:** Accepted - 2025-01-15

## Context

Full version will have multiple bounded contexts. MVP needs minimal viable domain decomposition.

## Decision

Use **3 bounded contexts**:
1. **Configuration Context**: Input validation & parsing
2. **Workshop Operations Context**: Simulation execution & analysis (workshops, tracks, trains)
3. **Analysis & Reporting Context**: Orchestration & output

## Rationale

- **Time constraint**: 5-week development with 3 developers
- **Clear ownership**: 1 context per developer
- **Essential separation**: Minimum viable domain boundaries
- **Extensible**: Can split into more contexts in full version

## Alternatives Considered

- **3 contexts** ✅ Chosen
- **1 monolith**: No domain separation
- **More specialized contexts**: Too complex for MVP timeline
- **2 contexts**: Insufficient separation

## Consequences

- **Positive**: Fast development, clear responsibilities
- **Negative**: Less granular than full version
- **Migration**: Context splitting planned for full version