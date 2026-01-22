# Complete Integration Picture - Retrofit Workflow

## Context Categories

### 1. Shared Contexts (Used by BOTH workflows)
- **Configuration Context** - Static config, no SimPy processes
- **Railway Infrastructure Context** - Static topology
- **External Trains Context** - Publishes TrainArrivedEvent
- **Analytics Context** - Collects metrics

### 2. Legacy Workflow Contexts (ONLY for legacy mode)
- **Yard Operations Context**
- **PopUp Retrofit Context**
- **Shunting Operations Context**

### 3. Retrofit Workflow Context (ONLY for retrofit mode)
- **RetrofitWorkshopContext** - Replaces all 3 legacy contexts

## Current Implementation Pattern

```python
# simulation_service.py - _register_all_contexts()

# Configuration Context - Special handling (no SimPy processes)
config_context = ConfigurationContext(self.infra.event_bus)
config_context.finalize_scenario(self.scenario.id)  # Called BEFORE registry
self.context_registry.register_context('configuration', config_context)
self.contexts['configuration'] = config_context

# Railway Context - Static, no processes
railway_context = create_railway_context(self.scenario)
self.context_registry.register_context('railway', railway_context)
self.contexts['railway'] = railway_context

# External Trains - Has processes, uses registry
external_trains_context = ExternalTrainsContext(self.infra.event_bus)
self.context_registry.register_context('external_trains', external_trains_context)
self.contexts['external_trains'] = external_trains_context

# Legacy workflow contexts - Use registry
yard_context = YardOperationsContext(self.infra, self._rake_registry)
self.context_registry.register_context('yard', yard_context)
# ... etc
```

## Key Insight: Configuration Context Pattern

Configuration Context is **NOT** registered with context registry for initialization:
1. Created directly
2. `finalize_scenario()` called BEFORE registry
3. Registered only for lifecycle events (started/ended)
4. No `initialize(infra, scenario)` call

## Proposed Pattern for Retrofit Context

Use the **same pattern** as Configuration Context:

```python
def _initialize_contexts(self) -> None:
    """Initialize contexts based on workflow mode."""
    
    # Always register shared contexts
    self._register_shared_contexts()
    
    # Conditional workflow registration
    if self._use_retrofit_workflow():
        self._register_retrofit_workflow()
    else:
        self._register_legacy_workflow()
    
    # Initialize registered contexts
    self.infra.contexts = self.contexts
    self.infra.shunting_context = self.contexts.get('shunting')
    self.context_registry.initialize_all(self.infra, self.scenario)
    
    # Post-initialization setup
    if not self._use_retrofit_workflow():
        self._setup_workshop_infrastructure()

def _use_retrofit_workflow(self) -> bool:
    """Check if retrofit workflow mode is enabled."""
    return (hasattr(self.scenario, 'workflow_mode') and 
            self.scenario.workflow_mode == 'retrofit_workflow')

def _register_shared_contexts(self) -> None:
    """Register contexts used by both workflows."""
    
    # Configuration Context - NO registry initialization
    config_context = ConfigurationContext(self.infra.event_bus)
    config_context.finalize_scenario(self.scenario.id)
    self.context_registry.register_context('configuration', config_context)
    self.contexts['configuration'] = config_context
    
    # Railway Context - NO registry initialization
    railway_context = create_railway_context(self.scenario)
    self.context_registry.register_context('railway', railway_context)
    self.contexts['railway'] = railway_context
    
    # External Trains - Uses registry initialization
    external_trains_context = ExternalTrainsContext(self.infra.event_bus)
    self.context_registry.register_context('external_trains', external_trains_context)
    self.contexts['external_trains'] = external_trains_context
    
    # Analytics Context - Uses registry initialization
    analytics_repository = InMemoryAnalyticsRepository()
    analytics_context = AnalyticsContext(self.infra.event_bus, analytics_repository)
    self.context_registry.register_context('analytics', analytics_context)
    self.contexts['analytics'] = analytics_context

def _register_retrofit_workflow(self) -> None:
    """Register retrofit workflow context - NO registry initialization."""
    from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
    
    # Create and initialize directly (like Configuration Context)
    retrofit_context = RetrofitWorkshopContext(self.engine.env, self.scenario)
    retrofit_context.initialize()  # Called BEFORE registry
    
    # Wire to train arrivals
    retrofit_context.subscribe_to_train_arrivals(self.infra.event_bus)
    
    # Register for lifecycle events only (like Configuration Context)
    self.context_registry.register_context('retrofit_workflow', retrofit_context)
    self.contexts['retrofit_workflow'] = retrofit_context

def _register_legacy_workflow(self) -> None:
    """Register legacy workflow contexts - Uses registry initialization."""
    
    # Shunting Context
    shunting_context = ShuntingOperationsContext(self.infra.event_bus, self._rake_registry)
    self.context_registry.register_context('shunting', shunting_context)
    self.contexts['shunting'] = shunting_context
    
    # Yard Context
    yard_context = YardOperationsContext(self.infra, self._rake_registry)
    self.context_registry.register_context('yard', yard_context)
    self.contexts['yard'] = yard_context
    
    # PopUp Context
    popup_context = PopUpRetrofitContext(self.infra.event_bus, self._rake_registry)
    self.context_registry.register_context('popup', popup_context)
    self.contexts['popup'] = popup_context
```

## Context Registry Behavior

The registry's `initialize_all()` will:
- **Skip** Configuration Context (already initialized)
- **Skip** Railway Context (already initialized)
- **Skip** Retrofit Context (already initialized)
- **Initialize** External Trains Context
- **Initialize** Analytics Context
- **Initialize** Legacy contexts (if registered)

## Start Processes

```python
def _start_processes(self) -> None:
    """Start all context processes."""
    
    # Start registered contexts via registry
    self.context_registry.start_all_processes()
    
    # Start retrofit workflow if present (like Configuration Context pattern)
    if 'retrofit_workflow' in self.contexts:
        self.contexts['retrofit_workflow'].start_processes()
    
    # Start orchestration
    self.engine.schedule_process(self._orchestrate_simulation())
```

## Summary: Two Initialization Patterns

### Pattern A: Registry-Managed (External Trains, Analytics, Legacy Contexts)
1. Create context
2. Register with registry
3. Registry calls `initialize(infra, scenario)`
4. Registry calls `start_processes()`

### Pattern B: Self-Managed (Configuration, Railway, Retrofit)
1. Create context
2. Call `initialize()` or `finalize_scenario()` directly
3. Register with registry (for lifecycle events only)
4. Call `start_processes()` manually if needed

## Why This Works

- **Configuration Context**: No SimPy processes, just static config
- **Railway Context**: No SimPy processes, just topology
- **Retrofit Context**: Has SimPy processes, but uses different initialization signature

All three bypass registry initialization but still participate in lifecycle events (started/ended/failed).

## Files to Modify

1. `contexts/configuration/domain/models/scenario.py` - Add `workflow_mode` field
2. `application/simulation_service.py` - Refactor initialization methods
3. `contexts/retrofit_workflow/application/retrofit_workflow_context.py` - Add train arrival handler

## Minimal Changes

Only 3 methods in `simulation_service.py`:
- `_initialize_contexts()` - Add workflow mode check
- `_register_shared_contexts()` - Extract shared context registration
- `_register_retrofit_workflow()` - New method (10 lines)
- `_register_legacy_workflow()` - Rename from `_register_all_contexts()`
- `_start_processes()` - Add manual start for retrofit context

Total: ~50 lines of code changes.
