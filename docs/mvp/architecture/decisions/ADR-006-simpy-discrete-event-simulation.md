# ADR-006: SimPy for Discrete Event Simulation

**Status:** Accepted - 2025-01-15

## Context

Need a discrete event simulation framework for modeling Pop-Up workshop operations with individual wagon tracking and resource management.

## Decision

Use **SimPy** as the simulation engine.

## Rationale

- **Proven in POC**: Successfully validated during 3-Länderhack 2024 hackathon
- **Python native**: Integrates seamlessly with Python ecosystem
- **Discrete event paradigm**: Perfect fit for workshop operations simulation
- **Deterministic**: Supports reproducible results
- **Well-documented**: Mature library with good community support
- **Lightweight**: No heavy infrastructure requirements

## Alternatives Considered

- **SimPy** ✅ Chosen
- **Mesa**: Agent-based, overkill for our use case
- **Custom simulation**: Too much development effort
- **AnyLogic**: Commercial, not open source

## Consequences

- **Positive**: Fast development, proven approach, deterministic results
- **Negative**: Tight coupling to SimPy (mitigated by preparing abstraction layer)
- **Risk**: Framework limitations (acceptable for MVP scope)