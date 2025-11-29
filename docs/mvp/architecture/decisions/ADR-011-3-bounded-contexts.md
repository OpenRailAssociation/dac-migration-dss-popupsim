# ADR-011: 3 Bounded Contexts

**Status:** IMPLEMENTED - 2025-01-15

## Context

Full version will have multiple bounded contexts. MVP needs minimal viable domain decomposition.

## Decision

Use **3 bounded contexts**:
1. **Configuration Context**: Input validation & parsing
2. **Workshop Operations Context**: Simulation execution & analysis (workshops, tracks, trains)
3. **Analysis & Reporting Context**: Orchestration & output

## Rationale

- **Time constraint**: 5-week development with 3 developers
- **Clear ownership**: 1 context per developer
- **Essential separation**: Minimum viable domain boundaries
- **Extensible**: Can split into more contexts in full version

## Alternatives Considered

- **3 contexts** ✅ Chosen
- **1 monolith**: No domain separation
- **More specialized contexts**: Too complex for MVP timeline
- **2 contexts**: Insufficient separation

## Implementation in MVP

### Context Responsibilities
```python
# Configuration Context
class ScenarioService:
    def load_and_validate_scenario(self, source: Path) -> Scenario:
        # Handles all input validation and parsing
        
# Workshop Operations Context  
class WorkshopOrchestrator:
    def run(self, until: float) -> None:
        # Handles all simulation execution
        
# Analytics Context
class KPICalculator:
    def calculate_all_kpis(self, metrics: SimulationMetrics) -> AllKPIs:
        # Handles all metrics and reporting
```

### Context Integration
```python
# main.py - Context coordination
def main():
    # 1. Configuration Context
    scenario = scenario_service.load_and_validate_scenario(args.config)
    
    # 2. Workshop Operations Context
    orchestrator = WorkshopOrchestrator(sim, scenario)
    orchestrator.run()
    
    # 3. Analytics Context
    kpis = kpi_calculator.calculate_all_kpis(orchestrator.get_metrics())
```

## Consequences

### Achieved
- ✅ **Clear Responsibilities**: Each context owns distinct domain area
- ✅ **Independent Development**: 3 developers worked on separate contexts
- ✅ **Clean Interfaces**: Simple data transfer between contexts
- ✅ **Testable**: Each context tested independently
- ✅ **Extensible**: Foundation for full version context splitting

### Files Implementing This Decision
- `configuration/` - Complete input processing context
- `workshop_operations/` - Complete simulation execution context
- `analytics/` - Complete metrics and reporting context