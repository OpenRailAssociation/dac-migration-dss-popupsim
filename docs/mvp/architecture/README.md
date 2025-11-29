# PopUpSim MVP - arc42 Architecture Documentation

## Overview

This documentation describes the **MVP (Minimum Viable Product) architecture** of PopUpSim.

**MVP Scope:** Desktop application with file-based configuration, SimPy simulation engine, and Matplotlib visualization.

## Architecture Documentation

1. **[Introduction and Goals](01-introduction-goals.md)** - Stakeholders, quality goals, requirements overview
2. **[Constraints](02-constraints.md)** - Technical and organizational constraints
3. **[Context and Scope](03-context.md)** - System boundaries and external interfaces
4. **[Solution Strategy](04-solution-strategy.md)** - Technology decisions and architecture approach
5. **[Building Blocks](05-building-blocks.md)** - System decomposition (3 bounded contexts, Level 2 & 3)
   - **[5a. Level 3 Implementation Details](05a-level3-implementation.md)** - Complete implementation architecture
6. **[Runtime View](06-runtime.md)** - Key scenarios and use case flows
7. **[Deployment View](07-deployment.md)** - Infrastructure and deployment
8. **[Cross-Cutting Concepts](08-concepts.md)** - Domain model, error handling, logging
9. **[Architecture Decisions](09-architecture-decisions.md)** - ADRs for key technology choices
10. **[Quality Requirements](10-quality-requirements.md)** - Quality scenarios and metrics
11. **[Risks and Technical Debt](11-risks-technical-debt.md)** - Known risks and debt
12. **[Glossary](12-glossary.md)** - Domain and technical terms
13. **[Bibliography](13-bibliography.md)** - References and resources

## Key Architecture Characteristics

- **3 Bounded Contexts:** Configuration, Workshop Operations, Analysis & Reporting
- **Hexagonal Architecture:** Data source adapters for JSON, CSV, and future API integration
- **Technology Stack:** Python 3.13+, SimPy, Pydantic, Matplotlib
- **Deployment:** Desktop application (local execution)
- **Data Storage:** File-based (JSON/CSV) with adapter pattern for extensibility
- **Integration:** Direct method calls (synchronous)

## Quick Links

- **[Quality Goals](01-introduction-goals.md#12-quality-goals)** - Top 5 quality priorities
- **[Use Cases](01-introduction-goals.md#14-mvp-scope)** - 4 MVP use cases
- **[Technology Decisions](09-architecture-decisions.md)** - 7 key ADRs
- **[Building Blocks](05-building-blocks.md)** - System structure (3 contexts)
- **[Glossary](12-glossary.md)** - 95+ terms
