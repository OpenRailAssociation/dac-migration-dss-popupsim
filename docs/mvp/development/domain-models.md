# PopUpSim MVP - Domain Models & Entities

## Übersicht

Diese Datei definiert alle Domain Models und Entities für die MVP-Implementierung. Alle Klassen verwenden **Pydantic** für Type Safety und Validierung.

---

## Configuration Context

### ScenarioConfig

```python
from pydantic import BaseModel, Field
from typing import Optional

class ScenarioConfig(BaseModel):
    """Hauptkonfiguration für ein Simulationsszenario"""
    duration_hours: int = Field(gt=0, description="Simulationsdauer in Stunden")
    random_seed: int = Field(default=42, description="Seed für Reproduzierbarkeit")

    workshop: "WorkshopConfig"
    trains: "TrainConfig"

class WorkshopConfig(BaseModel):
    """Werkstatt-Konfiguration (MVP: Vereinfacht)"""
    tracks: list["WorkshopTrackConfig"] = Field(min_length=1)

class WorkshopTrackConfig(BaseModel):
    """Werkstattgleis mit Gesamtkapazität (MVP: Vereinfacht)"""
    id: str = Field(pattern=r"^TRACK\d{2}$", description="Track ID (z.B. TRACK01)")
    capacity: int = Field(gt=0, le=20, description="Gesamtkapazität des Gleises")
    retrofit_time_min: int = Field(ge=10, le=300, description="Umrüstzeit in Minuten")

    # Hinweis für Vollversion:
    # In Vollversion wird dies zu list[StationConfig] mit einzelnen Stationen

class TrainConfig(BaseModel):
    """Zug-Ankunfts-Konfiguration"""
    arrival_interval_minutes: int = Field(gt=0, description="Intervall zwischen Zügen")
    wagons_per_train: int = Field(gt=0, le=50, description="Wagen pro Zug")
```

---

## Workshop Context

### Workshop Domain

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import simpy

class Workshop(BaseModel):
    """Werkstatt mit mehreren Gleisen (MVP: Vereinfacht)"""
    id: str
    tracks: list["WorkshopTrack"]

    class Config:
        arbitrary_types_allowed = True  # Für SimPy Resources

class WorkshopTrack(BaseModel):
    """Werkstattgleis mit SimPy Resource (MVP: Vereinfacht)"""
    id: str
    capacity: int
    retrofit_time_min: int
    current_wagons: int = 0

    # SimPy Resource (wird zur Laufzeit gesetzt)
    resource: Optional[simpy.Resource] = None

    class Config:
        arbitrary_types_allowed = True

    def is_available(self) -> bool:
        """Prüft ob Gleis verfügbar ist"""
        return self.current_wagons < self.capacity

class Wagon(BaseModel):
    """Güterwagen zur Umrüstung (MVP: Vereinfacht - alle Wagen gleich)"""
    id: str
    train_id: str
    needs_retrofit: bool = True  # Bestimmt ob Wagen umgerüstet werden muss

    # Zeitstempel
    arrival_time: Optional[float] = None
    retrofit_start_time: Optional[float] = None
    retrofit_end_time: Optional[float] = None

    # MVP: Welches Gleis hat den Wagen bearbeitet
    track_id: Optional[str] = None

    @property
    def waiting_time(self) -> Optional[float]:
        """Wartezeit bis Umrüstung beginnt"""
        if self.arrival_time and self.retrofit_start_time:
            return self.retrofit_start_time - self.arrival_time
        return None

    @property
    def retrofit_duration(self) -> Optional[float]:
        """Tatsächliche Umrüstdauer"""
        if self.retrofit_start_time and self.retrofit_end_time:
            return self.retrofit_end_time - self.retrofit_start_time
        return None

class Train(BaseModel):
    """Zug mit mehreren Wagen"""
    id: str
    wagons: list[Wagon]
    arrival_time: float

    @property
    def wagon_count(self) -> int:
        return len(self.wagons)
```

---

## Simulation Control Context

### Simulation Results

```python
from pydantic import BaseModel, Field
from typing import Optional

class SimulationResults(BaseModel):
    """Ergebnisse einer Simulation"""
    scenario_id: str
    duration_hours: float

    # Durchsatz
    total_wagons_processed: int = Field(ge=0)
    throughput_per_hour: float = Field(ge=0.0)

    # Wartezeiten
    average_waiting_time: float = Field(ge=0.0, description="Durchschnittliche Wartezeit in Minuten")
    max_waiting_time: float = Field(ge=0.0)
    min_waiting_time: float = Field(ge=0.0)

    # Auslastung
    track_utilization: float = Field(ge=0.0, le=1.0, description="Durchschnittliche Gleisauslastung (MVP)")

    # Warteschlange
    average_queue_length: float = Field(ge=0.0)
    max_queue_length: int = Field(ge=0)

    # Zeitstempel
    simulation_start: datetime
    simulation_end: datetime

class KPIData(BaseModel):
    """KPI-Datenpunkt für Zeitreihen"""
    timestamp: float = Field(description="Simulationszeit in Stunden")

    # Momentane Werte
    throughput: float = Field(ge=0.0, description="Wagen/Stunde")
    utilization: float = Field(ge=0.0, le=1.0, description="Auslastung 0-1")
    queue_length: int = Field(ge=0, description="Wartende Wagen")
    waiting_time: float = Field(ge=0.0, description="Aktuelle Wartezeit")

    # Kumulative Werte
    total_processed: int = Field(ge=0, description="Gesamt verarbeitete Wagen")

class TrackMetrics(BaseModel):
    """Metriken pro Werkstattgleis (MVP: Vereinfacht)"""
    track_id: str
    wagons_processed: int = Field(ge=0)
    utilization: float = Field(ge=0.0, le=1.0)
    average_retrofit_time: float = Field(ge=0.0)
    idle_time: float = Field(ge=0.0, description="Leerlaufzeit in Stunden")

    # Hinweis für Vollversion:
    # In Vollversion wird dies zu StationMetrics mit Pro-Station-Details
```

---

## Simulation Events

```python
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class EventType(str, Enum):
    """Typen von Simulationsereignissen"""
    TRAIN_ARRIVAL = "train_arrival"
    WAGON_QUEUED = "wagon_queued"
    RETROFIT_START = "retrofit_start"
    RETROFIT_COMPLETE = "retrofit_complete"
    TRACK_OCCUPIED = "track_occupied"  # MVP: Gleis statt Station
    TRACK_FREE = "track_free"  # MVP: Gleis statt Station

class SimulationEvent(BaseModel):
    """Basis-Event für alle Simulationsereignisse"""
    timestamp: float = Field(description="Simulationszeit in Stunden")
    event_type: EventType
    data: dict

class TrainArrivalEvent(BaseModel):
    """Zug kommt an"""
    timestamp: float
    train_id: str
    wagon_count: int

class RetrofitStartEvent(BaseModel):
    """Umrüstung beginnt"""
    timestamp: float
    wagon_id: str
    track_id: str  # MVP: Gleis statt Station
    waiting_time: float

class RetrofitCompleteEvent(BaseModel):
    """Umrüstung abgeschlossen"""
    timestamp: float
    wagon_id: str
    track_id: str  # MVP: Gleis statt Station
    retrofit_duration: float

class TrackOccupiedEvent(BaseModel):
    """Gleis wird belegt (MVP)"""
    timestamp: float
    track_id: str
    current_occupancy: int
    capacity: int

class TrackFreeEvent(BaseModel):
    """Gleis wird frei (MVP)"""
    timestamp: float
    track_id: str
    current_occupancy: int
```

---

## Validation Models

```python
from pydantic import BaseModel, validator

class ValidationResult(BaseModel):
    """Ergebnis einer Validierung"""
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []

    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        self.warnings.append(message)

class ConfigValidation(BaseModel):
    """Validierung für Konfigurationsdaten"""
    scenario: ValidationResult
    workshop: ValidationResult
    trains: ValidationResult

    @property
    def is_valid(self) -> bool:
        return all([
            self.scenario.is_valid,
            self.workshop.is_valid,
            self.trains.is_valid
        ])
```

---

## Error Handling (MVP: Vereinfacht)

```python
# MVP nutzt Standard Python Exceptions
# Keine komplexe Error-Hierarchie

# Konfigurationsfehler
raise ValueError(f"Ungültige Konfiguration: {message}")

# Simulationsfehler
raise RuntimeError(f"Simulationsfehler bei t={time}: {message}")

# Ausgabefehler
raise IOError(f"Ausgabefehler für {file_path}: {message}")

# Validierungsfehler werden von Pydantic automatisch geworfen
```

---

## Verwendungsbeispiele

### Configuration Context (Dev 1)

```python
# Laden und Validieren
from pathlib import Path
import json

def load_scenario(config_path: Path) -> ScenarioConfig:
    with open(config_path / "scenario.json") as f:
        data = json.load(f)

    # Pydantic validiert automatisch
    scenario = ScenarioConfig(**data)
    return scenario

# Beispiel-Nutzung
scenario = load_scenario(Path("config/"))
print(f"Simulation läuft {scenario.duration_hours} Stunden")
print(f"Werkstatt hat {len(scenario.workshop.tracks)} Gleise")
```

### Workshop Context (Dev 2)

```python
# Workshop erstellen (MVP: Vereinfacht)
def setup_workshop(config: WorkshopConfig, env: simpy.Environment) -> Workshop:
    tracks = []
    for track_config in config.tracks:
        track = WorkshopTrack(
            id=track_config.id,
            capacity=track_config.capacity,
            workers=track_config.workers,
            retrofit_time_min=track_config.retrofit_time_min,
            resource=simpy.Resource(env, capacity=track_config.capacity)
        )
        tracks.append(track)

    return Workshop(id="workshop_001", tracks=tracks)

# Wagen verarbeiten (MVP: Vereinfacht)
def process_wagon(env: simpy.Environment, wagon: Wagon, track: WorkshopTrack):
    wagon.arrival_time = env.now

    with track.resource.request() as req:
        yield req

        wagon.retrofit_start_time = env.now
        wagon.track_id = track.id
        track.current_wagons += 1

        yield env.timeout(track.retrofit_time_min / 60)  # Minuten → Stunden

        wagon.retrofit_end_time = env.now
        track.current_wagons -= 1

    return Workshop(id="workshop_001", stations=stations)

# Wagen verarbeiten
def process_wagon(env: simpy.Environment, wagon: Wagon, station: Station):
    wagon.arrival_time = env.now

    with station.resource.request() as req:
        yield req

        wagon.retrofit_start_time = env.now
        station.current_wagons += 1

        yield env.timeout(station.retrofit_time_min / 60)  # Minuten → Stunden

        wagon.retrofit_end_time = env.now
        station.current_wagons -= 1
```

### Simulation Control Context (Dev 3)

```python
# KPIs berechnen
def calculate_kpis(wagons: list[Wagon], duration_hours: float) -> SimulationResults:
    processed = [w for w in wagons if w.retrofit_end_time is not None]

    waiting_times = [w.waiting_time for w in processed if w.waiting_time]

    return SimulationResults(
        scenario_id="scenario_001",
        duration_hours=duration_hours,
        total_wagons_processed=len(processed),
        throughput_per_hour=len(processed) / duration_hours,
        average_waiting_time=sum(waiting_times) / len(waiting_times) if waiting_times else 0,
        max_waiting_time=max(waiting_times) if waiting_times else 0,
        min_waiting_time=min(waiting_times) if waiting_times else 0,
        station_utilization=0.75,  # Berechnung basierend auf Events
        average_queue_length=5.2,
        max_queue_length=15,
        simulation_start=datetime.now(),
        simulation_end=datetime.now()
    )
```

---

## Pydantic Validierungs-Features

### Automatische Validierung

```python
# Fehler bei ungültigen Werten
try:
    station = StationConfig(
        id="INVALID",  # Muss WS\d{3} sein
        capacity=0,     # Muss > 0 sein
        workers=-1,     # Muss > 0 sein
        retrofit_time_min=500  # Muss <= 300 sein
    )
except ValidationError as e:
    print(e.json())
```

### Custom Validators

```python
class ScenarioConfig(BaseModel):
    duration_hours: int
    workshop: WorkshopConfig

    @validator('duration_hours')
    def duration_must_be_reasonable(cls, v):
        if v > 168:  # 1 Woche
            raise ValueError('Simulation länger als 1 Woche nicht sinnvoll')
        return v

    @validator('workshop')
    def workshop_must_have_capacity(cls, v):
        total_capacity = sum(s.capacity for s in v.stations)
        if total_capacity < 2:
            raise ValueError('Werkstatt muss mindestens Kapazität 2 haben')
        return v
```

---

## Type Hints für IDE Support

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpy import Environment, Resource

# Ermöglicht Type Hints ohne zirkuläre Imports
def setup_simulation(env: "Environment") -> Workshop:
    pass
```

---

**Status:** ✅ Bereit für Implementierung | **Pydantic Version:** 2.0+ | **Python:** 3.13

---

**Navigation:** [← Migration Path](10-mvp-migration-path.md) | [← MVP Overview](01-mvp-overview.md)
