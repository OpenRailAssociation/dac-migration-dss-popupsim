# Simulation Control Context - Detailed Design

## Übersicht

Der Simulation Control Context steuert den Simulationslauf, verwaltet Zeit, Szenarien und koordiniert alle anderen Contexts. Er ist der zentrale Orchestrator der Simulation.

## Domain Model

### **Entities**

#### **Simulation**
```python
@dataclass
class Simulation:
    id: SimulationId
    name: str
    parameters: SimulationParameters
    status: SimulationStatus
    start_time: datetime
    end_time: Optional[datetime]
    current_time: datetime
    created_at: datetime

    def start(self) -> None:
        if self.status != SimulationStatus.READY:
            raise SimulationNotReadyError()

        self.status = SimulationStatus.RUNNING
        self.start_time = datetime.now()
        self.current_time = self.start_time

        # Domain Event
        DomainEvents.raise_event(SimulationStartedEvent(
            simulation_id=self.id.value,
            parameters=self.parameters,
            start_time=self.start_time,
            timestamp=datetime.now()
        ))

    def pause(self) -> None:
        if self.status != SimulationStatus.RUNNING:
            raise SimulationNotRunningError()

        self.status = SimulationStatus.PAUSED

        # Domain Event
        DomainEvents.raise_event(SimulationPausedEvent(
            simulation_id=self.id.value,
            paused_at=self.current_time,
            timestamp=datetime.now()
        ))

    def stop(self) -> None:
        if self.status not in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
            raise SimulationCannotBeStoppedError()

        self.status = SimulationStatus.STOPPED
        self.end_time = datetime.now()

        # Domain Event
        DomainEvents.raise_event(SimulationStoppedEvent(
            simulation_id=self.id.value,
            end_time=self.end_time,
            duration_minutes=self.get_duration_minutes(),
            timestamp=datetime.now()
        ))

    def advance_time(self, minutes: int) -> None:
        if self.status != SimulationStatus.RUNNING:
            return

        self.current_time += timedelta(minutes=minutes)

        # Domain Event
        DomainEvents.raise_event(SimulationTimeAdvancedEvent(
            simulation_id=self.id.value,
            current_time=self.current_time,
            advanced_minutes=minutes,
            timestamp=datetime.now()
        ))

    def get_duration_minutes(self) -> Optional[int]:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return None
```

#### **SimulationParameters**
```python
@dataclass(frozen=True)
class SimulationParameters:
    train_count: int
    simulation_hours: int
    time_acceleration: float
    train_arrival_interval_minutes: int
    schraubkupplung_percentage: int  # 0-100

    def get_simulation_duration(self) -> timedelta:
        return timedelta(hours=self.simulation_hours)

    def get_total_simulation_minutes(self) -> int:
        return self.simulation_hours * 60
```

### **Value Objects**

#### **TrainArrival**
```python
@dataclass(frozen=True)
class TrainArrival:
    train_id: str
    scheduled_time: datetime
    origin: str
    destination: str
    wagon_count: int
    priority: int
    wagon_configs: List[WagonConfig]
```

#### **WagonConfig**
```python
@dataclass(frozen=True)
class WagonConfig:
    wagon_id: str
    length: float
    weight: float
    front_coupling_type: str
    rear_coupling_type: str
```

#### **ResourceConfiguration**
```python
@dataclass(frozen=True)
class ResourceConfiguration:
    locomotives: int
    workers: int
    retrofit_stations: int
    tracks: Dict[str, int]  # track_type -> count
```

#### **RulesConfiguration**
```python
@dataclass(frozen=True)
class RulesConfiguration:
    train_priority_rules: bool
    wagon_selection_rules: bool
    resource_allocation_rules: bool
```

### **Enums**

#### **SimulationStatus**
```python
class SimulationStatus(Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"
```

## Domain Services

#### **SimulationOrchestrator**
```python
class SimulationOrchestrator:
    def __init__(self,
                 train_operations_service: TrainOperationsService,
                 workshop_service: WorkshopService,
                 rules_engine_service: RulesEngineService,
                 monitoring_service: MonitoringService):
        self._train_ops = train_operations_service
        self._workshop = workshop_service
        self._rules = rules_engine_service
        self._monitoring = monitoring_service

    def process_simulation_step(self, simulation: Simulation, train_schedule: List[TrainArrival]) -> None:
        """Verarbeitet einen Simulationsschritt"""
        if simulation.status != SimulationStatus.RUNNING:
            return

        # 1. Hole ankommende Züge
        arriving_trains = self._get_trains_for_time(train_schedule, simulation.current_time)

        # 2. Verarbeite jeden ankommenden Zug
        for train_arrival in arriving_trains:
            self._process_train_arrival(train_arrival)

        # 3. Verarbeite laufende Umrüstungen
        self._process_ongoing_retrofits()

        # 4. Sammle Metriken
        self._collect_step_metrics(simulation)

        # 5. Prüfe Abschlussbedingungen
        if self._is_simulation_completed(simulation, train_schedule):
            simulation.status = SimulationStatus.COMPLETED

            # Domain Event
            DomainEvents.raise_event(SimulationCompletedEvent(
                simulation_id=simulation.id.value,
                completed_at=simulation.current_time,
                total_duration_minutes=simulation.get_duration_minutes(),
                timestamp=datetime.now()
            ))

    def _get_trains_for_time(self, train_schedule: List[TrainArrival], current_time: datetime) -> List[TrainArrival]:
        """Holt Züge die zu gegebener Zeit ankommen sollen"""
        return [
            arrival for arrival in train_schedule
            if arrival.scheduled_time <= current_time
        ]

    def _is_simulation_completed(self, simulation: Simulation, train_schedule: List[TrainArrival]) -> bool:
        """Prüft ob Simulation abgeschlossen ist"""
        if not train_schedule:
            return True

        # Simulation ist fertig wenn alle Züge angekommen sind und Simulationszeit abgelaufen
        last_train_time = max(arrival.scheduled_time for arrival in train_schedule)
        simulation_end = simulation.start_time + simulation.parameters.get_simulation_duration()

        return simulation.current_time >= max(last_train_time, simulation_end)

    def _process_train_arrival(self, train_arrival: TrainArrival) -> None:
        """Verarbeitet Zugankunft"""
        # Erstelle Zug-Daten
        train_info = TrainInfo(
            id=train_arrival.train_id,
            arrival_time=train_arrival.scheduled_time,
            wagons=[self._wagon_config_to_info(wc) for wc in train_arrival.wagon_configs],
            total_length=sum(wc.length for wc in train_arrival.wagon_configs),
            total_weight=sum(wc.weight for wc in train_arrival.wagon_configs),
            origin=train_arrival.origin,
            destination=train_arrival.destination,
            priority=train_arrival.priority,
            status="arrived"
        )

        # Bestimme Priorität über Rules Engine
        priority = self._rules.evaluate_train_priority(train_info)

        # Simuliere Zug-Ankunft Event
        DomainEvents.raise_event(TrainArrivedEvent(
            train_id=train_arrival.train_id,
            arrival_track="arrival_track_1",
            wagon_count=train_arrival.wagon_count,
            timestamp=train_arrival.scheduled_time
        ))

    def _process_ongoing_retrofits(self) -> None:
        """Verarbeitet laufende Umrüstungen"""
        pending_orders = self._workshop.get_pending_orders()

        # Simuliere Umrüstungsabschlüsse
        for order in pending_orders[:2]:  # Max 2 pro Schritt
            # Simuliere Umrüstungsabschluss
            DomainEvents.raise_event(RetrofitOrderCompletedEvent(
                order_id=order.id,
                wagon_id=order.wagon_id,
                worker_id=order.assigned_worker or "worker_1",
                station_id=order.assigned_station or "station_1",
                coupling_positions=order.coupling_positions,
                duration_minutes=45,
                timestamp=datetime.now()
            ))

    def _collect_step_metrics(self, simulation: Simulation) -> None:
        """Sammelt Metriken für aktuellen Schritt"""
        self._monitoring.record_metric(
            name="simulation_time",
            value=simulation.current_time.timestamp(),
            unit="timestamp",
            source_context="simulation_control",
            tags={"simulation_id": simulation.id.value}
        )

    def _wagon_config_to_info(self, config: WagonConfig) -> WagonInfo:
        """Konvertiert WagonConfig zu WagonInfo"""
        return WagonInfo(
            id=config.wagon_id,
            length=config.length,
            weight=config.weight,
            front_coupling_type=config.front_coupling_type,
            rear_coupling_type=config.rear_coupling_type,
            current_location="arrival_track",
            needs_retrofit=config.front_coupling_type == "schraubkupplung" or config.rear_coupling_type == "schraubkupplung",
            is_fully_dak_equipped=config.front_coupling_type == "dak" and config.rear_coupling_type == "dak",
            is_ready_for_departure=False
        )
```

#### **TrainScheduleGenerator**
```python
class TrainScheduleGenerator:
    def generate_train_schedule(self, parameters: SimulationParameters) -> List[TrainArrival]:
        """Generiert Zugfahrplan basierend auf Parametern"""
        train_arrivals = []
        base_time = datetime.now()

        # Erstelle Züge basierend auf Parametern
        for i in range(parameters.train_count):
            wagon_configs = []
            wagon_count = random.randint(5, 15)

            for j in range(wagon_count):
                # Schraubkupplung-Anteil basierend auf Parameter
                coupling_type = "schraubkupplung" if random.random() < (parameters.schraubkupplung_percentage / 100) else "dak"

                wagon_configs.append(WagonConfig(
                    wagon_id=f"wagon_{i}_{j}",
                    length=random.uniform(15.0, 25.0),
                    weight=random.uniform(20.0, 80.0),
                    front_coupling_type=coupling_type,
                    rear_coupling_type=coupling_type
                ))

            train_arrivals.append(TrainArrival(
                train_id=f"train_{i:03d}",
                scheduled_time=base_time + timedelta(minutes=i * parameters.train_arrival_interval_minutes),
                origin=f"Origin_{i}",
                destination=f"Destination_{i}",
                wagon_count=wagon_count,
                priority=random.randint(1, 10),
                wagon_configs=wagon_configs
            ))

        return train_arrivals
```

## Domain Events

#### **Simulation Events**
```python
@dataclass(frozen=True)
class SimulationStartedEvent:
    simulation_id: str
    parameters: SimulationParameters
    start_time: datetime
    timestamp: datetime

@dataclass(frozen=True)
class SimulationPausedEvent:
    simulation_id: str
    paused_at: datetime
    timestamp: datetime

@dataclass(frozen=True)
class SimulationStoppedEvent:
    simulation_id: str
    end_time: datetime
    duration_minutes: int
    timestamp: datetime

@dataclass(frozen=True)
class SimulationCompletedEvent:
    simulation_id: str
    completed_at: datetime
    total_duration_minutes: int
    timestamp: datetime

@dataclass(frozen=True)
class SimulationTimeAdvancedEvent:
    simulation_id: str
    current_time: datetime
    advanced_minutes: int
    timestamp: datetime
```

## Data Transfer Objects (DTOs)

#### **SimulationInfo**
```python
@dataclass(frozen=True)
class SimulationInfo:
    id: str
    name: str
    status: str
    start_time: Optional[datetime]
    current_time: datetime
    time_acceleration: float
    scenario_name: str
    duration_minutes: Optional[int]
```

#### **ScenarioInfo**
```python
@dataclass(frozen=True)
class ScenarioInfo:
    id: str
    name: str
    description: str
    train_count: int
    duration_hours: int
    is_active: bool
```

## Application Services

#### **SimulationControlService**
```python
class SimulationControlService:
    """Öffentliche API für Simulationssteuerung"""

    def __init__(self,
                 simulation_repository: SimulationRepository,
                 scenario_repository: ScenarioRepository,
                 orchestrator: SimulationOrchestrator,
                 generator: ScenarioGenerator):
        self._simulations = simulation_repository
        self._scenarios = scenario_repository
        self._orchestrator = orchestrator
        self._generator = generator

    def create_simulation(self, name: str, parameters: SimulationParameters) -> str:
        """Erstellt neue Simulation"""
        simulation = Simulation(
            id=SimulationId(f"sim_{int(datetime.now().timestamp())}"),
            name=name,
            parameters=parameters,
            status=SimulationStatus.READY,
            start_time=datetime.now(),
            end_time=None,
            current_time=datetime.now(),
            created_at=datetime.now()
        )

        self._simulations.save(simulation)
        return simulation.id.value

    def start_simulation(self, simulation_id: str) -> bool:
        """Startet Simulation"""
        try:
            simulation = self._simulations.get_by_id(SimulationId(simulation_id))
            simulation.start()
            self._simulations.save(simulation)
            return True
        except:
            return False

    def pause_simulation(self, simulation_id: str) -> bool:
        """Pausiert Simulation"""
        try:
            simulation = self._simulations.get_by_id(SimulationId(simulation_id))
            simulation.pause()
            self._simulations.save(simulation)
            return True
        except:
            return False

    def stop_simulation(self, simulation_id: str) -> bool:
        """Stoppt Simulation"""
        try:
            simulation = self._simulations.get_by_id(SimulationId(simulation_id))
            simulation.stop()
            self._simulations.save(simulation)
            return True
        except:
            return False

    def run_simulation_step(self, simulation_id: str) -> bool:
        """Führt einen Simulationsschritt aus"""
        try:
            simulation = self._simulations.get_by_id(SimulationId(simulation_id))

            # Generiere Zugfahrplan falls noch nicht vorhanden
            if not hasattr(simulation, '_train_schedule'):
                simulation._train_schedule = self._generator.generate_train_schedule(simulation.parameters)

            # Verarbeite Schritt
            self._orchestrator.process_simulation_step(simulation, simulation._train_schedule)

            # Advance Zeit
            simulation.advance_time(5)  # 5 Minuten pro Schritt

            self._simulations.save(simulation)
            return True
        except:
            return False

    def get_simulation_status(self, simulation_id: str) -> Optional[SimulationInfo]:
        """Holt Simulationsstatus"""
        try:
            simulation = self._simulations.get_by_id(SimulationId(simulation_id))
            scenario = self._scenarios.get_by_id(simulation.scenario_id)

            return SimulationInfo(
                id=simulation.id.value,
                name=simulation.name,
                status=simulation.status.value,
                start_time=simulation.start_time,
                current_time=simulation.current_time,
                time_acceleration=simulation.time_acceleration,
                scenario_name=scenario.name,
                duration_minutes=simulation.get_duration_minutes()
            )
        except:
            return None

    def create_default_scenario(self) -> str:
        """Erstellt Standard-Szenario"""
        scenario = self._generator.create_default_scenario()
        self._scenarios.save(scenario)
        return scenario.id.value

    def get_available_scenarios(self) -> List[ScenarioInfo]:
        """Holt verfügbare Szenarien"""
        scenarios = self._scenarios.find_active()
        return [
            ScenarioInfo(
                id=s.id.value,
                name=s.name,
                description=s.description,
                train_count=len(s.train_schedule),
                duration_hours=int(s.simulation_duration.total_seconds() / 3600),
                is_active=s.is_active
            )
            for s in scenarios
        ]
```

## Integration mit anderen Contexts

### **Orchestrator für alle Contexts:**
- Koordiniert Train Operations, Workshop, Resource Management
- Nutzt Rules Engine für Entscheidungen
- Sendet Events an Monitoring

### **Customer von allen Contexts:**
- Empfängt Status-Updates über DTOs
- Nutzt Services aller anderen Contexts

### **Supplier für alle Contexts:**
- Steuert Simulationszeit
- Triggert Events für andere Contexts
- Koordiniert Gesamtablauf

## Simulation Loop

```python
class SimulationLoop:
    def __init__(self, control_service: SimulationControlService):
        self._control = control_service
        self._running = False

    async def run_simulation(self, simulation_id: str) -> None:
        """Führt Simulation aus"""
        self._running = True

        while self._running:
            success = self._control.run_simulation_step(simulation_id)
            if not success:
                break

            # Prüfe Status
            status = self._control.get_simulation_status(simulation_id)
            if not status or status.status in ["stopped", "completed", "error"]:
                break

            # Warte zwischen Schritten
            await asyncio.sleep(1.0)  # 1 Sekunde pro Schritt

    def stop_loop(self) -> None:
        self._running = False
```

## Nächste Schritte

1. **Repository-Implementierungen** für Simulation und Scenario
2. **Async Simulation Loop** für kontinuierlichen Betrieb
3. **Szenario-Editor** für benutzerdefinierte Szenarien
4. **Simulation-Snapshots** für Wiederherstellung

Sollen wir als nächstes den **Notification Context** ausarbeiten?
