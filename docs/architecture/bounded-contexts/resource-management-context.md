# Resource Management Context - Detailed Design

## Übersicht

Der Resource Management Context verwaltet alle Betriebsmittel der Simulation: Lokomotiven, Personal, Umrüststationen und deren Verfügbarkeiten. Er stellt Ressourcen-Pools bereit und koordiniert Allokationen zwischen den anderen Contexts.

## Domain Model

### **Entities**

#### **Locomotive**
```python
@dataclass
class Locomotive:
    id: LocomotiveId
    name: str
    max_pulling_capacity: Weight
    current_location: Optional[TrackId]
    status: LocomotiveStatus
    home_track: TrackId
    maintenance_schedule: MaintenanceSchedule
    current_assignment: Optional[AssignmentId]
    
    def is_available(self) -> bool:
        return self.status == LocomotiveStatus.AVAILABLE
    
    def can_handle_load(self, required_capacity: Weight) -> bool:
        return self.max_pulling_capacity >= required_capacity
    
    def assign_to_operation(self, assignment_id: AssignmentId, operation_type: str) -> None:
        if not self.is_available():
            raise LocomotiveNotAvailableError()
        
        self.current_assignment = assignment_id
        self.status = LocomotiveStatus.ASSIGNED
        
        # Domain Event
        DomainEvents.raise_event(LocomotiveAssignedEvent(
            locomotive_id=self.id.value,
            assignment_id=assignment_id.value,
            operation_type=operation_type,
            timestamp=datetime.now()
        ))
    
    def complete_assignment(self) -> None:
        if self.status != LocomotiveStatus.ASSIGNED:
            raise LocomotiveNotAssignedError()
        
        assignment_id = self.current_assignment
        self.current_assignment = None
        self.status = LocomotiveStatus.AVAILABLE
        
        # Domain Event
        DomainEvents.raise_event(LocomotiveReleasedEvent(
            locomotive_id=self.id.value,
            assignment_id=assignment_id.value if assignment_id else None,
            timestamp=datetime.now()
        ))
    
    def send_to_maintenance(self) -> None:
        if self.status == LocomotiveStatus.ASSIGNED:
            raise LocomotiveInUseError()
        
        self.status = LocomotiveStatus.IN_MAINTENANCE
        
        # Domain Event
        DomainEvents.raise_event(LocomotiveMaintenanceStartedEvent(
            locomotive_id=self.id.value,
            scheduled_return=self.maintenance_schedule.next_maintenance_end,
            timestamp=datetime.now()
        ))
```

#### **Worker**
```python
@dataclass
class Worker:
    id: WorkerId
    name: str
    skills: List[Skill]
    shift_schedule: ShiftSchedule
    current_location: Optional[TrackId]
    status: WorkerStatus
    current_assignment: Optional[AssignmentId]
    
    def is_available(self) -> bool:
        return (self.status == WorkerStatus.AVAILABLE and 
                self.shift_schedule.is_currently_working())
    
    def has_skill(self, required_skill: Skill) -> bool:
        return required_skill in self.skills
    
    def can_perform_operation(self, required_skills: List[Skill]) -> bool:
        return any(self.has_skill(skill) for skill in required_skills)
    
    def assign_to_operation(self, assignment_id: AssignmentId, operation_type: str) -> None:
        if not self.is_available():
            raise WorkerNotAvailableError()
        
        self.current_assignment = assignment_id
        self.status = WorkerStatus.ASSIGNED
        
        # Domain Event
        DomainEvents.raise_event(WorkerAssignedEvent(
            worker_id=self.id.value,
            assignment_id=assignment_id.value,
            operation_type=operation_type,
            skills_used=[skill.value for skill in self.skills],
            timestamp=datetime.now()
        ))
    
    def complete_assignment(self) -> None:
        if self.status != WorkerStatus.ASSIGNED:
            raise WorkerNotAssignedError()
        
        assignment_id = self.current_assignment
        self.current_assignment = None
        self.status = WorkerStatus.AVAILABLE
        
        # Domain Event
        DomainEvents.raise_event(WorkerReleasedEvent(
            worker_id=self.id.value,
            assignment_id=assignment_id.value if assignment_id else None,
            timestamp=datetime.now()
        ))
    
    def start_break(self, break_duration: timedelta) -> None:
        if self.status == WorkerStatus.ASSIGNED:
            raise WorkerInUseError()
        
        self.status = WorkerStatus.ON_BREAK
        
        # Domain Event
        DomainEvents.raise_event(WorkerBreakStartedEvent(
            worker_id=self.id.value,
            break_duration_minutes=int(break_duration.total_seconds() / 60),
            timestamp=datetime.now()
        ))
```

#### **RetrofitStation**
```python
@dataclass
class RetrofitStation:
    id: RetrofitStationId
    name: str
    location: TrackId
    capacity: int  # Anzahl gleichzeitiger Umrüstungen
    supported_operations: List[RetrofitOperationType]
    status: StationStatus
    current_occupancy: int
    assigned_workers: List[WorkerId]
    
    def is_available(self) -> bool:
        return (self.status == StationStatus.OPERATIONAL and 
                self.current_occupancy < self.capacity)
    
    def can_perform_operation(self, operation_type: RetrofitOperationType) -> bool:
        return operation_type in self.supported_operations
    
    def reserve_slot(self, assignment_id: AssignmentId) -> None:
        if not self.is_available():
            raise StationNotAvailableError()
        
        self.current_occupancy += 1
        
        # Domain Event
        DomainEvents.raise_event(RetrofitStationReservedEvent(
            station_id=self.id.value,
            assignment_id=assignment_id.value,
            current_occupancy=self.current_occupancy,
            timestamp=datetime.now()
        ))
    
    def release_slot(self, assignment_id: AssignmentId) -> None:
        if self.current_occupancy <= 0:
            raise StationNotOccupiedError()
        
        self.current_occupancy -= 1
        
        # Domain Event
        DomainEvents.raise_event(RetrofitStationReleasedEvent(
            station_id=self.id.value,
            assignment_id=assignment_id.value,
            current_occupancy=self.current_occupancy,
            timestamp=datetime.now()
        ))
    
    def assign_worker(self, worker_id: WorkerId) -> None:
        if worker_id not in self.assigned_workers:
            self.assigned_workers.append(worker_id)
    
    def remove_worker(self, worker_id: WorkerId) -> None:
        if worker_id in self.assigned_workers:
            self.assigned_workers.remove(worker_id)
```

#### **ResourceAssignment**
```python
@dataclass
class ResourceAssignment:
    id: AssignmentId
    resource_type: ResourceType
    resource_id: str  # LocomotiveId, WorkerId, oder StationId
    operation_id: str
    operation_type: str
    assigned_at: datetime
    scheduled_release: Optional[datetime]
    actual_release: Optional[datetime]
    status: AssignmentStatus
    
    def complete_assignment(self) -> None:
        if self.status != AssignmentStatus.ACTIVE:
            raise AssignmentNotActiveError()
        
        self.status = AssignmentStatus.COMPLETED
        self.actual_release = datetime.now()
        
        # Domain Event
        DomainEvents.raise_event(ResourceAssignmentCompletedEvent(
            assignment_id=self.id.value,
            resource_type=self.resource_type.value,
            resource_id=self.resource_id,
            operation_id=self.operation_id,
            duration_minutes=self.get_actual_duration_minutes(),
            timestamp=self.actual_release
        ))
    
    def get_actual_duration_minutes(self) -> Optional[int]:
        if self.assigned_at and self.actual_release:
            return int((self.actual_release - self.assigned_at).total_seconds() / 60)
        return None
```

### **Value Objects**

#### **IDs und Basic Types**
```python
@dataclass(frozen=True)
class LocomotiveId:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("LocomotiveId cannot be empty")

@dataclass(frozen=True)
class WorkerId:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("WorkerId cannot be empty")

@dataclass(frozen=True)
class RetrofitStationId:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("RetrofitStationId cannot be empty")

@dataclass(frozen=True)
class AssignmentId:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("AssignmentId cannot be empty")
```

#### **Schedules und Capacity**
```python
@dataclass(frozen=True)
class ShiftSchedule:
    start_time: time
    end_time: time
    break_times: List[Tuple[time, timedelta]]  # (start_time, duration)
    
    def is_currently_working(self, current_time: Optional[datetime] = None) -> bool:
        if not current_time:
            current_time = datetime.now()
        
        current_time_only = current_time.time()
        
        # Prüfe ob in Arbeitszeit
        if not (self.start_time <= current_time_only <= self.end_time):
            return False
        
        # Prüfe ob in Pause
        for break_start, break_duration in self.break_times:
            break_end = (datetime.combine(datetime.today(), break_start) + break_duration).time()
            if break_start <= current_time_only <= break_end:
                return False
        
        return True

@dataclass(frozen=True)
class MaintenanceSchedule:
    next_maintenance_start: datetime
    next_maintenance_end: datetime
    maintenance_interval_days: int
    
    def is_due_for_maintenance(self, current_time: Optional[datetime] = None) -> bool:
        if not current_time:
            current_time = datetime.now()
        return current_time >= self.next_maintenance_start
```

#### **Enums**
```python
class LocomotiveStatus(Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_MAINTENANCE = "in_maintenance"
    OUT_OF_SERVICE = "out_of_service"

class WorkerStatus(Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_BREAK = "on_break"
    OFF_SHIFT = "off_shift"
    SICK_LEAVE = "sick_leave"

class StationStatus(Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"

class Skill(Enum):
    DAK_RETROFIT = "dak_retrofit"
    SHUNTING_OPERATIONS = "shunting_operations"
    WAGON_INSPECTION = "wagon_inspection"
    BRAKE_TESTING = "brake_testing"
    COUPLING_OPERATIONS = "coupling_operations"

class ResourceType(Enum):
    LOCOMOTIVE = "locomotive"
    WORKER = "worker"
    RETROFIT_STATION = "retrofit_station"

class RetrofitOperationType(Enum):
    SCHRAUBKUPPLUNG_TO_DAK = "schraubkupplung_to_dak"
    DAK_MAINTENANCE = "dak_maintenance"
    COUPLING_INSPECTION = "coupling_inspection"

class AssignmentStatus(Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

## Domain Services

#### **ResourceAllocationService**
```python
class ResourceAllocationService:
    def __init__(self,
                 locomotive_repository: LocomotiveRepository,
                 worker_repository: WorkerRepository,
                 station_repository: RetrofitStationRepository,
                 assignment_repository: ResourceAssignmentRepository):
        self._locomotives = locomotive_repository
        self._workers = worker_repository
        self._stations = station_repository
        self._assignments = assignment_repository
    
    def allocate_locomotive(self, 
                          required_capacity: Weight, 
                          operation_id: str,
                          operation_type: str) -> Optional[LocomotiveAllocation]:
        # 1. Finde verfügbare Lokomotiven
        available_locomotives = self._locomotives.find_available()
        
        # 2. Filtere nach Kapazität
        suitable_locomotives = [
            loco for loco in available_locomotives 
            if loco.can_handle_load(required_capacity)
        ]
        
        if not suitable_locomotives:
            return None
        
        # 3. Wähle beste Lokomotive (kleinste ausreichende Kapazität)
        best_locomotive = min(suitable_locomotives, 
                            key=lambda l: l.max_pulling_capacity.tonnes)
        
        # 4. Erstelle Assignment
        assignment = ResourceAssignment(
            id=AssignmentId(f"loco_assign_{int(datetime.now().timestamp())}"),
            resource_type=ResourceType.LOCOMOTIVE,
            resource_id=best_locomotive.id.value,
            operation_id=operation_id,
            operation_type=operation_type,
            assigned_at=datetime.now(),
            scheduled_release=None,
            actual_release=None,
            status=AssignmentStatus.ACTIVE
        )
        
        # 5. Reserviere Lokomotive
        best_locomotive.assign_to_operation(assignment.id, operation_type)
        
        # 6. Speichere Assignment
        self._assignments.save(assignment)
        self._locomotives.save(best_locomotive)
        
        return LocomotiveAllocation(
            locomotive_id=best_locomotive.id.value,
            assignment_id=assignment.id.value,
            max_capacity=best_locomotive.max_pulling_capacity.tonnes
        )
    
    def allocate_worker(self, 
                       required_skills: List[Skill],
                       operation_id: str,
                       operation_type: str) -> Optional[WorkerAllocation]:
        # 1. Finde verfügbare Arbeiter
        available_workers = self._workers.find_available()
        
        # 2. Filtere nach Skills
        suitable_workers = [
            worker for worker in available_workers
            if worker.can_perform_operation(required_skills)
        ]
        
        if not suitable_workers:
            return None
        
        # 3. Wähle ersten verfügbaren Arbeiter
        selected_worker = suitable_workers[0]
        
        # 4. Erstelle Assignment
        assignment = ResourceAssignment(
            id=AssignmentId(f"worker_assign_{int(datetime.now().timestamp())}"),
            resource_type=ResourceType.WORKER,
            resource_id=selected_worker.id.value,
            operation_id=operation_id,
            operation_type=operation_type,
            assigned_at=datetime.now(),
            scheduled_release=None,
            actual_release=None,
            status=AssignmentStatus.ACTIVE
        )
        
        # 5. Reserviere Arbeiter
        selected_worker.assign_to_operation(assignment.id, operation_type)
        
        # 6. Speichere Assignment
        self._assignments.save(assignment)
        self._workers.save(selected_worker)
        
        return WorkerAllocation(
            worker_id=selected_worker.id.value,
            assignment_id=assignment.id.value,
            skills=[skill.value for skill in selected_worker.skills]
        )
    
    def allocate_retrofit_station(self,
                                operation_type: RetrofitOperationType,
                                operation_id: str) -> Optional[StationAllocation]:
        # 1. Finde verfügbare Stationen
        available_stations = self._stations.find_available()
        
        # 2. Filtere nach unterstützten Operationen
        suitable_stations = [
            station for station in available_stations
            if station.can_perform_operation(operation_type)
        ]
        
        if not suitable_stations:
            return None
        
        # 3. Wähle Station mit geringster Auslastung
        best_station = min(suitable_stations,
                         key=lambda s: s.current_occupancy / s.capacity)
        
        # 4. Erstelle Assignment
        assignment = ResourceAssignment(
            id=AssignmentId(f"station_assign_{int(datetime.now().timestamp())}"),
            resource_type=ResourceType.RETROFIT_STATION,
            resource_id=best_station.id.value,
            operation_id=operation_id,
            operation_type=operation_type.value,
            assigned_at=datetime.now(),
            scheduled_release=None,
            actual_release=None,
            status=AssignmentStatus.ACTIVE
        )
        
        # 5. Reserviere Station
        best_station.reserve_slot(assignment.id)
        
        # 6. Speichere Assignment
        self._assignments.save(assignment)
        self._stations.save(best_station)
        
        return StationAllocation(
            station_id=best_station.id.value,
            assignment_id=assignment.id.value,
            location=best_station.location.value
        )
```

#### **ResourceReleaseService**
```python
class ResourceReleaseService:
    def __init__(self,
                 locomotive_repository: LocomotiveRepository,
                 worker_repository: WorkerRepository,
                 station_repository: RetrofitStationRepository,
                 assignment_repository: ResourceAssignmentRepository):
        self._locomotives = locomotive_repository
        self._workers = worker_repository
        self._stations = station_repository
        self._assignments = assignment_repository
    
    def release_resources(self, operation_id: str) -> None:
        """Gibt alle Ressourcen einer Operation frei"""
        assignments = self._assignments.find_by_operation_id(operation_id)
        
        for assignment in assignments:
            if assignment.status == AssignmentStatus.ACTIVE:
                self._release_single_resource(assignment)
    
    def _release_single_resource(self, assignment: ResourceAssignment) -> None:
        if assignment.resource_type == ResourceType.LOCOMOTIVE:
            locomotive = self._locomotives.get_by_id(LocomotiveId(assignment.resource_id))
            locomotive.complete_assignment()
            self._locomotives.save(locomotive)
            
        elif assignment.resource_type == ResourceType.WORKER:
            worker = self._workers.get_by_id(WorkerId(assignment.resource_id))
            worker.complete_assignment()
            self._workers.save(worker)
            
        elif assignment.resource_type == ResourceType.RETROFIT_STATION:
            station = self._stations.get_by_id(RetrofitStationId(assignment.resource_id))
            station.release_slot(assignment.id)
            self._stations.save(station)
        
        # Assignment als abgeschlossen markieren
        assignment.complete_assignment()
        self._assignments.save(assignment)
```

## Domain Events

#### **Resource Events**
```python
@dataclass(frozen=True)
class LocomotiveAssignedEvent:
    locomotive_id: str
    assignment_id: str
    operation_type: str
    timestamp: datetime

@dataclass(frozen=True)
class LocomotiveReleasedEvent:
    locomotive_id: str
    assignment_id: Optional[str]
    timestamp: datetime

@dataclass(frozen=True)
class WorkerAssignedEvent:
    worker_id: str
    assignment_id: str
    operation_type: str
    skills_used: List[str]
    timestamp: datetime

@dataclass(frozen=True)
class WorkerReleasedEvent:
    worker_id: str
    assignment_id: Optional[str]
    timestamp: datetime

@dataclass(frozen=True)
class RetrofitStationReservedEvent:
    station_id: str
    assignment_id: str
    current_occupancy: int
    timestamp: datetime

@dataclass(frozen=True)
class RetrofitStationReleasedEvent:
    station_id: str
    assignment_id: str
    current_occupancy: int
    timestamp: datetime

@dataclass(frozen=True)
class ResourceAssignmentCompletedEvent:
    assignment_id: str
    resource_type: str
    resource_id: str
    operation_id: str
    duration_minutes: int
    timestamp: datetime
```

## Application Services

#### **ResourceManagementService**
```python
class ResourceManagementService:
    """Öffentliche API für Resource Management Context"""
    
    def __init__(self,
                 allocation_service: ResourceAllocationService,
                 release_service: ResourceReleaseService,
                 locomotive_repository: LocomotiveRepository,
                 worker_repository: WorkerRepository,
                 station_repository: RetrofitStationRepository):
        self._allocation = allocation_service
        self._release = release_service
        self._locomotives = locomotive_repository
        self._workers = worker_repository
        self._stations = station_repository
    
    def find_available_locomotive(self, min_capacity: float) -> Optional[LocomotiveInfo]:
        """Findet verfügbare Lokomotive"""
        locomotives = self._locomotives.find_available()
        suitable = [l for l in locomotives if l.max_pulling_capacity.tonnes >= min_capacity]
        
        if suitable:
            best = min(suitable, key=lambda l: l.max_pulling_capacity.tonnes)
            return LocomotiveInfo(
                id=best.id.value,
                name=best.name,
                max_capacity=best.max_pulling_capacity.tonnes,
                current_location=best.current_location.value if best.current_location else None,
                status=best.status.value
            )
        return None
    
    def find_available_worker(self, required_skills: List[str]) -> Optional[WorkerInfo]:
        """Findet verfügbaren Arbeiter"""
        workers = self._workers.find_available()
        skills_enum = [Skill(skill) for skill in required_skills]
        suitable = [w for w in workers if w.can_perform_operation(skills_enum)]
        
        if suitable:
            worker = suitable[0]
            return WorkerInfo(
                id=worker.id.value,
                name=worker.name,
                skills=[skill.value for skill in worker.skills],
                current_location=worker.current_location.value if worker.current_location else None,
                status=worker.status.value
            )
        return None
    
    def find_available_retrofit_station(self, operation_type: str) -> Optional[RetrofitStationInfo]:
        """Findet verfügbare Umrüststation"""
        stations = self._stations.find_available()
        operation_enum = RetrofitOperationType(operation_type)
        suitable = [s for s in stations if s.can_perform_operation(operation_enum)]
        
        if suitable:
            station = min(suitable, key=lambda s: s.current_occupancy / s.capacity)
            return RetrofitStationInfo(
                id=station.id.value,
                name=station.name,
                location=station.location.value,
                capacity=station.capacity,
                current_occupancy=station.current_occupancy,
                utilization=station.current_occupancy / station.capacity,
                supported_operations=[op.value for op in station.supported_operations]
            )
        return None
    
    def allocate_resources_for_shunting(self, 
                                      required_capacity: float,
                                      operation_id: str) -> Optional[ShuntingResourceAllocation]:
        """Allokiert Ressourcen für Rangieroperation"""
        
        # 1. Allokiere Lokomotive
        locomotive_allocation = self._allocation.allocate_locomotive(
            Weight(required_capacity),
            operation_id,
            "shunting_operation"
        )
        
        if not locomotive_allocation:
            return None
        
        # 2. Allokiere Rangierbegleiter
        worker_allocation = self._allocation.allocate_worker(
            [Skill.SHUNTING_OPERATIONS],
            operation_id,
            "shunting_operation"
        )
        
        if not worker_allocation:
            # Rollback Lokomotive
            self._release.release_resources(operation_id)
            return None
        
        return ShuntingResourceAllocation(
            locomotive_id=locomotive_allocation.locomotive_id,
            locomotive_assignment_id=locomotive_allocation.assignment_id,
            worker_id=worker_allocation.worker_id,
            worker_assignment_id=worker_allocation.assignment_id
        )
    
    def allocate_resources_for_retrofit(self,
                                      operation_type: str,
                                      operation_id: str) -> Optional[RetrofitResourceAllocation]:
        """Allokiert Ressourcen für Umrüstung"""
        
        # 1. Allokiere Umrüststation
        station_allocation = self._allocation.allocate_retrofit_station(
            RetrofitOperationType(operation_type),
            operation_id
        )
        
        if not station_allocation:
            return None
        
        # 2. Allokiere Werkstattarbeiter
        worker_allocation = self._allocation.allocate_worker(
            [Skill.DAK_RETROFIT],
            operation_id,
            "retrofit_operation"
        )
        
        if not worker_allocation:
            # Rollback Station
            self._release.release_resources(operation_id)
            return None
        
        return RetrofitResourceAllocation(
            station_id=station_allocation.station_id,
            station_assignment_id=station_allocation.assignment_id,
            worker_id=worker_allocation.worker_id,
            worker_assignment_id=worker_allocation.assignment_id,
            location=station_allocation.location
        )
    
    def release_operation_resources(self, operation_id: str) -> None:
        """Gibt alle Ressourcen einer Operation frei"""
        self._release.release_resources(operation_id)
    
    def get_resource_utilization(self) -> ResourceUtilizationInfo:
        """Holt aktuelle Ressourcenauslastung"""
        all_locomotives = self._locomotives.find_all()
        all_workers = self._workers.find_all()
        all_stations = self._stations.find_all()
        
        locomotive_utilization = len([l for l in all_locomotives if not l.is_available()]) / len(all_locomotives)
        worker_utilization = len([w for w in all_workers if not w.is_available()]) / len(all_workers)
        station_utilization = sum(s.current_occupancy for s in all_stations) / sum(s.capacity for s in all_stations)
        
        return ResourceUtilizationInfo(
            locomotive_utilization=locomotive_utilization,
            worker_utilization=worker_utilization,
            station_utilization=station_utilization,
            total_locomotives=len(all_locomotives),
            total_workers=len(all_workers),
            total_stations=len(all_stations)
        )
```

## Data Transfer Objects (DTOs)

#### **Resource Info DTOs**
```python
@dataclass(frozen=True)
class LocomotiveInfo:
    id: str
    name: str
    max_capacity: float
    current_location: Optional[str]
    status: str

@dataclass(frozen=True)
class WorkerInfo:
    id: str
    name: str
    skills: List[str]
    current_location: Optional[str]
    status: str

@dataclass(frozen=True)
class RetrofitStationInfo:
    id: str
    name: str
    location: str
    capacity: int
    current_occupancy: int
    utilization: float
    supported_operations: List[str]

@dataclass(frozen=True)
class ResourceUtilizationInfo:
    locomotive_utilization: float
    worker_utilization: float
    station_utilization: float
    total_locomotives: int
    total_workers: int
    total_stations: int
```

#### **Allocation DTOs**
```python
@dataclass(frozen=True)
class LocomotiveAllocation:
    locomotive_id: str
    assignment_id: str
    max_capacity: float

@dataclass(frozen=True)
class WorkerAllocation:
    worker_id: str
    assignment_id: str
    skills: List[str]

@dataclass(frozen=True)
class StationAllocation:
    station_id: str
    assignment_id: str
    location: str

@dataclass(frozen=True)
class ShuntingResourceAllocation:
    locomotive_id: str
    locomotive_assignment_id: str
    worker_id: str
    worker_assignment_id: str

@dataclass(frozen=True)
class RetrofitResourceAllocation:
    station_id: str
    station_assignment_id: str
    worker_id: str
    worker_assignment_id: str
    location: str
```

## SimPy Integration

### **Resource Pool Implementation**
```python
class SimPyResourcePools:
    def __init__(self, env: simpy.Environment, resource_service: ResourceManagementService):
        self.env = env
        self.resource_service = resource_service
        
        # SimPy Resource Pools
        self.locomotive_pool = simpy.FilterStore(env)
        self.worker_pools = {}  # skill -> FilterStore
        self.station_pools = {}  # operation_type -> Resource
        
        self._initialize_pools()
    
    def _initialize_pools(self):
        # Lade alle Ressourcen und fülle Pools
        locomotives = self.resource_service._locomotives.find_all()
        for loco in locomotives:
            if loco.is_available():
                self.locomotive_pool.put(loco.id.value)
        
        # Worker Pools nach Skills
        for skill in Skill:
            self.worker_pools[skill.value] = simpy.FilterStore(self.env)
            
        workers = self.resource_service._workers.find_all()
        for worker in workers:
            if worker.is_available():
                for skill in worker.skills:
                    self.worker_pools[skill.value].put(worker.id.value)
        
        # Station Pools
        stations = self.resource_service._stations.find_all()
        for station in stations:
            for operation_type in station.supported_operations:
                if operation_type.value not in self.station_pools:
                    self.station_pools[operation_type.value] = simpy.Resource(
                        self.env, 
                        capacity=sum(s.capacity for s in stations if operation_type in s.supported_operations)
                    )
```

## Repository Interfaces

#### **Resource Repositories**
```python
class LocomotiveRepository(ABC):
    @abstractmethod
    def get_by_id(self, locomotive_id: LocomotiveId) -> Locomotive:
        pass
    
    @abstractmethod
    def find_available(self) -> List[Locomotive]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[Locomotive]:
        pass
    
    @abstractmethod
    def save(self, locomotive: Locomotive) -> None:
        pass

class WorkerRepository(ABC):
    @abstractmethod
    def get_by_id(self, worker_id: WorkerId) -> Worker:
        pass
    
    @abstractmethod
    def find_available(self) -> List[Worker]:
        pass
    
    @abstractmethod
    def find_by_skill(self, skill: Skill) -> List[Worker]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[Worker]:
        pass
    
    @abstractmethod
    def save(self, worker: Worker) -> None:
        pass

class RetrofitStationRepository(ABC):
    @abstractmethod
    def get_by_id(self, station_id: RetrofitStationId) -> RetrofitStation:
        pass
    
    @abstractmethod
    def find_available(self) -> List[RetrofitStation]:
        pass
    
    @abstractmethod
    def find_by_operation_type(self, operation_type: RetrofitOperationType) -> List[RetrofitStation]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[RetrofitStation]:
        pass
    
    @abstractmethod
    def save(self, station: RetrofitStation) -> None:
        pass

class ResourceAssignmentRepository(ABC):
    @abstractmethod
    def get_by_id(self, assignment_id: AssignmentId) -> ResourceAssignment:
        pass
    
    @abstractmethod
    def find_by_operation_id(self, operation_id: str) -> List[ResourceAssignment]:
        pass
    
    @abstractmethod
    def find_active_assignments(self) -> List[ResourceAssignment]:
        pass
    
    @abstractmethod
    def save(self, assignment: ResourceAssignment) -> None:
        pass
```

## Integration mit anderen Contexts (Monolith)

### **Supplier für Train Operations Context**
```python
# Direkte Service-Aufrufe (Dependency Injection)
class TrainOperationsService:
    def __init__(self, resource_service: ResourceManagementService):
        self._resource_service = resource_service
    
    def schedule_shunting(self):
        locomotive = self._resource_service.find_available_locomotive(min_capacity=80.0)
        allocation = self._resource_service.allocate_resources_for_shunting(
            required_capacity=100.0, operation_id="shunt_001"
        )
```

### **Supplier für Workshop Context**
```python
# Direkte Service-Aufrufe
class WorkshopService:
    def __init__(self, resource_service: ResourceManagementService):
        self._resource_service = resource_service
    
    def start_retrofit(self):
        station = self._resource_service.find_available_retrofit_station("schraubkupplung_to_dak")
        allocation = self._resource_service.allocate_resources_for_retrofit(
            "schraubkupplung_to_dak", "retrofit_001"
        )
```

### **Customer von Infrastructure Context**
```python
# Dependency Injection für Infrastructure Service
class ResourceManagementService:
    def __init__(self, infrastructure_service: InfrastructureQueryService):
        self._infrastructure_service = infrastructure_service
    
    def update_locomotive_location(self, locomotive_id: str):
        track_info = self._infrastructure_service.get_track_info(locomotive.current_location)
```

## Nächste Schritte

1. **Repository Implementierungen** für alle Resource-Typen
2. **SimPy Resource Pool Integration** mit Domain Model
3. **Shift Management** für Arbeiter-Schichten
4. **Maintenance Scheduling** für Lokomotiven

**Resource Management Context ist jetzt vollständig definiert.**