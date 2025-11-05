# Workshop Context - Detailed Design

## Übersicht

Der Workshop Context verwaltet DAK-Umrüstungen von Wagen. Er empfängt Umrüstungsaufträge, plant Arbeitsschritte, führt Umrüstungen durch und benachrichtigt über Fertigstellung.

## Domain Model

### **Entities**

#### **RetrofitOrder (Umrüstungsauftrag)**
```python
@dataclass
class RetrofitOrder:
    id: RetrofitOrderId
    wagon_id: str  # String-ID aus Train Operations Context
    coupling_positions: List[CouplingPosition]  # Welche Kupplungen umrüsten
    priority: Priority
    status: RetrofitOrderStatus
    created_at: datetime
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]
    completed_at: Optional[datetime]
    assigned_station: Optional[str]  # RetrofitStation-ID
    assigned_worker: Optional[str]   # Worker-ID

    def can_be_started(self) -> bool:
        return (self.status == RetrofitOrderStatus.SCHEDULED and
                self.assigned_station is not None and
                self.assigned_worker is not None)

    def start_retrofit(self, worker_id: str, station_id: str) -> None:
        if not self.can_be_started():
            raise RetrofitOrderCannotBeStartedError()

        self.status = RetrofitOrderStatus.IN_PROGRESS
        self.actual_start = datetime.now()
        self.assigned_worker = worker_id
        self.assigned_station = station_id

        # Domain Event
        DomainEvents.raise_event(RetrofitOrderStartedEvent(
            order_id=self.id.value,
            wagon_id=self.wagon_id,
            worker_id=worker_id,
            station_id=station_id,
            coupling_positions=[pos.value for pos in self.coupling_positions],
            timestamp=datetime.now()
        ))

    def complete_retrofit(self) -> None:
        if self.status != RetrofitOrderStatus.IN_PROGRESS:
            raise RetrofitOrderNotInProgressError()

        self.status = RetrofitOrderStatus.COMPLETED
        self.completed_at = datetime.now()

        # Domain Event
        DomainEvents.raise_event(RetrofitOrderCompletedEvent(
            order_id=self.id.value,
            wagon_id=self.wagon_id,
            worker_id=self.assigned_worker,
            station_id=self.assigned_station,
            coupling_positions=[pos.value for pos in self.coupling_positions],
            duration_minutes=self.get_duration_minutes(),
            timestamp=datetime.now()
        ))

    def get_duration_minutes(self) -> Optional[int]:
        if self.actual_start and self.completed_at:
            return int((self.completed_at - self.actual_start).total_seconds() / 60)
        return None

    def get_estimated_duration(self) -> timedelta:
        # 45 Minuten pro Kupplung
        return timedelta(minutes=45 * len(self.coupling_positions))
```

#### **WorkStep (Arbeitsschritt)**
```python
@dataclass
class WorkStep:
    id: WorkStepId
    order_id: RetrofitOrderId
    coupling_position: CouplingPosition
    step_type: WorkStepType
    status: WorkStepStatus
    estimated_duration: timedelta
    actual_start: Optional[datetime]
    completed_at: Optional[datetime]
    worker_id: Optional[str]
    notes: Optional[str]

    def start_step(self, worker_id: str) -> None:
        if self.status != WorkStepStatus.PENDING:
            raise WorkStepAlreadyStartedError()

        self.status = WorkStepStatus.IN_PROGRESS
        self.actual_start = datetime.now()
        self.worker_id = worker_id

        # Domain Event
        DomainEvents.raise_event(WorkStepStartedEvent(
            step_id=self.id.value,
            order_id=self.order_id.value,
            step_type=self.step_type.value,
            coupling_position=self.coupling_position.value,
            worker_id=worker_id,
            timestamp=datetime.now()
        ))

    def complete_step(self, notes: Optional[str] = None) -> None:
        if self.status != WorkStepStatus.IN_PROGRESS:
            raise WorkStepNotInProgressError()

        self.status = WorkStepStatus.COMPLETED
        self.completed_at = datetime.now()
        self.notes = notes

        # Domain Event
        DomainEvents.raise_event(WorkStepCompletedEvent(
            step_id=self.id.value,
            order_id=self.order_id.value,
            step_type=self.step_type.value,
            coupling_position=self.coupling_position.value,
            worker_id=self.worker_id,
            duration_minutes=self.get_duration_minutes(),
            timestamp=datetime.now()
        ))

    def get_duration_minutes(self) -> Optional[int]:
        if self.actual_start and self.completed_at:
            return int((self.completed_at - self.actual_start).total_seconds() / 60)
        return None
```

### **Value Objects**

#### **RetrofitOrderId**
```python
@dataclass(frozen=True)
class RetrofitOrderId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("RetrofitOrderId cannot be empty")
```

#### **WorkStepId**
```python
@dataclass(frozen=True)
class WorkStepId:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("WorkStepId cannot be empty")
```

### **Enums**

#### **CouplingPosition**
```python
class CouplingPosition(Enum):
    FRONT = "front"
    REAR = "rear"
```

#### **RetrofitOrderStatus**
```python
class RetrofitOrderStatus(Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

#### **WorkStepType**
```python
class WorkStepType(Enum):
    REMOVE_OLD_COUPLING = "remove_old_coupling"
    INSTALL_DAK_COUPLING = "install_dak_coupling"
    TEST_COUPLING = "test_coupling"
    QUALITY_CHECK = "quality_check"
```

#### **WorkStepStatus**
```python
class WorkStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Domain Services

#### **RetrofitPlanningService**
```python
class RetrofitPlanningService:
    def __init__(self,
                 resource_service: ResourceQueryService,
                 topology_service: TopologyQueryService):
        self._resources = resource_service
        self._topology = topology_service

    def schedule_retrofit_order(self, order: RetrofitOrder) -> bool:
        """Plant Umrüstungsauftrag"""
        # 1. Finde verfügbare RetrofitStation
        stations = self._resources.get_available_retrofit_stations()
        if not stations:
            return False

        suitable_station = self._find_suitable_station(stations, order)
        if not suitable_station:
            return False

        # 2. Finde verfügbaren Worker
        workers = self._resources.get_available_workers(["retrofit_operations"])
        if not workers:
            return False

        # 3. Reserviere Ressourcen
        duration = order.get_estimated_duration()

        station_reserved = self._resources.reserve_retrofit_station(
            suitable_station.id,
            duration,
            f"retrofit_order_{order.id.value}"
        )

        if not station_reserved:
            return False

        worker_allocated = self._resources.allocate_worker(
            workers[0].id,
            duration,
            ["retrofit_operations"]
        )

        if not worker_allocated:
            return False

        # 4. Aktualisiere Auftrag
        order.status = RetrofitOrderStatus.SCHEDULED
        order.scheduled_start = datetime.now() + timedelta(minutes=30)
        order.assigned_station = suitable_station.id
        order.assigned_worker = workers[0].id

        # Domain Event
        DomainEvents.raise_event(RetrofitOrderScheduledEvent(
            order_id=order.id.value,
            wagon_id=order.wagon_id,
            station_id=suitable_station.id,
            worker_id=workers[0].id,
            scheduled_start=order.scheduled_start,
            timestamp=datetime.now()
        ))

        return True

    def create_work_steps(self, order: RetrofitOrder) -> List[WorkStep]:
        """Erstellt Arbeitsschritte für Umrüstungsauftrag"""
        work_steps = []

        for position in order.coupling_positions:
            # Standard-Arbeitsschritte für jede Kupplung
            steps = [
                WorkStep(
                    id=WorkStepId(f"{order.id.value}_{position.value}_remove"),
                    order_id=order.id,
                    coupling_position=position,
                    step_type=WorkStepType.REMOVE_OLD_COUPLING,
                    status=WorkStepStatus.PENDING,
                    estimated_duration=timedelta(minutes=15),
                    actual_start=None,
                    completed_at=None,
                    worker_id=None,
                    notes=None
                ),
                WorkStep(
                    id=WorkStepId(f"{order.id.value}_{position.value}_install"),
                    order_id=order.id,
                    coupling_position=position,
                    step_type=WorkStepType.INSTALL_DAK_COUPLING,
                    status=WorkStepStatus.PENDING,
                    estimated_duration=timedelta(minutes=20),
                    actual_start=None,
                    completed_at=None,
                    worker_id=None,
                    notes=None
                ),
                WorkStep(
                    id=WorkStepId(f"{order.id.value}_{position.value}_test"),
                    order_id=order.id,
                    coupling_position=position,
                    step_type=WorkStepType.TEST_COUPLING,
                    status=WorkStepStatus.PENDING,
                    estimated_duration=timedelta(minutes=5),
                    actual_start=None,
                    completed_at=None,
                    worker_id=None,
                    notes=None
                ),
                WorkStep(
                    id=WorkStepId(f"{order.id.value}_{position.value}_check"),
                    order_id=order.id,
                    coupling_position=position,
                    step_type=WorkStepType.QUALITY_CHECK,
                    status=WorkStepStatus.PENDING,
                    estimated_duration=timedelta(minutes=5),
                    actual_start=None,
                    completed_at=None,
                    worker_id=None,
                    notes=None
                )
            ]
            work_steps.extend(steps)

        return work_steps

    def _find_suitable_station(self, stations: List[RetrofitStationInfo],
                             order: RetrofitOrder) -> Optional[RetrofitStationInfo]:
        """Findet geeignete Umrüststation"""
        # Einfache Auswahl: erste verfügbare Station
        return stations[0] if stations else None
```

#### **RetrofitExecutionService**
```python
class RetrofitExecutionService:
    def __init__(self,
                 order_repository: RetrofitOrderRepository,
                 step_repository: WorkStepRepository,
                 train_operations_service: TrainOperationsService):
        self._orders = order_repository
        self._steps = step_repository
        self._train_ops = train_operations_service

    def execute_retrofit_order(self, order_id: RetrofitOrderId) -> bool:
        """Führt Umrüstungsauftrag aus"""
        order = self._orders.get_by_id(order_id)

        if not order.can_be_started():
            return False

        # 1. Starte Auftrag
        order.start_retrofit(order.assigned_worker, order.assigned_station)
        self._orders.save(order)

        # 2. Hole Arbeitsschritte
        work_steps = self._steps.find_by_order_id(order_id)

        # 3. Führe Arbeitsschritte sequenziell aus
        for step in work_steps:
            success = self._execute_work_step(step, order.assigned_worker)
            if not success:
                return False

        # 4. Schließe Auftrag ab
        order.complete_retrofit()
        self._orders.save(order)

        # 5. Benachrichtige Train Operations über Fertigstellung
        self._notify_train_operations(order)

        return True

    def _execute_work_step(self, step: WorkStep, worker_id: str) -> bool:
        """Führt einzelnen Arbeitsschritt aus"""
        try:
            step.start_step(worker_id)
            self._steps.save(step)

            # Simuliere Arbeitszeit
            time.sleep(1)  # Für Demo - in Realität würde hier gewartet

            step.complete_step()
            self._steps.save(step)

            return True

        except Exception:
            return False

    def _notify_train_operations(self, order: RetrofitOrder) -> None:
        """Benachrichtigt Train Operations über fertige Umrüstung"""
        # Domain Event für andere Contexts
        DomainEvents.raise_event(WagonRetrofitFinishedEvent(
            wagon_id=order.wagon_id,
            coupling_positions=[pos.value for pos in order.coupling_positions],
            completed_at=order.completed_at,
            timestamp=datetime.now()
        ))
```

## Domain Events

#### **Retrofit Order Events**
```python
@dataclass(frozen=True)
class RetrofitOrderCreatedEvent:
    order_id: str
    wagon_id: str
    coupling_positions: List[str]
    priority: int
    timestamp: datetime

@dataclass(frozen=True)
class RetrofitOrderScheduledEvent:
    order_id: str
    wagon_id: str
    station_id: str
    worker_id: str
    scheduled_start: datetime
    timestamp: datetime

@dataclass(frozen=True)
class RetrofitOrderStartedEvent:
    order_id: str
    wagon_id: str
    worker_id: str
    station_id: str
    coupling_positions: List[str]
    timestamp: datetime

@dataclass(frozen=True)
class RetrofitOrderCompletedEvent:
    order_id: str
    wagon_id: str
    worker_id: str
    station_id: str
    coupling_positions: List[str]
    duration_minutes: int
    timestamp: datetime
```

#### **Work Step Events**
```python
@dataclass(frozen=True)
class WorkStepStartedEvent:
    step_id: str
    order_id: str
    step_type: str
    coupling_position: str
    worker_id: str
    timestamp: datetime

@dataclass(frozen=True)
class WorkStepCompletedEvent:
    step_id: str
    order_id: str
    step_type: str
    coupling_position: str
    worker_id: str
    duration_minutes: int
    timestamp: datetime
```

#### **Integration Events**
```python
@dataclass(frozen=True)
class WagonRetrofitFinishedEvent:
    """Event für Train Operations Context"""
    wagon_id: str
    coupling_positions: List[str]
    completed_at: datetime
    timestamp: datetime
```

## Data Transfer Objects (DTOs)

#### **RetrofitOrderInfo**
```python
@dataclass(frozen=True)
class RetrofitOrderInfo:
    """DTO für andere Contexts"""
    id: str
    wagon_id: str
    coupling_positions: List[str]
    priority: int
    status: str
    created_at: datetime
    scheduled_start: Optional[datetime]
    estimated_completion: Optional[datetime]
    assigned_station: Optional[str]
    assigned_worker: Optional[str]
```

#### **WorkStepInfo**
```python
@dataclass(frozen=True)
class WorkStepInfo:
    """DTO für Monitoring"""
    id: str
    order_id: str
    step_type: str
    coupling_position: str
    status: str
    estimated_duration_minutes: int
    actual_duration_minutes: Optional[int]
    worker_id: Optional[str]
```

## Application Services

#### **WorkshopService**
```python
class WorkshopService:
    """Öffentliche API für andere Contexts"""

    def __init__(self,
                 planning_service: RetrofitPlanningService,
                 execution_service: RetrofitExecutionService,
                 order_repository: RetrofitOrderRepository):
        self._planning = planning_service
        self._execution = execution_service
        self._orders = order_repository

    def create_retrofit_order(self, wagon_id: str, coupling_positions: List[str],
                            priority: int) -> str:
        """Erstellt neuen Umrüstungsauftrag"""
        order_id = RetrofitOrderId(f"retrofit_{wagon_id}_{int(datetime.now().timestamp())}")

        positions = [CouplingPosition(pos) for pos in coupling_positions]

        order = RetrofitOrder(
            id=order_id,
            wagon_id=wagon_id,
            coupling_positions=positions,
            priority=Priority(priority),
            status=RetrofitOrderStatus.CREATED,
            created_at=datetime.now(),
            scheduled_start=None,
            actual_start=None,
            completed_at=None,
            assigned_station=None,
            assigned_worker=None
        )

        self._orders.save(order)

        # Domain Event
        DomainEvents.raise_event(RetrofitOrderCreatedEvent(
            order_id=order_id.value,
            wagon_id=wagon_id,
            coupling_positions=coupling_positions,
            priority=priority,
            timestamp=datetime.now()
        ))

        # Versuche sofort zu planen
        self._planning.schedule_retrofit_order(order)
        self._orders.save(order)

        return order_id.value

    def get_pending_orders(self) -> List[RetrofitOrderInfo]:
        """Holt wartende Umrüstungsaufträge"""
        orders = self._orders.find_by_status(RetrofitOrderStatus.CREATED)
        return [self._to_order_info(order) for order in orders]

    def get_order_status(self, order_id: str) -> Optional[RetrofitOrderInfo]:
        """Holt Status eines Umrüstungsauftrags"""
        try:
            order = self._orders.get_by_id(RetrofitOrderId(order_id))
            return self._to_order_info(order)
        except:
            return None

    def _to_order_info(self, order: RetrofitOrder) -> RetrofitOrderInfo:
        """Konvertierung zu DTO"""
        estimated_completion = None
        if order.scheduled_start:
            estimated_completion = order.scheduled_start + order.get_estimated_duration()

        return RetrofitOrderInfo(
            id=order.id.value,
            wagon_id=order.wagon_id,
            coupling_positions=[pos.value for pos in order.coupling_positions],
            priority=order.priority.value,
            status=order.status.value,
            created_at=order.created_at,
            scheduled_start=order.scheduled_start,
            estimated_completion=estimated_completion,
            assigned_station=order.assigned_station,
            assigned_worker=order.assigned_worker
        )
```

## Integration mit anderen Contexts

### **Customer von Train Operations Context:**
- Empfängt `WagonInfo` DTOs
- Reagiert auf `WagonRetrofitStartedEvent`
- Keine geteilten Domain-Entitäten

### **Customer von Resource Management Context:**
- Nutzt `ResourceQueryService` für Stationen und Worker
- Empfängt `RetrofitStationInfo`, `WorkerInfo` DTOs
- Reserviert Ressourcen über Service

### **Supplier für Train Operations Context:**
- Sendet `WagonRetrofitFinishedEvent`
- Stellt `RetrofitOrderInfo` DTOs bereit

### **Customer von Infrastructure Context:**
- Nutzt `TopologyQueryService` für Standortabfragen
- Empfängt `TrackInfo` DTOs

## Event Handler

#### **WagonRetrofitRequestHandler**
```python
class WagonRetrofitRequestHandler:
    """Reagiert auf Umrüstungsanfragen aus Train Operations"""

    def __init__(self, workshop_service: WorkshopService):
        self._workshop = workshop_service

    def handle_wagon_retrofit_started(self, event: WagonRetrofitStartedEvent) -> None:
        """Erstellt Umrüstungsauftrag basierend auf Train Operations Event"""
        coupling_positions = [event.coupling_position]

        order_id = self._workshop.create_retrofit_order(
            wagon_id=event.wagon_id,
            coupling_positions=coupling_positions,
            priority=5  # Standard-Priorität
        )

        print(f"Retrofit order {order_id} created for wagon {event.wagon_id}")
```

## Nächste Schritte

1. **Repository-Implementierungen** für RetrofitOrder und WorkStep
2. **Event Handler** für Integration mit Train Operations
3. **Rules Engine Integration** für Prioritätsvergabe
4. **Monitoring Dashboard** für Umrüstungsfortschritt

Sollen wir als nächstes den **Rules Engine Context** ausarbeiten?
