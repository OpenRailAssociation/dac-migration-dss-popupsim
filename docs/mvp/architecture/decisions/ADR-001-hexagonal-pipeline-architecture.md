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
- **Extensibility**: ★★☆☆☆☆ (2/6) - Domain services hard to extend for new sources
- **Testability**: ★★★☆☆☆ (3/6) - Domain logic testable, but infrastructure coupling
- **Validation**: ★★★★☆☆ (4/6) - Rich domain validation, but scattered across aggregates
- **Error Handling**: ★★★☆☆☆ (3/6) - Domain exceptions, but inconsistent error formats
- **Consistency**: ★★★☆☆☆ (3/6) - Domain consistency, but infrastructure varies
- **Async Support**: ★★☆☆☆☆ (2/6) - Domain events possible, but complex setup

#### 2. Enhanced ScenarioBuilder Pattern
- **Extensibility**: ★★☆☆☆☆ (2/6) - Builder methods for new sources, but monolithic
- **Testability**: ★★☆☆☆☆ (2/6) - Builder testable, but complex mocking required
- **Validation**: ★★★☆☆☆ (3/6) - Centralized in builder, but tightly coupled
- **Error Handling**: ★★☆☆☆☆ (2/6) - Builder exceptions, but limited error context
- **Consistency**: ★★★★☆☆ (4/6) - Single builder ensures consistency
- **Async Support**: ★☆☆☆☆☆ (1/6) - Builder pattern not async-friendly

#### 3. Pure Hexagonal Architecture
- **Extensibility**: ★★★☆☆☆ (3/6) - Easy to add adapters, but inconsistent validation
- **Testability**: ★★★☆☆☆ (3/6) - Adapters testable, but validation scattered
- **Validation**: ★★☆☆☆☆ (2/6) - Each adapter handles own validation differently
- **Error Handling**: ★★☆☆☆☆ (2/6) - Inconsistent error formats across adapters
- **Consistency**: ★★☆☆☆☆ (2/6) - Different processing flows per adapter
- **Async Support**: ★★★☆☆☆ (3/6) - Possible but requires adapter-level implementation

#### 4. Pure Pipeline Architecture
- **Extensibility**: ★★★★☆☆ (4/6) - Easy to add stages, harder to add sources
- **Testability**: ★★★★☆☆ (4/6) - Each stage independently testable
- **Validation**: ★★★★★☆ (5/6) - Consistent validation across all sources
- **Error Handling**: ★★★★★☆ (5/6) - Structured error collection and reporting
- **Consistency**: ★★★★★★ (6/6) - Uniform processing flow
- **Async Support**: ★★★★☆☆ (4/6) - Pipeline stages can be async

#### 5. Mixed Approach (Hexagonal + Pipeline)
- **Extensibility**: ★★★★★★ (6/6) - Easy to add both adapters and processing stages
- **Testability**: ★★★★★★ (6/6) - Both adapters and pipeline stages testable
- **Validation**: ★★★★★★ (6/6) - Consistent validation through pipeline
- **Error Handling**: ★★★★★★ (6/6) - Structured error collection with adapter flexibility
- **Consistency**: ★★★★★★ (6/6) - Uniform processing with adapter modularity
- **Async Support**: ★★★★★★ (6/6) - Both pipeline and adapters can be async

## Decision
We chose the **Mixed Approach (Hexagonal + Pipeline)** over all alternatives including the original ScenarioBuilder pattern for the following reasons:

### Comparison Summary
- **Original ScenarioBuilder**: 14/36 points - Monolithic, hard to extend
- **Pure DDD**: 17/36 points - Good domain logic, poor infrastructure flexibility
- **Enhanced ScenarioBuilder**: 14/36 points - Still monolithic despite improvements
- **Pure Hexagonal**: 17/36 points - Good modularity, poor consistency
- **Pure Pipeline**: 28/36 points - Good consistency, limited extensibility
- **Mixed Approach**: 36/36 points - Best of all patterns

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

This architecture provides the best balance of modularity, consistency, and extensibility for PopUpSim's evolving requirements.