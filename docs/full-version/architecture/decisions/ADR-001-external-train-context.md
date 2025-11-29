# ADR-006: External Train Context with Hexagonal Architecture

**Status:** Accepted  
**Date:** 2025-01-27  
**Deciders:** Architecture Team  

## Context

The current simulation treats all trains uniformly within the Workshop Operations Context, mixing external train arrivals (from external railway network) with internal yard operations. This creates confusion between:

- **External trains**: Scheduled arrivals delivering wagons from outside the facility
- **Internal operations**: Yard movements, consist formation, and shunting within the facility

Analysis shows these represent fundamentally different domains with distinct:
- Business rules and constraints
- Stakeholders (external railway vs internal operations)
- Integration requirements (APIs, EDI, manual notifications)
- Ubiquitous language and concepts

## Decision

We will create a dedicated **External Train Context** as a separate bounded context with hexagonal architecture to handle external train operations.

### Core Components

1. **External Train Context** - New bounded context
2. **Hexagonal Architecture** - Ports and adapters for flexible integration
3. **Domain Events** - Clean integration with existing contexts
4. **Anti-Corruption Layer** - Protect domain from external system complexity

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                External Train Context                    │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │   Domain Core   │    │        Application          │ │
│  │                 │    │                             │ │
│  │ • ExternalTrain │    │ • ExternalTrainService      │ │
│  │ • DeliveryManif │    │ • ArrivalScheduler          │ │
│  │ • ArrivalSched  │    │ • ManifestProcessor         │ │
│  └─────────────────┘    └─────────────────────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                Infrastructure                       │ │
│  │                                                     │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │ │
│  │ │   File      │ │     API     │ │      EDI        │ │ │
│  │ │  Adapter    │ │   Adapter   │ │    Adapter      │ │ │
│  │ └─────────────┘ └─────────────┘ └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              │ Domain Events
                              ▼
┌─────────────────────────────────────────────────────────┐
│              Yard Operations Context                    │
│                                                         │
│  • Receives: WagonsDeliveredEvent                      │
│  • Handles: Hump operations, classification            │
└─────────────────────────────────────────────────────────┘
```

### Integration Adapters

**Primary Port:**
```python
class ExternalTrainPort(ABC):
    @abstractmethod
    def get_arrival_schedule(self, date_range: DateRange) -> list[TrainArrival]: ...
    
    @abstractmethod
    def get_delivery_manifest(self, train_id: str) -> DeliveryManifest: ...
```

**Adapters:**
- **FileAdapter** - Current JSON/CSV scenario files
- **ApiAdapter** - REST API integration with external railway systems
- **EdiAdapter** - EDI message processing for industry standards
- **ManualAdapter** - Manual entry interface for ad-hoc arrivals

### Domain Events

```python
@dataclass(frozen=True)
class ExternalTrainArrivedEvent(DomainEvent):
    train_id: str
    arrival_time: datetime
    origin_station: str
    
@dataclass(frozen=True) 
class WagonsDeliveredEvent(DomainEvent):
    train_id: str
    wagons: list[Wagon]
    delivery_manifest: DeliveryManifest
    delivery_location: str
```

## Consequences

### Positive

- **Clear Domain Separation**: External vs internal train operations have distinct contexts
- **Integration Flexibility**: Hexagonal architecture enables multiple data sources (files, APIs, EDI)
- **Future-Proof**: Easy to add new integration methods without changing core logic
- **Testability**: Can mock external arrivals independently of yard operations
- **Business Alignment**: Matches real-world railway operational boundaries

### Negative

- **Implementation Complexity**: Additional context and integration layer
- **Initial Development Effort**: Refactoring existing train arrival logic
- **Testing Overhead**: More integration points to test

### Neutral

- **Event-Driven Integration**: Maintains loose coupling between contexts
- **Backward Compatibility**: Existing file-based scenarios continue to work via FileAdapter

## Implementation Plan

### Phase 1: Context Foundation
1. Create External Train Context structure
2. Define domain entities (ExternalTrain, DeliveryManifest, ArrivalSchedule)
3. Implement primary port interface

### Phase 2: File Adapter Migration
1. Create FileAdapter implementing ExternalTrainPort
2. Migrate existing train arrival logic to new context
3. Maintain backward compatibility with current scenarios

### Phase 3: API Integration
1. Implement ApiAdapter for REST API integration
2. Add configuration for external railway system endpoints
3. Implement error handling and retry logic

### Phase 4: Advanced Integrations
1. Add EdiAdapter for industry-standard messaging
2. Implement ManualAdapter for operational flexibility
3. Add monitoring and alerting for external integrations

## References

- [ADR-001: Hexagonal Pipeline Architecture](ADR-001-hexagonal-pipeline-architecture.md)
- [ADR-004: 3 Bounded Context Architecture](ADR-004-3-bounded-context-architecture.md)
- [Building Block View - Level 2](../05-building-blocks.md#52-level-2-configuration-context)
- Railway Industry EDI Standards