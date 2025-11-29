# ADR-012: Direct Method Calls Between Contexts

**Status:** IMPLEMENTED - 2025-01-15

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

## Implementation in MVP

### Direct Integration Pattern
```python
# main.py - Synchronous context calls
def main():
    # Direct method call to Configuration Context
    scenario = scenario_service.load_and_validate_scenario(config_path)
    
    # Direct instantiation with Workshop Operations Context
    orchestrator = WorkshopOrchestrator(sim, scenario)
    orchestrator.run()
    
    # Direct method call to Analytics Context
    metrics = orchestrator.get_metrics()
    kpis = kpi_calculator.calculate_all_kpis(metrics)
    
    # Direct call to export results
    exporter.export_results(kpis, output_path)
```

### Interface Preparation
```python
# Interfaces prepared for future event-driven migration
class ScenarioServiceInterface(ABC):
    @abstractmethod
    def load_and_validate_scenario(self, source: Path) -> Scenario: ...

class KPICalculatorInterface(ABC):
    @abstractmethod
    def calculate_all_kpis(self, metrics: SimulationMetrics) -> AllKPIs: ...
```

## Consequences

### Achieved
- ✅ **Fast Development**: No message bus or event infrastructure needed
- ✅ **Easy Debugging**: Clear call stack, simple error tracing
- ✅ **Synchronous Flow**: Matches file-based processing workflow
- ✅ **Interface Ready**: Abstract interfaces prepared for future migration
- ✅ **Simple Testing**: Direct method calls easy to test

### Files Implementing This Decision
- `main.py` - Direct context coordination
- Context interfaces prepared for future event-driven architecture