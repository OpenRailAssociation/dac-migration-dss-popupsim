# Train Operations Context - Detailed Design

## Übersicht

Der Train Operations Context verwaltet den gesamten Zugbetrieb von der Ankunft bis zur Abfahrt. Er orchestriert Rangieroperationen, Wagengruppierung und die Koordination mit Workshop und Infrastructure.

## Domain Model

### **Entities**

#### **Train**
```python
@dataclass
class Train:
    id: TrainId
    arrival_time: datetime
    origin: str
    destination: str
    wagons: List[WagonId]
    priority: Priority
    status: TrainStatus
    current_location: Optional[TrackId]

    def get_total_length(self) -> Length:
        return sum(wagon.length for wagon in self.wagons)

    def get_total_weight(self) -> Weight:
        return sum(wagon.weight for wagon in self.wagons)

    def needs_retrofit(self) -> bool:
        return any(wagon.needs_retrofit() for wagon in self.wagons)

    def split_into_groups(self, max_group_size: int) -> List[WagonGroup]:
        groups = []
        for i in range(0, len(self.wagons), max_group_size):
            group_wagons = self.wagons[i:i + max_group_size]
            groups.append(WagonGroup(
                id=WagonGroupId(f"{self.id.value}_group_{len(groups)}"),
                wagons=group_wagons,
                parent_train_id=self.id,
                created_at=datetime.now()
            ))
        return groups
```

#### **Wagon**
```python
@dataclass
class Wagon:
    id: WagonId
    length: Length
    weight: Weight
    front_coupling: CouplingType
    rear_coupling: CouplingType
    current_location: Optional[TrackId]
    status: WagonStatus
    retrofit_history: List[RetrofitRecord]

    def needs_retrofit(self) -> bool:
        return (self.front_coupling == CouplingType.SCHRAUBKUPPLUNG or
                self.rear_coupling == CouplingType.SCHRAUBKUPPLUNG)

    def is_fully_dak_equipped(self) -> bool:
        return (self.front_coupling == CouplingType.DAK and
                self.rear_coupling == CouplingType.DAK)

    def get_retrofit_positions(self) -> List[CouplingPosition]:
        positions = []
        if self.front_coupling == CouplingType.SCHRAUBKUPPLUNG:
            positions.append(CouplingPosition.FRONT)
        if self.rear_coupling == CouplingType.SCHRAUBKUPPLUNG:
            positions.append(CouplingPosition.REAR)
        return positions
```

#### **WagonGroup**
```python
@dataclass
class WagonGroup:
    id: WagonGroupId
    wagons: List[WagonId]
    parent_train_id: TrainId
    current_location: Optional[TrackId]
    status: WagonGroupStatus
    created_at: datetime
    assigned_locomotive: Optional[LocomotiveId]

    def get_total_length(self) -> Length:
        return sum(wagon.length for wagon in self.wagons)

    def get_total_weight(self) -> Weight:
        return sum(wagon.weight for wagon in self.wagons)

    def has_retrofit_candidates(self) -> bool:
        return any(wagon.needs_retrofit() for wagon in self.wagons)

    def assign_locomotive(self, locomotive_id: LocomotiveId) -> None:
        if self.assigned_locomotive:
            raise WagonGroupAlreadyAssignedError()

        self.assigned_locomotive = locomotive_id
        self.status = WagonGroupStatus.LOCOMOTIVE_ASSIGNED

        # Domain Event
        DomainEvents.raise_event(WagonGroupLocomotiveAssignedEvent(
            group_id=self.id.value,
            locomotive_id=locomotive_id.value,
            timestamp=datetime.now()
        ))
```

#### **ShuntingOperation**
```python
@dataclass
class ShuntingOperation:
    id: ShuntingOperationId
    group_id: WagonGroupId
    from_track: TrackId
    to_track: TrackId
    locomotive_id: LocomotiveId
    worker_id: WorkerId
    status: ShuntingStatus
    scheduled_start: datetime
    actual_start: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_duration: timedelta

    def start_operation(self) -> None:
        if self.status != ShuntingStatus.SCHEDULED:
            raise InvalidShuntingStatusError()

        self.status = ShuntingStatus.IN_PROGRESS
        self.actual_start = datetime.now()

        # Domain Event
        DomainEvents.raise_event(ShuntingOperationStartedEvent(
            operation_id=self.id.value,
            group_id=self.group_id.value,
            from_track=self.from_track.value,
            to_track=self.to_track.value,
            locomotive_id=self.locomotive_id.value,
            worker_id=self.worker_id.value,
            timestamp=self.actual_start
        ))

    def complete_operation(self) -> None:
        if self.status != ShuntingStatus.IN_PROGRESS:
            raise InvalidShuntingStatusError()

        self.status = ShuntingStatus.COMPLETED
        self.completed_at = datetime.now()

        # Domain Event
        DomainEvents.raise_event(ShuntingOperationCompletedEvent(
            operation_id=self.id.value,
            group_id=self.group_id.value,
            from_track=self.from_track.value,
            to_track=self.to_track.value,
            locomotive_id=self.locomotive_id.value,
            worker_id=self.worker_id.value,
            duration_minutes=self.get_actual_duration_minutes(),
            timestamp=self.completed_at
        ))

    def get_actual_duration_minutes(self) -> Optional[int]:
        if self.actual_start and self.completed_at:
            return int((self.completed_at - self.actual_start).total_seconds() / 60)
        return None
```

### **Value Objects**

#### **TrainId, WagonId, WagonGroupId**
```python
@dataclass(frozen=True)
class TrainId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("TrainId cannot be empty")

@dataclass(frozen=True)
class WagonId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("WagonId cannot be empty")

@dataclass(frozen=True)
class WagonGroupId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("WagonGroupId cannot be empty")
```

#### **CouplingType, Priority, Weight**
```python
class CouplingType(Enum):
    SCHRAUBKUPPLUNG = "schraubkupplung"
    DAK = "dak"

class CouplingPosition(Enum):
    FRONT = "front"
    REAR = "rear"

@dataclass(frozen=True)
class Priority:
    value: int

    def __post_init__(self):
        if not 1 <= self.value <= 10:
            raise ValueError("Priority must be between 1 and 10")

@dataclass(frozen=True)
class Weight:
    tonnes: float

    def __post_init__(self):
        if self.tonnes < 0:
            raise ValueError("Weight cannot be negative")

    def __add__(self, other: 'Weight') -> 'Weight':
        return Weight(self.tonnes + other.tonnes)
```

#### **Status Enums**
```python
class TrainStatus(Enum):
    SCHEDULED = "scheduled"
    ARRIVED = "arrived"
    PROCESSING = "processing"
    COMPLETED = "completed"
    DEPARTED = "departed"

class WagonStatus(Enum):
    IN_TRANSIT = "in_transit"
    AT_COLLECTION_TRACK = "at_collection_track"
    AWAITING_RETROFIT = "awaiting_retrofit"
    IN_RETROFIT = "in_retrofit"
    RETROFIT_COMPLETED = "retrofit_completed"
    AT_PARKING_TRACK = "at_parking_track"
    READY_FOR_DEPARTURE = "ready_for_departure"

class WagonGroupStatus(Enum):
    CREATED = "created"
    LOCOMOTIVE_ASSIGNED = "locomotive_assigned"
    IN_TRANSIT = "in_transit"
    AT_DESTINATION = "at_destination"
    DISBANDED = "disbanded"

class ShuntingStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

## Domain Services

#### **TrainArrivalService**
```python
class TrainArrivalService:
    def __init__(self,
                 train_repository: TrainRepository,
                 infrastructure_service: InfrastructureQueryService,
                 capacity_rules: CapacityRulesService):
        self._trains = train_repository
        self._infrastructure = infrastructure_service
        self._capacity_rules = capacity_rules

    def process_train_arrival(self, train_arrival_data: TrainArrivalData) -> TrainArrivalResult:
        # 1. Erstelle Train Entity
        train = self._create_train_from_arrival_data(train_arrival_data)

        # 2. Finde geeignetes Sammelgleis
        suitable_track = self._find_suitable_collection_track(train)

        if not suitable_track:
            # Zug wird abgelehnt
            DomainEvents.raise_event(TrainRejectedEvent(
                train_id=train.id.value,
                reason="no_suitable_collection_track",
                required_length=train.get_total_length().meters,
                timestamp=datetime.now()
            ))
            return TrainArrivalResult.rejected("No suitable collection track available")

        # 3. Reserviere Platz auf Sammelgleis
        train.current_location = suitable_track.id
        train.status = TrainStatus.ARRIVED

        # 4. Speichere Train
        self._trains.save(train)

        # 5. Domain Event
        DomainEvents.raise_event(TrainArrivedEvent(
            train_id=train.id.value,
            arrival_track=suitable_track.id.value,
            wagon_count=len(train.wagons),
            total_length=train.get_total_length().meters,
            total_weight=train.get_total_weight().tonnes,
            priority=train.priority.value,
            timestamp=train.arrival_time
        ))

        return TrainArrivalResult.accepted(train.id, suitable_track.id)

    def _find_suitable_collection_track(self, train: Train) -> Optional[TrackInfo]:
        # Hole alle Sammelgleise
        collection_tracks = self._infrastructure.get_available_tracks_by_type(
            "sammelgleis",
            train.get_total_length().meters
        )

        # Wende Kapazitätsregeln an (25m Puffer)
        for track_info in collection_tracks:
            if self._capacity_rules.can_accommodate_with_buffer(
                track_info,
                train.get_total_length().meters
            ):
                return track_info

        return None
```

#### **WagonGroupingService**
```python
class WagonGroupingService:
    def __init__(self,
                 wagon_repository: WagonRepository,
                 grouping_rules: WagonGroupingRulesService):
        self._wagons = wagon_repository
        self._grouping_rules = grouping_rules

    def create_wagon_groups(self, train: Train, max_group_size: int) -> List[WagonGroup]:
        # 1. Lade alle Wagen des Zugs
        wagons = [self._wagons.get_by_id(wagon_id) for wagon_id in train.wagons]

        # 2. Sortiere nach Priorität (Retrofit-Kandidaten zuerst)
        sorted_wagons = self._grouping_rules.sort_wagons_by_priority(wagons)

        # 3. Erstelle Gruppen
        groups = []
        for i in range(0, len(sorted_wagons), max_group_size):
            group_wagons = sorted_wagons[i:i + max_group_size]

            group = WagonGroup(
                id=WagonGroupId(f"{train.id.value}_group_{len(groups) + 1}"),
                wagons=[w.id for w in group_wagons],
                parent_train_id=train.id,
                current_location=train.current_location,
                status=WagonGroupStatus.CREATED,
                created_at=datetime.now(),
                assigned_locomotive=None
            )

            groups.append(group)

            # Domain Event
            DomainEvents.raise_event(WagonGroupCreatedEvent(
                group_id=group.id.value,
                train_id=train.id.value,
                wagon_count=len(group_wagons),
                has_retrofit_candidates=group.has_retrofit_candidates(),
                timestamp=group.created_at
            ))

        return groups
```

#### **ShuntingCoordinationService**
```python
class ShuntingCoordinationService:
    def __init__(self,
                 resource_service: ResourceQueryService,
                 infrastructure_service: InfrastructureQueryService,
                 route_service: RouteCalculationService):
        self._resources = resource_service
        self._infrastructure = infrastructure_service
        self._routes = route_service

    def schedule_shunting_operation(self,
                                  group: WagonGroup,
                                  target_track_type: str) -> Optional[ShuntingOperation]:
        # 1. Finde verfügbare Lokomotive
        locomotive = self._resources.find_available_locomotive(
            min_capacity=group.get_total_weight().tonnes
        )

        if not locomotive:
            return None

        # 2. Finde verfügbaren Rangierbegleiter
        worker = self._resources.find_available_worker(["shunting_operations"])

        if not worker:
            return None

        # 3. Finde Zielgleis
        target_track = self._infrastructure.find_suitable_track(
            track_type=target_track_type,
            required_capacity=group.get_total_length().meters
        )

        if not target_track:
            return None

        # 4. Berechne Route
        route = self._routes.calculate_route(
            from_track=group.current_location,
            to_track=TrackId(target_track.id)
        )

        if not route:
            return None

        # 5. Erstelle Shunting Operation
        operation = ShuntingOperation(
            id=ShuntingOperationId(f"shunt_{group.id.value}_{int(datetime.now().timestamp())}"),
            group_id=group.id,
            from_track=group.current_location,
            to_track=TrackId(target_track.id),
            locomotive_id=LocomotiveId(locomotive.id),
            worker_id=WorkerId(worker.id),
            status=ShuntingStatus.SCHEDULED,
            scheduled_start=datetime.now() + timedelta(minutes=5),
            actual_start=None,
            completed_at=None,
            estimated_duration=route.estimated_travel_time
        )

        return operation
```

## Domain Events

#### **Train Events**
```python
@dataclass(frozen=True)
class TrainArrivedEvent:
    train_id: str
    arrival_track: str
    wagon_count: int
    total_length: float
    total_weight: float
    priority: int
    timestamp: datetime

@dataclass(frozen=True)
class TrainRejectedEvent:
    train_id: str
    reason: str
    required_length: float
    timestamp: datetime

@dataclass(frozen=True)
class WagonGroupCreatedEvent:
    group_id: str
    train_id: str
    wagon_count: int
    has_retrofit_candidates: bool
    timestamp: datetime

@dataclass(frozen=True)
class ShuntingOperationStartedEvent:
    operation_id: str
    group_id: str
    from_track: str
    to_track: str
    locomotive_id: str
    worker_id: str
    timestamp: datetime

@dataclass(frozen=True)
class ShuntingOperationCompletedEvent:
    operation_id: str
    group_id: str
    from_track: str
    to_track: str
    locomotive_id: str
    worker_id: str
    duration_minutes: int
    timestamp: datetime

@dataclass(frozen=True)
class WagonRetrofitRequestedEvent:
    wagon_id: str
    group_id: str
    coupling_positions: List[str]
    current_location: str
    priority: int
    timestamp: datetime
```

## Application Services

#### **TrainOperationsService**
```python
class TrainOperationsService:
    """Öffentliche API für Train Operations Context"""

    def __init__(self,
                 train_repository: TrainRepository,
                 wagon_group_repository: WagonGroupRepository,
                 arrival_service: TrainArrivalService,
                 grouping_service: WagonGroupingService,
                 shunting_service: ShuntingCoordinationService):
        self._trains = train_repository
        self._groups = wagon_group_repository
        self._arrival = arrival_service
        self._grouping = grouping_service
        self._shunting = shunting_service

    def process_train_arrival(self, arrival_data: TrainArrivalData) -> TrainArrivalResult:
        """Verarbeitet Zugankunft"""
        return self._arrival.process_train_arrival(arrival_data)

    def create_wagon_groups(self, train_id: str, max_group_size: int) -> List[str]:
        """Erstellt Wagengruppen aus Zug"""
        train = self._trains.get_by_id(TrainId(train_id))
        groups = self._grouping.create_wagon_groups(train, max_group_size)

        # Speichere Gruppen
        for group in groups:
            self._groups.save(group)

        return [group.id.value for group in groups]

    def schedule_workshop_transfer(self, group_id: str) -> Optional[str]:
        """Plant Transfer zur Werkstatt"""
        group = self._groups.get_by_id(WagonGroupId(group_id))

        if not group.has_retrofit_candidates():
            return None

        operation = self._shunting.schedule_shunting_operation(
            group,
            "werkstatt_zufuehrung"
        )

        if operation:
            # Domain Event für Workshop Context
            DomainEvents.raise_event(WorkshopTransferRequestedEvent(
                group_id=group_id,
                operation_id=operation.id.value,
                estimated_arrival=operation.scheduled_start + operation.estimated_duration,
                wagon_count=len(group.wagons),
                timestamp=datetime.now()
            ))

            return operation.id.value

        return None

    def get_train_status(self, train_id: str) -> Optional[TrainInfo]:
        """Holt Zugstatus"""
        try:
            train = self._trains.get_by_id(TrainId(train_id))
            return TrainInfo(
                id=train.id.value,
                status=train.status.value,
                current_location=train.current_location.value if train.current_location else None,
                wagon_count=len(train.wagons),
                total_length=train.get_total_length().meters,
                total_weight=train.get_total_weight().tonnes,
                priority=train.priority.value,
                arrival_time=train.arrival_time
            )
        except:
            return None
```

## Data Transfer Objects (DTOs)

#### **TrainInfo**
```python
@dataclass(frozen=True)
class TrainInfo:
    id: str
    status: str
    current_location: Optional[str]
    wagon_count: int
    total_length: float
    total_weight: float
    priority: int
    arrival_time: datetime

@dataclass(frozen=True)
class WagonInfo:
    id: str
    length: float
    weight: float
    front_coupling_type: str
    rear_coupling_type: str
    current_location: Optional[str]
    needs_retrofit: bool
    is_fully_dak_equipped: bool
    status: str

@dataclass(frozen=True)
class WagonGroupInfo:
    id: str
    train_id: str
    wagon_count: int
    total_length: float
    total_weight: float
    current_location: Optional[str]
    status: str
    has_retrofit_candidates: bool
    assigned_locomotive: Optional[str]

@dataclass(frozen=True)
class ShuntingOperationInfo:
    id: str
    group_id: str
    from_track: str
    to_track: str
    locomotive_id: str
    worker_id: str
    status: str
    estimated_duration_minutes: int
    actual_duration_minutes: Optional[int]
```

## Integration mit anderen Contexts (Monolith)

### **Customer von Infrastructure Context**
```python
# Direkte Service-Aufrufe (keine HTTP APIs)
infrastructure_service = get_infrastructure_service()  # Dependency Injection
track_info = infrastructure_service.get_available_tracks_by_type("sammelgleis", 500.0)
route = infrastructure_service.calculate_route(from_track, to_track)
```

### **Customer von Resource Management Context**
```python
# Direkte Service-Aufrufe
resource_service = get_resource_service()  # Dependency Injection
locomotive = resource_service.find_available_locomotive(min_capacity=80.0)
worker = resource_service.find_available_worker(["shunting_operations"])
```

### **Supplier für Workshop Context**
```python
# In-Memory Event Bus
event_bus = get_event_bus()  # Shared Event Bus
event_bus.publish(WorkshopTransferRequestedEvent(...))
```

### **Integration mit Simulation Control**
```python
# Direkte Orchestrierung über Service-Aufrufe
simulation_control_service.register_context(train_operations_service)
# Events über shared Event Bus
```

## SimPy Integration

### **Train Arrival Process**
```python
def train_arrival_simpy_process(env: simpy.Environment,
                               train_arrival_data: TrainArrivalData,
                               train_ops_service: TrainOperationsService):
    # Warte bis Ankunftszeit
    yield env.timeout(calculate_arrival_delay(train_arrival_data.scheduled_time))

    # Verarbeite Ankunft
    result = train_ops_service.process_train_arrival(train_arrival_data)

    if result.accepted:
        # Starte Wagengruppierung nach 5-15 Minuten
        processing_time = random.uniform(5, 15)
        yield env.timeout(processing_time)

        # Erstelle Wagengruppen
        group_ids = train_ops_service.create_wagon_groups(
            result.train_id,
            max_group_size=3
        )

        # Starte Transfers für Retrofit-Kandidaten
        for group_id in group_ids:
            operation_id = train_ops_service.schedule_workshop_transfer(group_id)
            if operation_id:
                env.process(shunting_operation_process(env, operation_id, train_ops_service))
```

## Repository Interfaces

#### **TrainRepository**
```python
class TrainRepository(ABC):
    @abstractmethod
    def get_by_id(self, train_id: TrainId) -> Train:
        pass

    @abstractmethod
    def find_by_status(self, status: TrainStatus) -> List[Train]:
        pass

    @abstractmethod
    def find_by_location(self, track_id: TrackId) -> List[Train]:
        pass

    @abstractmethod
    def save(self, train: Train) -> None:
        pass

class WagonGroupRepository(ABC):
    @abstractmethod
    def get_by_id(self, group_id: WagonGroupId) -> WagonGroup:
        pass

    @abstractmethod
    def find_by_train(self, train_id: TrainId) -> List[WagonGroup]:
        pass

    @abstractmethod
    def find_retrofit_candidates(self) -> List[WagonGroup]:
        pass

    @abstractmethod
    def save(self, group: WagonGroup) -> None:
        pass
```

## Nächste Schritte

1. **Repository Implementierungen** für Train und WagonGroup
2. **SimPy Process Integration** für alle Operationen
3. **Event Handler** für Workshop Integration
4. **Performance Tests** mit großen Zugmengen

**Train Operations Context ist jetzt vollständig definiert.**
