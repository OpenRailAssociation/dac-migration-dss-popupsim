# ADR-013: Hexagonal Architecture for Data Sources

**Status:** Accepted - 2025-01-16

## Context

Need to support multiple input formats (JSON, CSV) and prepare for future API integration while maintaining clean separation between domain logic and data access.

## Decision

Implement **hexagonal architecture** specifically for the Configuration Context with data source adapters.

## Rationale

- **Multi-format support**: CSV import requirement from stakeholders
- **Future API readiness**: Planned integration with external systems
- **Testability**: Easy to mock data sources for testing
- **Maintainability**: Clear separation between data access and business logic
- **Extensibility**: New data sources without changing core logic
- **Type safety**: Consistent DTOs across all adapters

## Implementation

- **DataSourcePort**: Interface defining adapter contract
- **JsonDataSourceAdapter**: Wraps existing JSON functionality
- **CsvDataSourceAdapter**: New CSV directory support
- **DataSourceFactory**: Auto-detects source type
- **ScenarioLoader**: Orchestrates using adapters

## Alternatives Considered

- **Hexagonal Architecture** ✅ Chosen
- **Direct CSV parsing**: Tight coupling, hard to test
- **Single JSON format**: Doesn't meet CSV requirement
- **Full hexagonal everywhere**: Too complex for MVP timeline

## Consequences

- **Positive**: Multi-format support, future-ready, testable, maintainable
- **Negative**: Additional complexity (justified by requirements)
- **Benefit**: Foundation for full hexagonal architecture migration

## CSV Directory Structure

```
csv_scenario/
├── scenario.csv      # Basic metadata (ID, dates, seed)
├── trains.csv        # Train schedule with arrival times
├── wagons.csv        # Wagon data linked to trains
├── workshops.csv     # Workshop configuration
├── tracks.csv        # Track definitions
├── routes.csv        # Route definitions
└── locomotives.csv   # Locomotive fleet data
```