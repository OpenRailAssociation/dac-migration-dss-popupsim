# Retrofit Workflow Context Integration

## Overview
Integration plan for the new `RetrofitWorkflowContext` that supersedes the legacy three-context architecture (Yard, PopUp, Shunting) while maintaining backward compatibility and output format consistency.

## Architecture Decision: Option B - Dual Event Collection

**Strategy**: Keep both EventCollectors, wire Analytics Context to subscribe to retrofit events

### Benefits
- Retrofit context remains self-contained
- Analytics Context is single source of truth for aggregates
- No breaking changes to existing code
- Easy rollback if needed

### Components
```
┌─────────────────────────────────────────────────────────┐
│              Analytics Context (Aggregator)              │
│  - Subscribes to ALL events (legacy + retrofit)         │
│  - Computes summary metrics                             │
│  - Exports CSV/JSON in legacy format                    │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ Events via EventBus
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼────────┐              ┌──────────▼──────────┐
│ Legacy Workflow│              │ Retrofit Workflow   │
│ - Yard         │              │ - EventCollector    │
│ - PopUp        │              │   (internal use)    │
│ - Shunting     │              │ - Coordinators      │
└────────────────┘              └─────────────────────┘
```

---

## Implementation Steps

### Step 1: Add Workflow Mode Toggle to Scenario

**File**: `contexts/configuration/domain/models/scenario.py`

```python
from enum import Enum

class WorkflowMode(str, Enum):
    """Workflow implementation mode."""
    LEGACY = 'legacy'
    RETROFIT_WORKFLOW = 'retrofit_workflow'

class Scenario(BaseModel):
    # ... existing fields ...
    workflow_mode: WorkflowMode = WorkflowMode.LEGACY
```

**JSON Configuration Example**:
```json
{
  "id": "test_scenario",
  "workflow_mode": "retrofit_workflow",
  ...
}
```

---

### Step 2: Create Workflow Strategy Pattern

**File**: `application/workflow_strategy.py` (NEW)

```python
"""Workflow strategy pattern for legacy vs retrofit workflow."""

from typing import Protocol, Any
from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkflowContext
from contexts.yard_operations.application.yard_context import YardOperationsContext
from contexts.popup_retrofit.application.popup_context import PopUpRetrofitContext
from contexts.shunting_operations.application.shunting_context import ShuntingOperationsContext


class WorkflowStrategy(Protocol):
    """Protocol for workflow implementations."""
    
    def initialize(self, infra: Any, scenario: Any) -> None: ...
    def start_processes(self) -> None: ...
    def get_metrics(self) -> dict[str, Any]: ...
    def cleanup(self) -> None: ...


class LegacyWorkflowStrategy:
    """Legacy three-context workflow."""
    
    def __init__(self, infra: Any, event_bus: Any, rake_registry: Any):
        self.yard = YardOperationsContext(infra, rake_registry)
        self.popup = PopUpRetrofitContext(event_bus, rake_registry)
        self.shunting = ShuntingOperationsContext(event_bus, rake_registry)
        self.contexts = {'yard': self.yard, 'popup': self.popup, 'shunting': self.shunting}
    
    def initialize(self, infra: Any, scenario: Any) -> None:
        for ctx in self.contexts.values():
            ctx.initialize(infra, scenario)
    
    def start_processes(self) -> None:
        for ctx in self.contexts.values():
            ctx.start_processes()
    
    def get_metrics(self) -> dict[str, Any]:
        return {name: ctx.get_metrics() for name, ctx in self.contexts.items()}
    
    def cleanup(self) -> None:
        for ctx in self.contexts.values():
            ctx.cleanup()


class RetrofitWorkflowStrategy:
    """New unified retrofit workflow."""
    
    def __init__(self, env: Any, scenario: Any):
        self.retrofit_workflow = RetrofitWorkflowContext(env, scenario)
        self.contexts = {'retrofit_workflow': self.retrofit_workflow}
    
    def initialize(self, infra: Any, scenario: Any) -> None:
        self.retrofit_workflow.initialize()
    
    def start_processes(self) -> None:
        self.retrofit_workflow.start_processes()
    
    def get_metrics(self) -> dict[str, Any]:
        return {'retrofit_workflow': self.retrofit_workflow.get_metrics()}
    
    def cleanup(self) -> None:
        self.retrofit_workflow.cleanup()
```

---

### Step 3: Update Simulation Service

**File**: `application/simulation_service.py`

```python
from application.workflow_strategy import LegacyWorkflowStrategy, RetrofitWorkflowStrategy
from contexts.configuration.domain.models.scenario import WorkflowMode

class SimulationApplicationService:
    def __init__(self, scenario: Scenario) -> None:
        # ... existing initialization ...
        self.workflow_strategy: LegacyWorkflowStrategy | RetrofitWorkflowStrategy | None = None
    
    def _register_all_contexts(self) -> None:
        """Register all bounded contexts with the registry."""
        # Always register shared contexts
        self._register_shared_contexts()
        
        # Register workflow-specific contexts
        if self.scenario.workflow_mode == WorkflowMode.RETROFIT_WORKFLOW:
            self.workflow_strategy = RetrofitWorkflowStrategy(self.engine.env, self.scenario)
        else:
            self.workflow_strategy = LegacyWorkflowStrategy(
                self.infra, self.infra.event_bus, self._rake_registry
            )
        
        # Register workflow contexts in registry
        for name, ctx in self.workflow_strategy.contexts.items():
            self.context_registry.register_context(name, ctx)
            self.contexts[name] = ctx
    
    def _register_shared_contexts(self) -> None:
        """Register contexts used by both workflows."""
        # Configuration Context
        config_context = ConfigurationContext(self.infra.event_bus)
        config_context.finalize_scenario(self.scenario.id)
        self.context_registry.register_context('configuration', config_context)
        self.contexts['configuration'] = config_context
        
        # Railway Infrastructure Context
        railway_context = create_railway_context(self.scenario)
        self.context_registry.register_context('railway', railway_context)
        self.contexts['railway'] = railway_context
        
        # External Trains Context
        external_trains_context = ExternalTrainsContext(self.infra.event_bus)
        self.context_registry.register_context('external_trains', external_trains_context)
        self.contexts['external_trains'] = external_trains_context
        
        # Analytics Context
        analytics_repository = InMemoryAnalyticsRepository()
        analytics_context = AnalyticsContext(self.infra.event_bus, analytics_repository)
        self.context_registry.register_context('analytics', analytics_context)
        self.contexts['analytics'] = analytics_context
```

---

### Step 4: Wire Analytics Context to Retrofit Events

**File**: `contexts/analytics/application/analytics_context.py`

```python
class AnalyticsContext:
    def __init__(self, event_bus: EventBus, repository: AnalyticsRepository, ...):
        # ... existing initialization ...
        self._subscribe_to_retrofit_events()
    
    def _subscribe_to_retrofit_events(self) -> None:
        """Subscribe to retrofit workflow events."""
        try:
            from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
            from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
            from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
            
            self.event_bus.subscribe(WagonJourneyEvent, self._handle_retrofit_wagon_event)
            self.event_bus.subscribe(LocomotiveMovementEvent, self._handle_retrofit_loco_event)
            self.event_bus.subscribe(ResourceStateChangeEvent, self._handle_retrofit_resource_event)
        except ImportError:
            # Retrofit workflow not available, skip subscription
            pass
    
    def _handle_retrofit_wagon_event(self, event: Any) -> None:
        """Handle wagon journey events from retrofit workflow."""
        # Convert to analytics internal format and record
        self.event_stream.collector.record_event({
            'type': 'wagon_journey',
            'timestamp': event.timestamp,
            'wagon_id': event.wagon_id,
            'event_type': event.event_type,
            'location': event.location,
            'status': event.status,
        })
    
    def _handle_retrofit_loco_event(self, event: Any) -> None:
        """Handle locomotive movement events from retrofit workflow."""
        self.event_stream.collector.record_event({
            'type': 'locomotive_movement',
            'timestamp': event.timestamp,
            'locomotive_id': event.locomotive_id,
            'event_type': event.event_type,
        })
    
    def _handle_retrofit_resource_event(self, event: Any) -> None:
        """Handle resource state change events from retrofit workflow."""
        self.event_stream.collector.record_event({
            'type': 'resource_state',
            'timestamp': event.timestamp,
            'resource_type': event.resource_type,
            'resource_id': event.resource_id,
        })
```

---

### Step 5: Add Aggregate Export Methods to Analytics Context

**File**: `contexts/analytics/application/analytics_context.py`

```python
import pandas as pd
from pathlib import Path

class AnalyticsContext:
    def export_workshop_metrics_summary(self, output_path: Path) -> None:
        """Export workshop summary metrics (legacy format compatible)."""
        workshop_data = self._compute_workshop_aggregates()
        df = pd.DataFrame(workshop_data)
        df.to_csv(output_path / 'workshop_metrics.csv', index=False)
    
    def export_locomotive_utilization_summary(self, output_path: Path) -> None:
        """Export locomotive utilization summary (legacy format compatible)."""
        loco_data = self._compute_locomotive_aggregates()
        df = pd.DataFrame(loco_data)
        df.to_csv(output_path / 'locomotive_utilization.csv', index=False)
    
    def export_track_capacity_snapshot(self, output_path: Path) -> None:
        """Export final track capacity state (legacy format compatible)."""
        track_metrics = self.get_track_metrics()
        df = pd.DataFrame([
            {
                'track_id': track_id,
                'max_capacity_m': metrics['max_capacity'],
                'current_occupancy_m': metrics['current_occupancy'],
                'utilization_percent': metrics['utilization_percent'],
                'state': metrics['state'],
            }
            for track_id, metrics in track_metrics.items()
        ])
        df.to_csv(output_path / 'track_capacity.csv', index=False)
    
    def _compute_workshop_aggregates(self) -> list[dict[str, Any]]:
        """Compute workshop aggregates from event stream."""
        events = self.event_stream.collector.get_events()
        workshop_stats: dict[str, dict[str, float]] = {}
        
        for event in events:
            if event.get('type') == 'wagon_journey' and event.get('event_type') == 'RETROFIT_COMPLETED':
                workshop_id = event.get('location')
                if workshop_id not in workshop_stats:
                    workshop_stats[workshop_id] = {
                        'completed_retrofits': 0,
                        'total_retrofit_time': 0.0,
                        'total_waiting_time': 0.0,
                    }
                workshop_stats[workshop_id]['completed_retrofits'] += 1
        
        # Calculate throughput and utilization
        sim_duration = max((e.get('timestamp', 0) for e in events), default=0)
        
        return [
            {
                'workshop_id': ws_id,
                'completed_retrofits': stats['completed_retrofits'],
                'total_retrofit_time': stats['total_retrofit_time'],
                'total_waiting_time': stats['total_waiting_time'],
                'throughput_per_hour': (stats['completed_retrofits'] / sim_duration * 60) if sim_duration > 0 else 0,
                'utilization_percent': (stats['total_retrofit_time'] / sim_duration * 100) if sim_duration > 0 else 0,
            }
            for ws_id, stats in workshop_stats.items()
        ]
    
    def _compute_locomotive_aggregates(self) -> list[dict[str, Any]]:
        """Compute locomotive aggregates from event stream."""
        events = self.event_stream.collector.get_events()
        loco_stats: dict[str, dict[str, float]] = {}
        
        for event in events:
            if event.get('type') == 'locomotive_movement':
                loco_id = event.get('locomotive_id')
                if loco_id not in loco_stats:
                    loco_stats[loco_id] = {
                        'parking_time': 0.0,
                        'moving_time': 0.0,
                        'coupling_time': 0.0,
                        'decoupling_time': 0.0,
                    }
        
        # Calculate percentages
        return [
            {
                'locomotive_id': loco_id,
                'parking_time': stats['parking_time'],
                'moving_time': stats['moving_time'],
                'coupling_time': stats['coupling_time'],
                'decoupling_time': stats['decoupling_time'],
                'parking_percent': (stats['parking_time'] / sum(stats.values()) * 100) if sum(stats.values()) > 0 else 0,
                'moving_percent': (stats['moving_time'] / sum(stats.values()) * 100) if sum(stats.values()) > 0 else 0,
                'coupling_percent': (stats['coupling_time'] / sum(stats.values()) * 100) if sum(stats.values()) > 0 else 0,
                'decoupling_percent': (stats['decoupling_time'] / sum(stats.values()) * 100) if sum(stats.values()) > 0 else 0,
            }
            for loco_id, stats in loco_stats.items()
        ]
```

---

### Step 6: Update Main CLI for Conditional Output

**File**: `main.py`

```python
from contexts.configuration.domain.models.scenario import WorkflowMode

@app.command()
def run(scenario_path: Path, output_path: Path = Path('./output'), verbose: bool = False) -> None:
    """Run PopUpSim with new bounded contexts architecture."""
    # ... existing setup ...
    
    scenario = ConfigurationBuilder(scenario_path).build()
    service = SimulationApplicationService(scenario)
    result = service.execute(until)
    
    if result.success:
        analytics = service.context_registry.contexts.get('analytics')
        
        # Export analytics aggregates (works for both workflows)
        analytics.export_workshop_metrics_summary(output_path)
        analytics.export_locomotive_utilization_summary(output_path)
        analytics.export_track_capacity_snapshot(output_path)
        
        # Export workflow-specific data
        if scenario.workflow_mode == WorkflowMode.RETROFIT_WORKFLOW:
            retrofit_ctx = service.contexts.get('retrofit_workflow')
            if retrofit_ctx:
                retrofit_ctx.export_events(str(output_path))
        
        # Generate visualizations (works for both)
        output_visualization(service.contexts, output_path)
        
        # Print metrics (conditional based on workflow)
        print_metrics(service.contexts, scenario.workflow_mode)

def print_metrics(contexts: dict, workflow_mode: WorkflowMode) -> None:
    """Print metrics based on workflow mode."""
    if workflow_mode == WorkflowMode.RETROFIT_WORKFLOW:
        print_retrofit_workflow_metrics(contexts)
    else:
        print_legacy_workflow_metrics(contexts)
```

---

## Output Format Compatibility

### Required CSV Files (Both Workflows)

1. **wagon_journey.csv**
   - Columns: `timestamp, wagon_id, train_id, event, location, status`
   - Source: Analytics Context (aggregated from events)

2. **workshop_metrics.csv**
   - Columns: `workshop_id, completed_retrofits, total_retrofit_time, total_waiting_time, throughput_per_hour, utilization_percent`
   - Source: Analytics Context (computed from wagon events)

3. **locomotive_utilization.csv**
   - Columns: `locomotive_id, parking_time, moving_time, coupling_time, decoupling_time, parking_percent, moving_percent, coupling_percent, decoupling_percent`
   - Source: Analytics Context (computed from loco events)

4. **track_capacity.csv**
   - Columns: `track_id, max_capacity_m, current_occupancy_m, utilization_percent, state`
   - Source: Analytics Context (final snapshot)

5. **rejected_wagons.csv**
   - Columns: `wagon_id, train_id, rejection_time, rejection_type, detailed_reason, collection_track_id`
   - Source: Analytics Context (filtered wagon events)

---

## Testing Strategy

### Phase 1: Unit Tests
- Test workflow strategy pattern
- Test Analytics event handlers
- Test aggregate computation methods

### Phase 2: Integration Tests
- Run same scenario with both workflows
- Compare output CSV files
- Verify metrics match

### Phase 3: Validation
- Run existing test scenarios with `workflow_mode: legacy`
- Run same scenarios with `workflow_mode: retrofit_workflow`
- Compare results

---

## Migration Path

### Stage 1: Parallel Operation (Current)
- Both workflows available
- Toggle via scenario configuration
- Default: `legacy`

### Stage 2: Validation Period
- Run production scenarios with both modes
- Validate output consistency
- Fix discrepancies

### Stage 3: Deprecation
- Default: `retrofit_workflow`
- Legacy mode marked deprecated
- Documentation updated

### Stage 4: Removal
- Remove legacy contexts
- Remove workflow strategy pattern
- Simplify codebase

---

## Configuration Examples

### Legacy Mode
```json
{
  "id": "legacy_scenario",
  "workflow_mode": "legacy",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-02T00:00:00Z",
  ...
}
```

### Retrofit Workflow Mode
```json
{
  "id": "retrofit_scenario",
  "workflow_mode": "retrofit_workflow",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-02T00:00:00Z",
  "parking_strategy": "smart_accumulation",
  "parking_normal_threshold": 0.3,
  "parking_critical_threshold": 0.8,
  ...
}
```

---

## Implementation Checklist

- [ ] Step 1: Add `WorkflowMode` enum to Scenario model
- [ ] Step 2: Create `workflow_strategy.py` with strategy pattern
- [ ] Step 3: Update `simulation_service.py` to use strategy
- [ ] Step 4: Wire Analytics Context to retrofit events
- [ ] Step 5: Add aggregate export methods to Analytics
- [ ] Step 6: Update `main.py` for conditional output
- [ ] Test: Run legacy mode with existing scenarios
- [ ] Test: Run retrofit mode with same scenarios
- [ ] Test: Compare outputs for consistency
- [ ] Documentation: Update user guide
- [ ] Documentation: Update architecture docs

---

## Benefits

1. **Backward Compatibility**: Existing scenarios work unchanged
2. **Gradual Migration**: Toggle per scenario, not system-wide
3. **Single Source of Truth**: Analytics Context aggregates all metrics
4. **Easy Rollback**: Switch back to legacy if issues found
5. **Clean Architecture**: Strategy pattern isolates workflow logic
6. **Testability**: Both workflows can be tested independently

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Output format mismatch | Comprehensive integration tests comparing CSV outputs |
| Event subscription overhead | Analytics Context already subscribes to many events |
| Duplicate event collection | Retrofit EventCollector is internal, Analytics is export layer |
| Performance degradation | Profile both workflows, optimize bottlenecks |
| Breaking changes | Default to legacy mode, explicit opt-in to new workflow |

---

## Next Steps

1. Implement Step 1-3 (core strategy pattern)
2. Run integration tests with legacy mode
3. Implement Step 4-5 (Analytics wiring)
4. Run integration tests with retrofit mode
5. Compare outputs and fix discrepancies
6. Update Step 6 (CLI) for production use
