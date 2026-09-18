# ADR-001: Hexagonal + Pipeline Architecture for Scenario Loading

## Status
Accepted

## Context
The PopUpSim configuration system needed to support multiple data sources (JSON files, CSV directories, future REST APIs) with consistent validation and error handling. We analyzed six architectural approaches:

### Original Implementation (ScenarioBuilder Pattern)
- **Lines of Code**: 600+ across multiple components
- **Complexity**: High - monolithic builder with complex validation logic
- **Extensibility**: Low - adding new sources required modifying existing code
- **Testability**: Poor - tightly coupled validation and loading logic
- **Maintainability**: Low - duplicated validation across contexts
- **Pattern**: Builder pattern with complex forward references and DTO handling

### Evaluated Alternatives

#### 1. Pure Domain-Driven Design (DDD)
- **Extensibility**: Domain services are hard to extend for new sources.
- **Testability**: Domain logic is testable, but coupled to infrastructure.
- **Validation**: Validation lives in the domain but is scattered across aggregates.
- **Error Handling**: Domain exceptions, but inconsistent error formats.
- **Consistency**: Domain is consistent, but infrastructure handling varies.

#### 2. Enhanced ScenarioBuilder Pattern
- **Extensibility**: New sources are added via builder methods, but the builder stays monolithic.
- **Testability**: The builder is testable, but requires complex mocking.
- **Validation**: Centralized in the builder, but tightly coupled to it.
- **Error Handling**: Builder exceptions carry limited error context.
- **Consistency**: A single builder keeps processing consistent.

#### 3. Pure Hexagonal Architecture
- **Extensibility**: Easy to add adapters, but validation is inconsistent between them.
- **Testability**: Adapters are testable, but validation is scattered.
- **Validation**: Each adapter validates differently.
- **Error Handling**: Error formats differ across adapters.
- **Consistency**: Processing flows differ per adapter.

#### 4. Pure Pipeline Architecture
- **Extensibility**: Easy to add stages; harder to add new data sources.
- **Testability**: Each stage is independently testable.
- **Validation**: Consistent validation across all sources.
- **Error Handling**: Structured error collection and reporting.
- **Consistency**: Uniform processing flow.

#### 5. Mixed Approach (Hexagonal + Pipeline)
- **Extensibility**: New data sources (adapters) and new processing stages can both be added.
- **Testability**: Both adapters and pipeline stages are independently testable.
- **Validation**: Consistent validation runs through the pipeline.
- **Error Handling**: Structured error collection, with adapters handling source-specific parsing.
- **Consistency**: Uniform processing with modular adapters.

## Decision
We chose the **Mixed Approach (Hexagonal + Pipeline)** over the alternatives, including the original ScenarioBuilder pattern.

### Rationale Summary
- **Original / Enhanced ScenarioBuilder**: Monolithic and hard to extend for new sources.
- **Pure DDD**: Strong domain logic, but limited infrastructure flexibility.
- **Pure Hexagonal**: Good modularity, but inconsistent validation across adapters.
- **Pure Pipeline**: Consistent processing, but harder to add new data sources.
- **Mixed Approach (chosen)**: Combines adapter modularity with a consistent validation pipeline.

### Technical Benefits
1. **Modularity**: Hexagonal ports/adapters for data source flexibility
2. **Consistency**: Pipeline ensures uniform validation and processing
3. **Extensibility**: Easy to add new data sources and processing stages
4. **Testability**: Both adapters and pipeline stages independently testable
5. **Error Handling**: Structured validation results with detailed feedback

### Implementation Results
- **Lines of Code**: 140 total (vs 600+ original)
- **Components**: 4 clean components vs 8+ complex ones
- **Validation**: Centralized in pipeline vs duplicated across contexts
- **Data Sources**: JSON, CSV supported; REST API ready
- **Test Coverage**: Each component independently testable

### Code Quality Improvements
```
Original Implementation:
- ScenarioBuilder: 400+ lines
- CsvDataSourceAdapter: 300+ lines  
- ScenarioValidator: 200+ lines
- Duplicated validation logic

New Implementation:
- ScenarioPipeline: 40 lines
- CsvScenarioAdapter: 45 lines
- JsonScenarioAdapter: 25 lines
- ScenarioService: 30 lines
```

## Consequences

### Positive
- **Reduced Complexity**: 76% reduction in code lines
- **Better Separation**: Clear boundaries between concerns
- **Consistent Validation**: Single pipeline for all sources
- **Future-Proof**: Ready for REST API, database sources
- **Maintainable**: Each component has single responsibility

### Negative
- **Learning Curve**: Developers need to understand both patterns
- **Initial Setup**: More files than monolithic approach
- **Abstraction**: Additional layer between service and data loading

### Migration Impact
- All existing JSON scenarios work unchanged
- CSV scenarios use new simplified format
- Tests updated to use new architecture
- Main.py updated to handle validation results

## Implementation
- **Pipeline**: 3-stage validation (source → loading → domain)
- **Adapters**: JSON and CSV with consistent interface
- **Service**: Hexagonal service using pipeline for processing
- **Validation**: Structured results with error aggregation

This architecture balances modularity (adapters), consistency (pipeline), and extensibility for PopUpSim's evolving data-source requirements.