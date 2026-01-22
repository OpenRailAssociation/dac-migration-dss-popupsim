# Retrofit Workflow Integration - Minimal Path

## Key Discovery from Tests

The `RetrofitWorkshopContext` works **standalone** and has a different initialization pattern than legacy contexts:

### Retrofit Context Pattern (from test_retrofit_workflow_scenarios.py)
```python
env = simpy.Environment()
context = RetrofitWorkshopContext(env, scenario)
context.initialize()  # NO parameters!
context.start_processes()  # Spawns SimPy processes

# Wagons injected via TrainArrivedEvent subscription
context.subscribe_to_train_arrivals(event_bus)
```

### Legacy Context Pattern (current simulation_service.py)
```python
context = YardOperationsContext(infra, rake_registry)
context_registry.register_context('yard', context)
context_registry.initialize_all(infra, scenario)  # Calls initialize(infra, scenario)
context_registry.start_all_processes()
```

## The Problem

`RetrofitWorkshopContext.initialize()` takes **NO parameters**, but the context registry calls `initialize(infrastructure, scenario)`.

## Minimal Solution

Add a **conditional branch** in `simulation_service.py` that:
1. Detects retrofit workflow mode
2. Bypasses context registry for retrofit context
3. Uses direct initialization like the tests do
4. Still uses context registry for shared contexts (External Trains, Analytics)

## Implementation

```python
def _initialize_contexts(self) -> None:
    """Initialize contexts based on workflow mode."""
    
    # Check if retrofit workflow mode
    use_retrofit = hasattr(self.scenario, 'workflow_mode') and self.scenario.workflow_mode == 'retrofit_workflow'
    
    if use_retrofit:
        self._initialize_retrofit_workflow()
    else:
        self._initialize_legacy_workflow()

def _initialize_retrofit_workflow(self) -> None:
    """Initialize retrofit workflow (bypass context registry)."""
    from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
    
    # Create retrofit context directly
    retrofit_context = RetrofitWorkshopContext(self.engine.env, self.scenario)
    retrofit_context.initialize()  # NO parameters!
    self.contexts['retrofit_workflow'] = retrofit_context
    
    # Subscribe to train arrivals
    retrofit_context.subscribe_to_train_arrivals(self.infra.event_bus)
    
    # Register shared contexts (External Trains, Analytics) via registry
    self._register_shared_contexts()
    self.context_registry.initialize_all(self.infra, self.scenario)

def _initialize_legacy_workflow(self) -> None:
    """Initialize legacy workflow (use context registry)."""
    self._register_all_contexts()  # Current implementation
    self.infra.contexts = self.contexts
    self.infra.shunting_context = self.contexts.get('shunting')
    self.context_registry.initialize_all(self.infra, self.scenario)
    self._setup_workshop_infrastructure()
```

## Benefits

1. **Respects original design** - Each context uses its intended initialization pattern
2. **Minimal changes** - Only touches simulation_service.py
3. **No breaking changes** - Legacy workflow unchanged
4. **Clean separation** - Retrofit and legacy paths are independent
5. **Works like tests** - Uses exact same pattern as working tests

## Next Steps

1. Add `workflow_mode` field to Scenario model
2. Implement conditional initialization in simulation_service.py
3. Update `_start_processes()` to handle retrofit context separately
4. Test with both modes

## Files to Modify

1. `contexts/configuration/domain/models/scenario.py` - Add workflow_mode field
2. `application/simulation_service.py` - Add conditional initialization
3. `Data/examples/ten_trains_two_days/scenario.json` - Add workflow_mode field for testing
