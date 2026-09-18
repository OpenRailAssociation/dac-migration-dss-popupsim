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

- **Direct calls** — Chosen
- **Event bus**: Too complex for MVP
- **Message queue**: Infrastructure overhead
- **REST API**: Unnecessary for single process

## Implementation in MVP

### Direct Integration Pattern
```python
# main.py - Synchronous context orchestration (simplified)
def run(scenario_path: Path, output_path: Path):
    # Configuration Context - load & validate scenario
    scenario = ConfigurationBuilder(scenario_path).build()

    # Retrofit Workflow + Railway Infrastructure + External Trains
    # are wired and driven by the application service
    service = SimulationApplicationService(scenario, output_path)
    until = timedelta_to_sim_ticks(scenario.end_date - scenario.start_date)
    result = service.execute(until)

    # Export results (CSV/JSON) for the dashboard to consume
    output_visualization(result, output_path)
```

> **Note:** The `WorkshopOrchestrator`/`kpi_calculator`/`analytics` names from the original
> proposal do not exist. Orchestration is handled by
> `application/simulation_service.py` (`SimulationApplicationService`), which registers the
> four contexts and drives the SimPy engine.

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
- **Fast Development**: No message bus or event infrastructure needed
- **Easy Debugging**: Clear call stack, simple error tracing
- **Synchronous Flow**: Matches file-based processing workflow
- **Interface Ready**: Abstract interfaces prepared for future migration
- **Simple Testing**: Direct method calls easy to test

### Files Implementing This Decision
- `main.py` - Direct context coordination
- Context interfaces prepared for future event-driven architecture