# ADR-012: Shunting Operations Context

## Status
Proposed

## Context
Shunting operations within railway yards involve complex microscopic movements including coupling/decoupling, push/pull operations, conflict resolution, and safety protocols. Current architecture mixes shunting with general yard management, but shunting complexity justifies dedicated domain modeling with specialized algorithms and safety-critical operations.

### Shunting Complexity
- **Microscopic Movements** - Track-by-track locomotive and wagon movements
- **Coupling Operations** - Complex coupling/decoupling sequences with safety protocols
- **Conflict Resolution** - Multiple locomotives sharing tracks, switches, and resources
- **Safety Protocols** - Speed limits, signal compliance, collision avoidance
- **Optimization Algorithms** - Minimize movements, efficient wagon sorting, locomotive utilization
- **Resource Coordination** - Shunting locomotives, track occupancy, switch operations

### Current Problems
- **Mixed Concerns** - Shunting operations mixed with general yard management
- **Algorithm Complexity** - Sophisticated pathfinding and optimization buried in yard context
- **Safety Critical** - Safety protocols not properly modeled as first-class domain concepts
- **Resource Conflicts** - No dedicated conflict resolution for simultaneous shunting operations
- **Reusability** - Shunting algorithms locked to specific yard implementation

## Decision
Create **Shunting Operations Context** as dedicated bounded context for microscopic locomotive movements within yards with specialized safety and optimization algorithms.

### Architecture
```
shunting_operations/
├── domain/
│   ├── aggregates/
│   │   ├── shunting_mission.py      # Complete shunting operation
│   │   └── shunting_plan.py         # Optimized sequence of movements
│   ├── entities/
│   │   ├── shunting_locomotive.py   # Specialized yard locomotive
│   │   ├── wagon_consist.py         # Group of coupled wagons
│   │   ├── shunting_movement.py     # Individual push/pull operation
│   │   ├── coupling_operation.py    # Coupling/decoupling with safety
│   │   └── track_occupation.py      # Real-time track occupancy
│   ├── services/
│   │   ├── movement_planner.py      # Optimize shunting sequences
│   │   ├── conflict_resolver.py     # Resolve resource conflicts
│   │   ├── safety_controller.py     # Speed limits, collision avoidance
│   │   ├── coupling_coordinator.py  # Manage coupling operations
│   │   ├── pathfinder.py           # Find optimal paths through yard
│   │   └── locomotive_dispatcher.py # Assign locomotives to missions
│   └── value_objects/
│       ├── movement_sequence.py     # Ordered list of movements
│       ├── safety_constraints.py    # Speed, distance, signal limits
│       ├── coupling_specification.py # Coupling requirements and protocols
│       └── conflict_resolution.py   # Resource conflict solutions
├── application/
│   ├── shunting_orchestrator.py     # Coordinate multiple shunting missions
│   ├── mission_scheduler.py         # Schedule and prioritize missions
│   └── services/
│       ├── shunting_planning_service.py # Plan optimal shunting operations
│       ├── safety_monitoring_service.py # Monitor safety compliance
│       ├── resource_allocation_service.py # Allocate locomotives and tracks
│       └── performance_optimization_service.py # Optimize shunting efficiency
└── infrastructure/
    ├── pathfinding/
    │   ├── astar_pathfinder.py      # A* algorithm for yard pathfinding
    │   ├── conflict_detector.py     # Detect resource conflicts
    │   └── movement_optimizer.py    # Optimize movement sequences
    ├── safety/
    │   ├── collision_detector.py    # Real-time collision detection
    │   ├── speed_controller.py      # Enforce speed limits
    │   └── signal_monitor.py        # Monitor yard signals
    └── simulation/
        └── shunting_simpy_adapter.py # Microscopic simulation integration
```

### Domain Model
```python
class ShuntingMission:
    """Complete shunting operation with safety and optimization."""
    mission_id: str
    mission_type: ShuntingType       # COLLECTION, DISTRIBUTION, SORTING, REPOSITIONING
    wagons: list[Wagon]
    origin_tracks: list[Track]
    destination_tracks: list[Track]
    assigned_locomotive: ShuntingLocomotive
    movement_plan: ShuntingPlan
    safety_constraints: SafetyConstraints
    priority: Priority               # URGENT, HIGH, NORMAL, LOW
    estimated_duration: float        # Minutes
    actual_duration: float | None

class ShuntingLocomotive:
    """Specialized locomotive for yard operations."""
    locomotive_id: str
    locomotive_type: ShuntingType    # DIESEL, ELECTRIC, BATTERY
    max_speed: float                 # km/h (typically 25-40 km/h in yards)
    tractive_effort: float           # kN
    max_wagons: int                  # Maximum wagons that can be pushed/pulled
    current_track: Track
    current_speed: float
    coupled_wagons: list[Wagon]
    available: bool
    maintenance_status: MaintenanceStatus

class ShuntingMovement:
    """Individual locomotive movement with safety protocols."""
    movement_id: str
    movement_type: MovementType      # PUSH, PULL, COUPLE, DECOUPLE, POSITION
    locomotive: ShuntingLocomotive
    wagons: list[Wagon]
    from_track: Track
    to_track: Track
    path: list[TrackElement]         # Detailed path through switches/junctions
    speed_profile: SpeedProfile      # Speed limits along path
    safety_checks: list[SafetyCheck] # Required safety validations
    estimated_time: float            # Minutes
    
class CouplingOperation:
    """Coupling/decoupling operation with safety protocols."""
    operation_id: str
    operation_type: CouplingType     # COUPLE, DECOUPLE
    locomotive: ShuntingLocomotive
    target_wagons: list[Wagon]
    coupling_point: CouplingPoint
    safety_protocol: CouplingProtocol
    required_checks: list[SafetyCheck]
    approach_speed: float            # Maximum approach speed
    
class ConflictResolution:
    """Resolution for resource conflicts between shunting operations."""
    conflict_id: str
    conflicting_missions: list[ShuntingMission]
    conflicted_resources: list[Resource] # Tracks, switches, locomotives
    resolution_strategy: ResolutionStrategy # PRIORITY, TIME_SLICE, REROUTE
    resolved_plan: ShuntingPlan
```

### Shunting Algorithms
```python
class MovementPlanner:
    def plan_shunting_sequence(
        self, 
        mission: ShuntingMission
    ) -> ShuntingPlan:
        """Create optimized sequence of movements for shunting mission."""
        
        # Find optimal paths for each movement
        paths = self.pathfinder.find_optimal_paths(
            mission.origin_tracks, 
            mission.destination_tracks
        )
        
        # Optimize movement sequence to minimize total time
        sequence = self.optimizer.optimize_sequence(paths, mission.wagons)
        
        # Apply safety constraints
        safe_sequence = self.safety_controller.apply_constraints(sequence)
        
        return ShuntingPlan(movements=safe_sequence)

class ConflictResolver:
    def resolve_conflicts(
        self, 
        missions: list[ShuntingMission]
    ) -> list[ShuntingPlan]:
        """Resolve resource conflicts between simultaneous missions."""
        
        # Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(missions)
        
        # Apply resolution strategies
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.HIGH:
                self.apply_priority_resolution(conflict)
            else:
                self.apply_time_slice_resolution(conflict)
                
        return [mission.movement_plan for mission in missions]

class SafetyController:
    def validate_movement_safety(
        self, 
        movement: ShuntingMovement
    ) -> SafetyValidation:
        """Validate movement complies with safety protocols."""
        
        checks = [
            self.check_speed_limits(movement),
            self.check_collision_risk(movement),
            self.check_signal_compliance(movement),
            self.check_track_capacity(movement)
        ]
        
        return SafetyValidation(
            is_safe=all(check.passed for check in checks),
            failed_checks=[check for check in checks if not check.passed]
        )
```

### Integration with Other Contexts
```python
# Yard Management requests shunting operation
yard_management.request_shunting(
    ShuntingRequest(
        wagons=["wagon_1", "wagon_2", "wagon_3"],
        from_area="classification_area",
        to_area="retrofit_area",
        priority=Priority.HIGH
    )
)

# Shunting Operations executes detailed movements
shunting_mission = ShuntingMission(
    wagons=wagons,
    movement_plan=movement_planner.plan_optimal_sequence(wagons),
    safety_constraints=safety_controller.get_constraints()
)

# PopUp Retrofit receives wagons after shunting
popup_retrofit.receive_wagons(
    wagons=completed_mission.wagons,
    delivery_track="retrofit_track_1"
)
```

## Rationale

### Why Separate Context?
- **Algorithm Complexity** - Sophisticated pathfinding, optimization, and conflict resolution
- **Safety Critical** - Complex safety protocols require dedicated modeling
- **Domain Richness** - Shunting operations complex enough to justify own context
- **Reusability** - Every railway yard needs shunting operations
- **Performance** - Specialized algorithms for microscopic simulation efficiency
- **Expertise** - Different domain knowledge than general yard management

### Why Microscopic Resolution?
- **Safety Requirements** - Need precise positioning and speed control
- **Resource Conflicts** - Detailed tracking of locomotive and track occupancy
- **Optimization Opportunities** - Fine-grained movement optimization
- **Realistic Simulation** - Accurate modeling of actual shunting operations

### Integration Strategy
- **Yard Management Context** → Requests shunting operations, provides infrastructure
- **Railway Infrastructure Context** → Provides detailed track topology for pathfinding
- **PopUp Retrofit Context** → Receives wagons via shunting operations
- **Inter-Yard Transport Context** → Coordinates with shunting for train assembly

## Consequences

### Positive
- **Safety Focus** - Dedicated safety protocols and collision avoidance
- **Optimization** - Specialized algorithms for efficient shunting operations
- **Reusability** - Shunting operations usable across different yard types
- **Performance** - Optimized microscopic simulation for complex movements
- **Domain Clarity** - Clear separation of shunting from general yard operations

### Negative
- **Complexity** - Additional bounded context increases system complexity
- **Integration Overhead** - Coordination with multiple other contexts
- **Performance Cost** - Microscopic simulation computationally intensive
- **Algorithm Development** - Requires sophisticated pathfinding and optimization algorithms

## Implementation Plan

### Phase 1: Core Shunting Model
1. Create `ShuntingMission` and `ShuntingLocomotive` domain models
2. Implement basic `ShuntingMovement` and `CouplingOperation`
3. Create simple pathfinding for yard movements
4. Integrate with yard management for basic shunting requests

### Phase 2: Safety and Optimization
1. Implement `SafetyController` with collision detection and speed limits
2. Create `MovementPlanner` with optimization algorithms
3. Add `ConflictResolver` for resource conflict resolution
4. Implement detailed coupling/decoupling protocols

### Phase 3: Advanced Algorithms
1. Implement A* pathfinding for complex yard layouts
2. Create advanced optimization algorithms for movement sequences
3. Add predictive conflict detection and prevention
4. Performance optimization for large-scale shunting operations

### Phase 4: Integration and Validation
1. Full integration with all yard contexts
2. Comprehensive safety validation and testing
3. Performance benchmarking with complex scenarios
4. Real-world validation with railway domain experts

## Related ADRs
- ADR-009: Yard Management Context - Requests shunting operations
- ADR-011: Inter-Yard Transport Context - Coordinates for train assembly
- ADR-010: PopUp Retrofit Context - Receives wagons via shunting
- ADR-008: Railway Infrastructure Context - Provides detailed track topology

## Migration Strategy
- **Current Workshop Operations** → Extract shunting operations to dedicated context
- **Locomotive Management** → Separate shunting locomotives from line locomotives
- **Movement Planning** → Create dedicated pathfinding and optimization
- **Safety Integration** → Implement safety protocols as first-class domain concepts

## Notes
Shunting Operations Context captures the complex microscopic domain of yard locomotive movements with dedicated safety protocols and optimization algorithms. Essential for realistic and safe simulation of railway yard operations during DAC migration.