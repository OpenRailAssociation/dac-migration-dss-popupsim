# ADR-010: PopUp Retrofit Context

## Status
Proposed

## Context
DAC migration requires specialized temporary retrofit facilities called "PopUp workshops" - mobile/temporary installations with tents spanning across railway tracks for rapid DAC installation. These are fundamentally different from permanent workshop facilities and have unique operational characteristics, resource requirements, and constraints.

### PopUp Workshop Characteristics
- **Temporary Installation** - Tents and mobile equipment across tracks
- **Rapid Deployment** - Quick setup/teardown for migration timeline
- **Track Spanning** - Tents cover multiple tracks simultaneously
- **Specialized Equipment** - Mobile cranes, portable tools, temporary utilities
- **Weather Dependent** - Operations affected by weather conditions
- **Capacity Constraints** - Limited by tent size and mobile equipment

### Current Problem
Retrofit operations are mixed within general workshop operations context, but PopUp workshops have distinct:
- **Setup/Teardown Processes** - Temporary facility management
- **Weather Dependencies** - Operational constraints
- **Mobile Resource Management** - Portable equipment and utilities
- **Tent Configuration** - Track spanning and capacity planning
- **Rapid Deployment Requirements** - Time-critical setup

## Decision
Create **PopUp Retrofit Context** as dedicated bounded context for temporary DAC installation facilities with tent-based operations.

### Architecture
```
popup_retrofit/
├── domain/
│   ├── aggregates/
│   │   ├── popup_workshop.py        # Complete PopUp facility
│   │   └── retrofit_campaign.py     # Time-bounded retrofit operation
│   ├── entities/
│   │   ├── tent_installation.py     # Tent spanning tracks
│   │   ├── mobile_equipment.py      # Portable cranes, tools
│   │   ├── retrofit_bay.py          # Individual work positions
│   │   ├── dac_component.py         # DAC parts inventory
│   │   └── specialist_team.py       # Skilled retrofit technicians
│   ├── services/
│   │   ├── setup_orchestrator.py    # Facility deployment/teardown
│   │   ├── retrofit_processor.py    # DAC installation workflow
│   │   ├── weather_monitor.py       # Weather impact assessment
│   │   ├── capacity_planner.py      # Tent and equipment optimization
│   │   └── quality_controller.py    # Installation validation
│   └── value_objects/
│       ├── tent_configuration.py    # Track spanning setup
│       ├── weather_conditions.py    # Operational constraints
│       ├── setup_timeline.py        # Deployment schedule
│       └── retrofit_specification.py # DAC installation requirements
├── application/
│   ├── popup_orchestrator.py        # Multi-workshop coordination
│   ├── campaign_manager.py          # Time-bounded operations
│   └── services/
│       ├── deployment_service.py    # Setup/teardown management
│       ├── retrofit_scheduling_service.py # Work scheduling
│       ├── resource_planning_service.py # Mobile equipment allocation
│       └── weather_planning_service.py # Weather-dependent scheduling
└── infrastructure/
    ├── equipment/
    │   ├── mobile_crane_pool.py      # Portable lifting equipment
    │   ├── tent_system_manager.py    # Tent deployment/management
    │   └── utility_connections.py    # Temporary power/air/tools
    ├── weather/
    │   ├── weather_service_adapter.py # External weather data
    │   └── weather_impact_calculator.py # Operational impact
    └── simulation/
        └── popup_simpy_adapter.py    # PopUp-specific simulation
```

### Domain Model
```python
class PopUpWorkshop:
    """Temporary retrofit facility with tent installations across tracks."""
    workshop_id: str
    location: GeoLocation
    tent_installations: list[TentInstallation]
    mobile_equipment: MobileEquipmentPool
    specialist_teams: list[SpecialistTeam]
    setup_status: SetupStatus              # DEPLOYING, OPERATIONAL, TEARDOWN
    weather_constraints: WeatherConstraints
    
    def deploy_facility(self, tracks: list[Track]) -> None:
        """Deploy tents and equipment across specified tracks."""
        
    def process_wagon(self, wagon: Wagon) -> RetrofitResult:
        """Perform DAC installation in PopUp facility."""

class TentInstallation:
    """Tent structure spanning multiple railway tracks."""
    tent_id: str
    covered_tracks: list[Track]
    work_positions: list[RetrofitBay]
    weather_protection: WeatherProtection
    utility_connections: UtilityConnections
    
class MobileEquipmentPool:
    """Portable equipment for PopUp operations."""
    mobile_cranes: ResourcePool
    portable_tools: ResourcePool
    testing_equipment: ResourcePool
    parts_inventory: PartsInventory
    
class RetrofitCampaign:
    """Time-bounded PopUp retrofit operation."""
    campaign_id: str
    start_date: datetime
    end_date: datetime
    target_wagons: int
    popup_workshops: list[PopUpWorkshop]
    deployment_timeline: SetupTimeline
```

### PopUp-Specific Operations
```python
# Weather-dependent operations
class WeatherMonitor:
    def assess_operational_impact(self, conditions: WeatherConditions) -> OperationalImpact:
        """Determine if PopUp operations can continue safely."""
        
# Rapid deployment
class SetupOrchestrator:
    def deploy_popup_workshop(self, location: Location, tracks: list[Track]) -> None:
        """Deploy tent installation and mobile equipment."""
        
    def teardown_popup_workshop(self, workshop: PopUpWorkshop) -> None:
        """Dismantle and relocate PopUp facility."""

# Capacity optimization
class CapacityPlanner:
    def optimize_tent_configuration(self, tracks: list[Track]) -> TentConfiguration:
        """Optimize tent placement for maximum throughput."""
```

## Rationale

### Why Dedicated Context?
- **Specialized Domain** - PopUp workshops are fundamentally different from permanent facilities
- **Unique Constraints** - Weather, temporary setup, mobile equipment
- **Operational Complexity** - Setup/teardown, tent management, rapid deployment
- **Business Critical** - Core to DAC migration strategy and timeline
- **Reusability** - Other temporary railway installations could use this context

### Why Separate from Yard Management?
- **Different Lifecycle** - Temporary vs permanent facilities
- **Different Resources** - Mobile vs fixed equipment
- **Different Constraints** - Weather, setup time, portability
- **Different Expertise** - PopUp deployment vs yard operations

### Integration Strategy
- **Yard Management Context** → Provides location and basic infrastructure
- **PopUp Retrofit Context** → Handles specialized temporary operations
- **Railway Infrastructure Context** → Provides track topology for tent placement
- **External Train Context** → Delivers wagons to PopUp facilities

## Consequences

### Positive
- **Domain Alignment** - Matches real PopUp workshop operations
- **Specialized Optimization** - Weather planning, rapid deployment, capacity optimization
- **Operational Realism** - Models actual DAC migration constraints
- **Flexibility** - Can model different PopUp configurations and campaigns
- **Business Value** - Direct support for DAC migration planning

### Negative
- **Additional Complexity** - Another bounded context to manage
- **Integration Overhead** - Coordination with yard and infrastructure contexts
- **Weather Dependencies** - External data requirements for realistic simulation
- **Resource Modeling** - Complex mobile equipment and tent management

## Implementation Plan

### Phase 1: Core PopUp Model
1. Create `PopUpWorkshop` aggregate with basic tent operations
2. Implement `TentInstallation` and `MobileEquipmentPool`
3. Create basic retrofit workflow for PopUp environment
4. Integrate with existing wagon processing

### Phase 2: Deployment Operations
1. Implement `SetupOrchestrator` for facility deployment/teardown
2. Create `CapacityPlanner` for tent configuration optimization
3. Add deployment timeline and resource planning
4. Create PopUp-specific simulation scenarios

### Phase 3: Weather Integration
1. Implement `WeatherMonitor` with external weather data
2. Add weather-dependent operational constraints
3. Create weather planning and scheduling services
4. Validate weather impact on throughput

### Phase 4: Campaign Management
1. Implement `RetrofitCampaign` for time-bounded operations
2. Add multi-PopUp coordination and resource sharing
3. Create campaign optimization and planning tools
4. Performance validation with large-scale scenarios

## Related ADRs
- ADR-009: Yard Management Context - Provides PopUp location infrastructure
- ADR-008: Railway Infrastructure Context - Provides track topology for tent placement
- ADR-007: Configuration Context Restructure - Separates PopUp configuration

## Migration Strategy
- **Current Workshop Operations** → Extract PopUp-specific operations
- **Resource Management** → Create mobile equipment pools
- **Weather Integration** → Add external weather service adapters
- **Scenario Updates** → Convert existing scenarios to use PopUp context

## Notes
PopUp Retrofit Context captures the unique domain of temporary DAC installation facilities, enabling realistic simulation of the actual migration strategy with tent-based workshops spanning railway tracks. Essential for accurate planning of the 3-week "Big Bang" migration period.