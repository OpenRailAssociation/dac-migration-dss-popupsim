# PopUpSim Documentation

This directory contains all documentation for PopUpSim, organized by version and topic.

## Documentation Structure

```
docs/
├── mvp/                    # MVP implementation documentation
├── full-version/           # Full version architecture and design
├── requirements/           # Requirements and use cases
├── ci-cd.md               # CI/CD pipeline documentation
├── DOCS_DEPLOYMENT.md     # Documentation deployment guide
└── DOCS_SETUP.md          # Documentation setup instructions
```

## Quick Navigation

### MVP Documentation
- **[MVP Architecture](mvp/architecture/README.md)** - Complete arc42 architecture for the MVP
- **[MVP Development Guide](mvp/development/README.md)** - Implementation details and examples

### Requirements & Use Cases
- **[Use Cases](requirements/use-cases.md)** - User stories and requirements
- **[Concept Document](requirements/250321_KonzeptPopUpSim_Entwurf.md)** - Original concept

## Version Comparison

| Aspect | MVP | Full Version |
|--------|-----|--------------|
| **Architecture** | Layered within 3 contexts | Hexagonal with 8+ contexts |
| **Integration** | Direct method calls | Event-driven architecture |
| **Interface** | CLI + Files | Web application |
| **Data Storage** | JSON/CSV files | Database + Event Store |
| **Workflows** | Hard-coded processes | External workflow definitions |
| **Resources** | Simple pools | Configurable state machines |

## Architecture Decision Records (ADRs)

### MVP ADRs (1-5)
Located in `mvp/architecture/decisions/`:
- ADR-001: Hexagonal Pipeline Architecture
- ADR-002: 4-Layer Validation Framework  
- ADR-003: Field Name Standardization
- ADR-004: 3 Bounded Context Architecture
- ADR-005: Type Hints Mandatory

### Full Version ADRs (1-18)
Located in `full-version/architecture/decisions/`:
- **ADR-001 to ADR-003**: Core infrastructure decisions
- **ADR-006 to ADR-018**: Bounded context definitions

## Getting Started

1. **For MVP Development**: Start with [MVP Architecture](mvp/architecture/README.md)
2. **For Requirements**: Review [Use Cases](requirements/use-cases.md)
3. **For Architecture Decisions**: Browse [MVP ADRs](mvp/architecture/decisions/)

## Contributing to Documentation

- Follow [arc42 template](https://arc42.org/) for architecture documentation
- Use [ADR format](https://adr.github.io/) for architectural decisions
- Keep MVP and Full Version documentation clearly separated
- Update cross-references when moving or renaming files

## Documentation Maintenance

- **MVP Documentation**: Updated during MVP development
- **Full Version Documentation**: Updated during architecture planning
- **Cross-References**: Maintained automatically where possible
- **Navigation**: Keep README files current with structure changes