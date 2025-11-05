# PopUpSim MVP - SimPy Integration

## Übersicht

Diese Datei beschreibt die Integration von SimPy als Discrete Event Simulation Engine für den MVP. Der Fokus liegt auf einem **Thin Adapter Pattern**, um die Domain Logic von SimPy zu entkoppeln und zukünftige Austauschbarkeit zu ermöglichen.

---

## Architektur-Prinzip: Thin Adapter

```
┌─────────────────────────────────────────┐
│     Domain Logic (Framework-frei)      │
│  Workshop, Wagon, Train, Track          │
└─────────────────┬───────────────────────┘
                  │
                  │ Interface
                  │
┌─────────────────▼───────────────────────┐
│      SimPy Adapter (Thin Layer)         │
│  - SimPy Environment Wrapper            │
│  - Process Generators                   │
│  - Resource Management                  │
└─────────────────┬───────────────────────┘
                  │
                  │
┌─────────────────▼───────────────────────┐
│         SimPy Framework                 │
│  Environment, Resource, Process         │
└─────────────────────────────────────────┘
```

**Ziel:** Domain Logic kann ohne SimPy getestet werden, SimPy kann später ausgetauscht werden.

---

## SimPy Core Concepts

### Environment
```python
import simpy

# SimPy Environment = Simulationsuhr
env = simpy.Environment()

# Zeit in Minuten (MVP Konvention)
env.run(until=480)  # 8 Stunden = 480 Minuten
```

### Resource
```python
# Resource = Begrenzte Kapazität (z.B. Werkstattgleis)
track_resource = simpy.Resource(env, capacity=5)

# Request = Ressource anfordern
with track_resource.request() as req:
    yield req  # Warten bis verfügbar
    # Ressource ist jetzt belegt
    yield env.timeout(30)  # 30 Minuten arbeiten
    # Ressource wird automatisch freigegeben
```

### Process
```python
# Process = Generator-Funktion
def train_arrival_process(env):
    while True:
        yield env.timeout(60)  # Alle 60 Minuten
        print(f"Zug kommt an bei t={env.now}")

# Process registrieren
env.process(train_arrival_process(env))
```

---

## MVP SimPy Adapter

### 1. Environment Wrapper

```python
from typing import Protocol
import simpy

class SimulationEnvironment(Protocol):
    """Interface für Simulation Environment (SimPy-unabhängig)"""

    @property
    def now(self) -> float:
        """Aktuelle Simulationszeit"""
        ...

    def timeout(self, delay: float):
        """Warte für delay Zeiteinheiten"""
        ...

    def process(self, generator):
        """Registriere einen Process"""
        ...

    def run(self, until: float):
        """Führe Simulation aus bis Zeit 'until'"""
        ...


class SimPyEnvironmentAdapter:
    """Thin Adapter für SimPy Environment"""

    def __init__(self):
        self._env = simpy.Environment()

    @property
    def now(self) -> float:
        return self._env.now

    def timeout(self, delay: float):
        return self._env.timeout(delay)

    def process(self, generator):
        return self._env.process(generator)

    def run(self, until: float):
        self._env.run(until=until)

    @property
    def simpy_env(self) -> simpy.Environment:
        """Zugriff auf natives SimPy Environment (für Resources)"""
        return self._env
```

**Verwendung:**
```python
# Domain Logic nutzt Interface
env = SimPyEnvironmentAdapter()

# SimPy-spezifisch nur im Adapter
track_resource = simpy.Resource(env.simpy_env, capacity=5)
```

---

### 2. Workshop SimPy Adapter

```python
from dataclasses import dataclass
import simpy
from typing import Generator

@dataclass
class WorkshopSimPyAdapter:
    """Adapter zwischen Workshop Domain und SimPy"""

    workshop: Workshop
    env: SimPyEnvironmentAdapter

    def __post_init__(self):
        """Initialisiere SimPy Resources für alle Tracks"""
        for track in self.workshop.tracks:
            track.resource = simpy.Resource(
                self.env.simpy_env,
                capacity=track.capacity
            )

    def train_arrival_process(
        self,
        interval_minutes: int,
        wagons_per_train: int
    ) -> Generator:
        """SimPy Process: Züge kommen an"""
        train_counter = 0

        while True:
            # Warte bis nächster Zug
            yield self.env.timeout(interval_minutes)

            # Erstelle Zug mit Wagen
            train_counter += 1
            train = Train(
                id=f"TRAIN{train_counter:04d}",
                arrival_time=self.env.now,
                wagons=[
                    Wagon(
                        id=f"WAGON{train_counter:04d}_{i:02d}",
                        train_id=f"TRAIN{train_counter:04d}",
                        needs_retrofit=True
                    )
                    for i in range(wagons_per_train)
                ]
            )

            # Starte Retrofit für alle Wagen
            for wagon in train.wagons:
                self.env.process(self.retrofit_process(wagon))

    def retrofit_process(self, wagon: Wagon) -> Generator:
        """SimPy Process: Wagen wird umgerüstet"""
        wagon.arrival_time = self.env.now

        # Wähle Track (MVP: Einfache Strategie - erster verfügbarer)
        track = self._select_track()

        # Fordere Track-Ressource an
        with track.resource.request() as req:
            yield req  # Warten bis Track verfügbar

            # Umrüstung beginnt
            wagon.retrofit_start_time = self.env.now
            wagon.track_id = track.id
            track.current_wagons += 1

            # Umrüstung durchführen
            yield self.env.timeout(track.retrofit_time_min)

            # Umrüstung abgeschlossen
            wagon.retrofit_end_time = self.env.now
            wagon.needs_retrofit = False
            track.current_wagons -= 1

    def _select_track(self) -> WorkshopTrack:
        """Wähle verfügbares Track (MVP: Round-Robin)"""
        # MVP: Einfach erstes verfügbares Track
        for track in self.workshop.tracks:
            if track.is_available():
                return track
        # Fallback: Erstes Track (wird dann warten)
        return self.workshop.tracks[0]
```

---

### 3. Event Logging Adapter

```python
from typing import List

class EventLogger:
    """Loggt Simulation Events für spätere Analyse"""

    def __init__(self):
        self.events: List[SimulationEvent] = []

    def log_train_arrival(self, env: SimulationEnvironment, train: Train):
        event = TrainArrivalEvent(
            timestamp=env.now,
            train_id=train.id,
            wagon_count=len(train.wagons)
        )
        self.events.append(event)

    def log_retrofit_start(
        self,
        env: SimulationEnvironment,
        wagon: Wagon,
        track: WorkshopTrack
    ):
        event = RetrofitStartEvent(
            timestamp=env.now,
            wagon_id=wagon.id,
            track_id=track.id,
            waiting_time=wagon.waiting_time or 0.0
        )
        self.events.append(event)

    def log_retrofit_complete(
        self,
        env: SimulationEnvironment,
        wagon: Wagon,
        track: WorkshopTrack
    ):
        event = RetrofitCompleteEvent(
            timestamp=env.now,
            wagon_id=wagon.id,
            track_id=track.id,
            retrofit_duration=wagon.retrofit_duration or 0.0
        )
        self.events.append(event)


# Integration in Adapter
@dataclass
class WorkshopSimPyAdapter:
    workshop: Workshop
    env: SimPyEnvironmentAdapter
    event_logger: EventLogger

    def retrofit_process(self, wagon: Wagon) -> Generator:
        wagon.arrival_time = self.env.now
        track = self._select_track()

        with track.resource.request() as req:
            yield req

            wagon.retrofit_start_time = self.env.now
            wagon.track_id = track.id
            track.current_wagons += 1

            # Event loggen
            self.event_logger.log_retrofit_start(self.env, wagon, track)

            yield self.env.timeout(track.retrofit_time_min)

            wagon.retrofit_end_time = self.env.now
            wagon.needs_retrofit = False
            track.current_wagons -= 1

            # Event loggen
            self.event_logger.log_retrofit_complete(self.env, wagon, track)
```

---

## Simulation Orchestration

```python
class SimulationService:
    """Orchestriert die gesamte Simulation"""

    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.env = SimPyEnvironmentAdapter()
        self.event_logger = EventLogger()
        self.all_wagons: List[Wagon] = []

    def run(self) -> SimulationResults:
        """Führe Simulation aus"""

        # 1. Setup Workshop
        workshop = self._setup_workshop()

        # 2. Erstelle Adapter
        adapter = WorkshopSimPyAdapter(
            workshop=workshop,
            env=self.env,
            event_logger=self.event_logger
        )

        # 3. Registriere Processes
        self.env.process(
            adapter.train_arrival_process(
                interval_minutes=self.config.trains.arrival_interval_minutes,
                wagons_per_train=self.config.trains.wagons_per_train
            )
        )

        # 4. Führe Simulation aus
        duration_minutes = self.config.duration_hours * 60
        self.env.run(until=duration_minutes)

        # 5. Sammle Ergebnisse
        return self._collect_results(workshop)

    def _setup_workshop(self) -> Workshop:
        """Erstelle Workshop aus Config"""
        tracks = [
            WorkshopTrack(
                id=track_config.id,
                capacity=track_config.capacity,
                retrofit_time_min=track_config.retrofit_time_min,
                current_wagons=0,
                resource=None  # Wird vom Adapter gesetzt
            )
            for track_config in self.config.workshop.tracks
        ]
        return Workshop(id="workshop_001", tracks=tracks)

    def _collect_results(self, workshop: Workshop) -> SimulationResults:
        """Sammle Ergebnisse aus Events und Wagons"""
        # Implementierung siehe KPI Service
        pass
```

---

## Testing Strategy

### Unit Tests (ohne SimPy)

```python
# Domain Logic kann ohne SimPy getestet werden
def test_wagon_waiting_time():
    wagon = Wagon(
        id="W001",
        train_id="T001",
        arrival_time=10.0,
        retrofit_start_time=15.0
    )
    assert wagon.waiting_time == 5.0

def test_track_availability():
    track = WorkshopTrack(
        id="TRACK01",
        capacity=5,
        retrofit_time_min=30,
        current_wagons=3
    )
    assert track.is_available() == True

    track.current_wagons = 5
    assert track.is_available() == False
```

### Integration Tests (mit SimPy)

```python
def test_simple_simulation():
    """Test mit SimPy Environment"""
    env = SimPyEnvironmentAdapter()

    workshop = Workshop(
        id="test_workshop",
        tracks=[
            WorkshopTrack(
                id="TRACK01",
                capacity=2,
                retrofit_time_min=30,
                resource=simpy.Resource(env.simpy_env, capacity=2)
            )
        ]
    )

    adapter = WorkshopSimPyAdapter(
        workshop=workshop,
        env=env,
        event_logger=EventLogger()
    )

    # Erstelle Test-Wagon
    wagon = Wagon(id="W001", train_id="T001")

    # Starte Retrofit Process
    env.process(adapter.retrofit_process(wagon))

    # Führe Simulation aus
    env.run(until=60)

    # Assertions
    assert wagon.retrofit_end_time is not None
    assert wagon.needs_retrofit == False
```

---

## Performance Considerations

### MVP Optimierungen

```python
# 1. Batch Processing von Wagen
def retrofit_batch_process(self, wagons: List[Wagon]) -> Generator:
    """Verarbeite mehrere Wagen gleichzeitig"""
    for wagon in wagons:
        self.env.process(self.retrofit_process(wagon))
    yield self.env.timeout(0)  # Yield control

# 2. Resource Pooling
class ResourcePool:
    """Pool von Tracks für effiziente Auswahl"""

    def __init__(self, tracks: List[WorkshopTrack]):
        self.tracks = tracks
        self._index = 0

    def get_next_available(self) -> WorkshopTrack:
        """Round-Robin Selection"""
        track = self.tracks[self._index]
        self._index = (self._index + 1) % len(self.tracks)
        return track
```

### Monitoring

```python
class SimulationMonitor:
    """Überwacht Simulation Performance"""

    def __init__(self, env: SimulationEnvironment):
        self.env = env
        self.checkpoints: List[float] = []

    def checkpoint(self):
        """Speichere aktuellen Zeitpunkt"""
        self.checkpoints.append(self.env.now)

    def progress_percentage(self, total_duration: float) -> float:
        """Berechne Fortschritt in %"""
        return (self.env.now / total_duration) * 100
```

---

## Migration Path (Post-MVP)

### Vollversion: Austausch von SimPy

```python
# Alternative: Salabim
class SalabimEnvironmentAdapter(SimulationEnvironment):
    def __init__(self):
        import salabim as sim
        self._env = sim.Environment()

    # Implementiere gleiche Interface
    ...

# Alternative: Custom Discrete Event Engine
class CustomDESAdapter(SimulationEnvironment):
    def __init__(self):
        self._event_queue = PriorityQueue()
        self._current_time = 0.0

    # Implementiere gleiche Interface
    ...
```

**Aufwand:** 2-3 Tage, da Domain Logic unverändert bleibt.

---

## Best Practices

### ✅ Do's
- Domain Logic in separaten Klassen (ohne SimPy Imports)
- Thin Adapter Pattern verwenden
- Events für Nachvollziehbarkeit loggen
- Generator-Funktionen klein halten
- Type Hints für bessere IDE-Unterstützung

### ❌ Don'ts
- SimPy nicht direkt in Domain Logic importieren
- Keine komplexe Logik in Generator-Funktionen
- Keine globalen SimPy Resources
- Keine direkten `yield` Statements in Domain Models

---

**Navigation:** [← 3 Domain model](03-mvp-domain-model.md) | [Data flow →](05-mvp-data-flow.md)
