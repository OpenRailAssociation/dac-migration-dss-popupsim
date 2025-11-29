# ADR-004: Yard Operations Context

**Status:** Proposed  
**Date:** 2025-01-16  
**Deciders:** Architecture Team  

## Context

Current workshop operations context mixes multiple yard operations without clear separation. In reality, a yard is a unified facility with different operational areas (classification, retrofitting, parking) rather than separate yard types. A retrofitting yard may have parking tracks, classification areas, and maintenance facilities all within the same physical yard.

### Current Problems
- **Mixed Operations** - Workshop context handles parking, retrofitting, classification
- **No Yard Boundaries** - Resources not properly assigned to specific yards
- **Scalability Issues** - Cannot model multiple yards or complex yard layouts
- **Resource Confusion** - Locomotives, tracks, equipment not yard-specific

### Real-World Yard Structure
```
Yard (Physical Facility)
├── Classification Area    # Hump, selector, collection tracks
├── Retrofitting Area     # Workshop tracks, retrofit stations
├── Parking Area          # Storage tracks, long-term parking
├── Maintenance Area      # Repair facilities, inspection
└── Interchange Area      # External railway connections
```

## Decision

Create **Yard Operations Context** as dedicated bounded context for unified yard operations with area-based organization.

### Architecture
```
yard_operations/
├── domain/
│   ├── aggregates/
│   │   └── yard.py                  # Main yard aggregate
│   ├── entities/
│   │   ├── yard_area.py             # Operational area within yard
│   │   ├── classification_area.py   # Hump/selector operations
│   │   ├── retrofitting_area.py     # DAC installation
│   │   ├── parking_area.py          # Storage operations
│   │   ├── maintenance_area.py      # Repair/inspection
│   │   └── interchange_area.py      # External connections
│   ├── services/
│   │   ├── yard_coordinator.py      # Cross-area coordination
│   │   ├── area_selector.py         # Route wagons to correct area
│   │   ├── resource_allocator.py    # Yard-wide resource management
│   │   └── capacity_manager.py      # Yard capacity planning
│   └── value_objects/
│       ├── yard_layout.py           # Physical yard structure
│       ├── area_capacity.py         # Area-specific capacity
│       └── yard_configuration.py    # Operational parameters
├── application/
│   ├── yard_orchestrator.py         # Multi-yard coordination
│   ├── area_coordinator.py          # Area-specific operations
│   └── services/
│       ├── wagon_routing_service.py # Route wagons between areas
│       ├── resource_planning_service.py # Resource allocation
│       └── capacity_planning_service.py # Capacity management
└── infrastructure/
    ├── resources/
    │   ├── yard_resource_pool.py     # Yard-specific resources
    │   ├── area_resource_manager.py  # Area resource allocation
    │   └── inter_yard_transport.py   # Movement between yards
    └── simulation/
        └── yard_simpy_adapter.py     # Yard simulation integration
```

### Domain Model
```python
class Yard:
    """Main yard aggregate - unified facility with multiple operational areas."""
    yard_id: str
    name: str
    location: GeoLocation
    areas: dict[str, YardArea]           # Classification, retrofitting, parking, etc.
    shared_resources: ResourcePool       # Locomotives, mobile equipment
    yard_layout: YardLayout              # Physical track connections
    
    def route_wagon_to_area(self, wagon: Wagon, operation: Operation) -> YardArea:
        """Route wagon to appropriate area based on required operation."""
        
    def allocate_resources(self, area: YardArea, resource_type: ResourceType) -> Resource:
        """Allocate shared resources to specific area."""

class YardArea:
    """Base class for operational areas within a yard."""
    area_id: str
    area_type: AreaType                  # CLASSIFICATION, RETROFITTING, PARKING
    tracks: list[Track]
    dedicated_resources: ResourcePool    # Area-specific equipment
    capacity: AreaCapacity
    
class ClassificationArea(YardArea):
    """Hump/selector operations for wagon sorting."""
    hump_tracks: list[Track]
    collection_tracks: list[Track]
    
    def process_incoming_train(self, train: Train) -> list[WagonGroup]:
        """Sort wagons by destination/operation type."""
    
    def classify_wagon(self, wagon: Wagon) -> ClassificationDecision:
        """Determine wagon routing (retrofit, reject, bypass)."""

class RetrofittingArea(YardArea):
    """DAC installation workshop operations."""
    workshop_tracks: list[Track]
    retrofit_stations: list[RetrofitStation]  # Work bays with tools
    
    def retrofit_wagon(self, wagon: Wagon) -> None:
        """Perform DAC installation with technicians and hand tools."""
    
    def allocate_station(self, wagon: Wagon) -> RetrofitStation | None:
        """Allocate available retrofit station for wagon."""

class ParkingArea(YardArea):
    """Storage for wagons awaiting processing or pickup."""
    storage_tracks: list[Track]
    storage_capacity: int
    
    def store_wagon(self, wagon: Wagon, expected_duration: float) -> None:
        """Store wagon for specified duration."""
    
    def retrieve_wagon(self, wagon_id: str) -> Wagon | None:
        """Retrieve wagon from storage."""
```

### Multi-Yard Scenarios
```python
# Scenario: Multiple yards in DAC migration
yards = {
    "classification_yard": Yard(
        areas={
            "hump": ClassificationArea(),
            "collection": ParkingArea(),
            "departure": ClassificationArea()
        }
    ),
    "retrofitting_yard": Yard(
        areas={
            "intake": ParkingArea(),           # Wagons awaiting retrofit
            "workshop": RetrofittingArea(),    # DAC installation
            "completed": ParkingArea(),        # Retrofitted wagons
            "maintenance": MaintenanceArea()   # Repairs if needed
        }
    )
}
```

## Rationale

### Why "Yard Operations" not "Yard Management"?
- **Operations Focus** - Emphasizes actual operational work, not administrative planning
- **Domain Language** - Railway operators talk about "yard operations"
- **Clear Intent** - Immediately conveys this is about executing yard work

### Why Unified Yard Model?
- **Reality Alignment** - Matches real railway yard operations
- **Flexibility** - Yards can have any combination of areas
- **Resource Sharing** - Locomotives and equipment shared across areas
- **Scalability** - Easy to add new area types or yard configurations

### Why Area-Based Organization?
- **Operational Clarity** - Each area has specific purpose and resources
- **Capacity Management** - Area-specific capacity limits and planning
- **Workflow Routing** - Clear routing between areas based on operations
- **Resource Allocation** - Dedicated vs shared resource management

### Why No Cranes?
- **DAC Retrofit Reality** - DAC installation uses hand tools and technicians, not cranes
- **Workshop Equipment** - Retrofit stations have torque tools, testing equipment, mobile platforms
- **Simplicity** - Avoid modeling unnecessary heavy equipment

### Integration Strategy
- **Railway Infrastructure Context** → Provides yard topology and track connections
- **External Train Context** → Delivers trains to appropriate yard entrance
- **Current Workshop Operations** → Becomes RetrofittingArea within yards
- **Resource Management** → Yard-specific and area-specific allocation

## Consequences

### Positive
- **Realistic Modeling** - Matches real-world yard operations
- **Flexible Configuration** - Yards can have any combination of areas
- **Resource Efficiency** - Proper sharing of locomotives and equipment
- **Scalability** - Easy to model complex multi-yard facilities
- **Clear Boundaries** - Proper separation between yard operations
- **Orchestrator Reduction** - Extracts ~300-400 lines from orchestrator

### Negative
- **Complexity** - More sophisticated domain model required
- **Migration Effort** - Need to restructure existing workshop operations
- **Performance** - Additional coordination overhead between areas
- **Configuration** - More complex yard setup and configuration

## Implementation Plan

### Phase 1: Core Yard Model
1. Create `Yard` aggregate with basic area management
2. Implement `YardArea` base class and area types
3. Create `YardCoordinator` for cross-area operations
4. Extract wagon classification from orchestrator

### Phase 2: Area Specialization
1. Implement `ClassificationArea` with hump operations
2. Create `ParkingArea` with storage management
3. Extract parking operations from orchestrator
4. Implement area-specific resource allocation

### Phase 3: Multi-Yard Support
1. Create `YardOrchestrator` for multi-yard coordination
2. Implement inter-yard wagon transport
3. Add yard-to-yard routing and scheduling
4. Create complex multi-yard scenarios

### Phase 4: Advanced Features
1. Implement dynamic area reconfiguration
2. Add predictive capacity planning
3. Create optimization algorithms for area utilization
4. Performance tuning for large yard operations

## Related ADRs
- [ADR-001: External Train Context](ADR-001-external-train-context.md) - Delivers trains to yards
- [ADR-003: Railway Infrastructure Context](ADR-003-railway-infrastructure-context.md) - Provides yard topology
- [ADR-007: Shunting Operations Context](ADR-007-shunting-operations-context.md) - Handles yard movements

## Migration Strategy
- **Current Workshop Operations** → Becomes `RetrofittingArea` within yards
- **Parking Coordinator** → Becomes `ParkingArea` operations
- **Wagon Classification** → Moves to `ClassificationArea`
- **Resource Pools** → Yard-specific and area-specific allocation
- **Backward Compatibility** - Maintain single-yard scenarios during transition

## Notes

Yard Operations Context enables realistic modeling of complex railway facilities while maintaining operational clarity through area-based organization. Essential for accurate simulation of DAC migration logistics across multiple yard facilities.

**Key Correction**: DAC retrofit uses technicians with hand tools and mobile platforms, not cranes. Retrofit stations are work bays with specialized equipment, not heavy lifting facilities.
