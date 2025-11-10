# MVP Development Documentation

## Overview

This folder contains **developer-focused documentation** for implementing the PopUpSim MVP. These documents complement the main architecture documentation with implementation details, code examples, and development guidelines.

## Documentation Structure

### Core Documents
1. **[MVP Overview](01-mvp-overview.md)** - System overview, goals, constraints
2. **[Bounded Contexts](02-mvp-contexts.md)** - 3 MVP contexts and their responsibilities
3. **[Domain Model](03-mvp-domain-model.md)** - Domain entities, value objects, services
4. **[SimPy Integration](04-mvp-simpy-integration.md)** - Discrete event simulation integration
5. **[Data Flow](05-mvp-data-flow.md)** - Data flow through system
6. **[Technology Stack](06-mvp-technology-stack.md)** - Detailed technology decisions
7. **[File Formats](07-mvp-file-formats.md)** - JSON/CSV format specifications
8. **[Testing Strategy](08-mvp-testing-strategy.md)** - Testing approach and examples
9. **[Deployment](09-mvp-deployment.md)** - Deployment and installation
10. **[Migration Path](10-mvp-migration-path.md)** - Path from MVP to full version
11. **[Domain Processes](11-mvp-domain-processes.md)** - Process flows, state machines, business rules (TEMPLATE)

### Reference Documents
- **[Business Rules](business-rules.md)** - Consolidated business rules (FOR REVIEW)
- **[Configuration Validation](configuration-validation.md)** - Pydantic validation patterns
- **[Domain Models](domain-models.md)** - Detailed domain model reference
- **[Examples](examples.md)** - Synthetic workshop scenarios and test data

## Main Architecture Documentation

For complete architecture documentation, see:
- **[MVP Architecture](../architecture/README.md)** - arc42 architecture documentation (12 sections)
- **[Requirements](../../requirements/use-cases.md)** - User stories and requirements

## Key Differences

| Aspect | Architecture Docs | Development Docs |
|--------|-------------------|------------------|
| **Audience** | Stakeholders, architects | Developers, implementers |
| **Focus** | Decisions, structure, quality | Implementation, code, patterns |
| **Format** | arc42 template | Developer guides |
| **Code Examples** | Conceptual | Detailed with type hints |
| **Status** | Complete | Partially updated |

## Development Guidelines

### Code Standards
- **Python 3.13+** required
- **Type hints mandatory** on all functions/methods
- **Pydantic 2.0+** for data validation
- **Ruff** for formatting and linting
- **MyPy** for type checking
- **Pytest** for testing

### Project Rules
See `.amazonq/rules/project-rules.md` in the repository root for complete coding standards.

## Quick Start for Developers

1. **Read architecture first**: Start with [MVP Architecture Overview](../architecture/README.md)
2. **Understand contexts**: Review [Bounded Contexts](02-mvp-contexts.md)
3. **Study domain model**: Check [Domain Model](03-mvp-domain-model.md)
4. **Review actual code**: See `popupsim/backend/src/` for implementation
5. **Run tests**: Use `uv run pytest` to verify setup

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|-------------|
| Core Documents (1-10) | ✅ Complete | 2025 |
| Domain Processes (11) | 📋 Template | 2025 |
| Reference Documents | ✅ Complete | 2025 |
| Code Examples | ✅ Type hints added | 2025 |
| Cross-references | ✅ Added | 2025 |
| Translation | ✅ English | 2025 |

## Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Configuration Context | ✅ Implemented | `popupsim/backend/src/configuration/` |
| Workshop Operations Context | 🚧 In Progress | `popupsim/backend/src/domain/` |
| Analysis & Reporting Context | 📋 Planned | `popupsim/backend/src/control/` |
| SimPy Integration | 🚧 In Progress | `popupsim/backend/src/simulation/` |
| Testing | 🚧 In Progress | `popupsim/backend/tests/` |

## Contributing

When updating these development docs:
1. Keep consistent with main architecture
2. Include type hints in all code examples
3. Reference actual implementation files
4. Add cross-references to architecture sections
5. Use English language
6. Follow minimal code principle (no verbose examples)

## Questions?

- Architecture questions → See [Architecture Documentation](../architecture/README.md)
- Implementation questions → Check actual code in `popupsim/backend/src/`
- Requirements questions → See [Use Cases](../../requirements/use-cases.md)
