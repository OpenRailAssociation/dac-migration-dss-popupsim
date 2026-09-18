# PopUpSim Documentation

This directory contains all documentation for PopUpSim, organized by topic.

## Documentation Structure

```
docs/
├── tutorial/              # Step-by-step configuration tutorial
├── mvp/                  # MVP implementation documentation
├── requirements/         # Requirements and use cases
├── adr/                  # Architecture Decision Records
├── ci-cd.md             # CI/CD pipeline documentation
├── DOCS_DEPLOYMENT.md   # Documentation deployment guide
└── DOCS_SETUP.md        # Documentation setup instructions
```

## Quick Navigation

### Getting Started
- **[Tutorial](tutorial/README.md)** - Step-by-step configuration guide
- **[Installation Guide](tutorial/00-installation.md)** - Installing Python, uv, and PopUpSim

### MVP Documentation
- **[MVP Architecture](mvp/architecture/README.md)** - Complete arc42 architecture for the MVP
- **[MVP Development Guide](mvp/development/README.md)** - Implementation details and examples

### Requirements & Use Cases
- **[Use Cases](requirements/use-cases.md)** - User stories and requirements
- **[Concept Document](requirements/250321_KonzeptPopUpSim_Entwurf.md)** - Original concept

### Architecture Decisions
- **[ADR Overview](adr/README.md)** - Performance optimizations and architectural decisions

## Architecture Overview

PopUpSim uses a 4 bounded-context architecture (Domain-Driven Design):

| Context | Purpose | Technology |
|---------|---------|------------|
| **Configuration** | Input loading & validation | Pydantic |
| **External Trains** | Train arrivals & wagon creation | Event publishing |
| **Railway Infrastructure** | Track capacity & occupancy | Domain aggregates |
| **Retrofit Workflow** | Simulation execution & reporting | SimPy, domain services |

See [MVP Architecture Building Blocks](mvp/architecture/05-building-blocks.md) for the detailed context breakdown.

## Getting Started

1. **For MVP Development**: Start with [MVP Architecture](mvp/architecture/README.md)
2. **For Requirements**: Review [Use Cases](requirements/use-cases.md)
3. **For Architecture Decisions**: Browse the [Architecture Decisions overview](mvp/architecture/09-architecture-decisions.md)

## Contributing to Documentation

- Follow [arc42 template](https://arc42.org/) for architecture documentation
- Keep documentation current with code changes
- Update cross-references when moving or renaming files

## Documentation Maintenance

- **Tutorial**: Updated when configuration format changes
- **MVP Documentation**: Updated during development
- **Cross-References**: Maintained manually
- **Navigation**: Keep README files current with structure changes