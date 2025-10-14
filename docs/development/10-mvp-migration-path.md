# PopUpSim MVP - Migration Path zur Vollversion

## Übersicht

Diese Datei beschreibt den Weg vom MVP zur vollständigen Architektur mit Aufwandsschätzungen und Prioritäten.

---

## MVP vs. Vollversion - Übersicht

| Aspekt | MVP | Vollversion | Aufwand |
|--------|-----|-------------|---------|
| **Bounded Contexts** | 3 Contexts | 7 Contexts | 2-3 Wochen |
| **Architektur** | Layered | Hexagonal + Event-Driven | 1-2 Wochen |
| **Domain Model** | Track-basiert | Station-basiert | 1 Woche |
| **Wagon Types** | Alle gleich | Verschiedene Typen | 3-5 Tage |
| **Workers** | Implizit | Explizit modelliert | 3-5 Tage |
| **Error Handling** | Standard Exceptions | Custom Hierarchy | 2-3 Tage |
| **API** | CLI only | REST API (FastAPI) | 1 Woche |
| **Frontend** | Keine | Vue.js SPA | 3-4 Wochen |
| **Monitoring** | Logs | Prometheus + Grafana | 1 Woche |

**Gesamt-Aufwand:** 10-15 Wochen (2.5-4 Monate)

---

## Phase 1: Domain Model Erweiterung (1-2 Wochen)

### 1.1 Station-basiertes Model

**Aufwand:** 1 Woche | **Priorität:** High

**Änderungen:**
```python
# MVP: Track-basiert
class WorkshopTrack(BaseModel):
    id: str
    capacity: int
    retrofit_time_min: int

# Vollversion: Station-basiert
class WorkshopTrack(BaseModel):
    id: str
    stations: list[Station]

class Station(BaseModel):
    id: str
    position: int
    capacity: int
    workers: list[Worker]
    retrofit_time_min: int
```

**Migration Steps:**
1. Erstelle `Station` Model
2. Refactore `WorkshopTrack` zu Container für Stations
3. Update SimPy Adapter für Station-Resources
4. Migriere Tests
5. Update Konfigurationsformat

**Breaking Changes:**
- Configuration Format ändert sich
- SimPy Adapter muss angepasst werden
- KPI Calculation muss Station-Metriken berücksichtigen

---

### 1.2 Wagon Types

**Aufwand:** 3-5 Tage | **Priorität:** Medium

**Änderungen:**
```python
# MVP: Alle Wagen gleich
class Wagon(BaseModel):
    id: str
    train_id: str
    needs_retrofit: bool

# Vollversion: Verschiedene Typen
class WagonType(str, Enum):
    STANDARD = "standard"
    REFRIGERATED = "refrigerated"
    TANK = "tank"
    FLATBED = "flatbed"

class Wagon(BaseModel):
    id: str
    train_id: str
    wagon_type: WagonType
    needs_retrofit: bool

    def get_retrofit_time_multiplier(self) -> float:
        multipliers = {
            WagonType.STANDARD: 1.0,
            WagonType.REFRIGERATED: 1.2,
            WagonType.TANK: 1.5,
            WagonType.FLATBED: 0.8
        }
        return multipliers[self.wagon_type]
```

**Migration Steps:**
1. Erstelle `WagonType` Enum
2. Füge `wagon_type` zu `Wagon` hinzu
3. Update Retrofit-Zeit-Berechnung
4. Migriere bestehende Daten (alle → STANDARD)
5. Update Tests

---

### 1.3 Explizite Workers

**Aufwand:** 3-5 Tage | **Priorität:** Medium

**Änderungen:**
```python
# MVP: Workers implizit in capacity
class WorkshopTrack(BaseModel):
    capacity: int  # Implizit: capacity = workers

# Vollversion: Workers explizit
class Worker(BaseModel):
    id: str
    name: str
    skill_level: float  # 0.5 - 2.0
    shift_start: int
    shift_end: int

class Station(BaseModel):
    id: str
    workers: list[Worker]

    @property
    def capacity(self) -> int:
        return len(self.workers)
```

**Migration Steps:**
1. Erstelle `Worker` Model
2. Füge `workers` zu `Station` hinzu
3. Update Capacity-Berechnung
4. Implementiere Skill-Level-Multiplikator
5. Update Tests

---

## Phase 2: Architektur-Erweiterung (2-3 Wochen)

### 2.1 Bounded Contexts Expansion

**Aufwand:** 2-3 Wochen | **Priorität:** High

**MVP (3 Contexts):**
- Configuration
- Workshop
- Simulation Control

**Vollversion (7 Contexts):**
- Configuration Management
- Workshop Management
- Train Scheduling
- Simulation Engine
- Analytics & Reporting
- User Management
- System Administration

**Migration Steps:**
1. **Woche 1:** Splitte Workshop Context
   - Workshop Management (Domain Logic)
   - Simulation Engine (SimPy Integration)
2. **Woche 2:** Erstelle neue Contexts
   - Train Scheduling (aus Configuration)
   - Analytics & Reporting (aus Simulation Control)
3. **Woche 3:** Infrastruktur Contexts
   - User Management
   - System Administration

---

### 2.2 Event-Driven Architecture

**Aufwand:** 1-2 Wochen | **Priorität:** High

**MVP: Direct Calls**
```python
# Direct method calls
config = config_service.load_scenario(path)
workshop = workshop_service.setup_workshop(config.workshop)
results = simulation_service.run(workshop)
```

**Vollversion: Event-Driven**
```python
# Event Bus
class EventBus:
    def publish(self, event: DomainEvent):
        for handler in self._handlers[type(event)]:
            handler.handle(event)

# Events
class ConfigurationLoadedEvent(DomainEvent):
    config: ScenarioConfig

class WorkshopSetupCompletedEvent(DomainEvent):
    workshop: Workshop

# Handlers
class WorkshopSetupHandler:
    def handle(self, event: ConfigurationLoadedEvent):
        workshop = self.workshop_service.setup_workshop(event.config.workshop)
        self.event_bus.publish(WorkshopSetupCompletedEvent(workshop=workshop))
```

**Migration Steps:**
1. Implementiere Event Bus
2. Definiere Domain Events
3. Erstelle Event Handlers
4. Refactore Services zu Event-basiert
5. Update Tests

---

### 2.3 Hexagonal Architecture

**Aufwand:** 1 Woche | **Priorität:** Medium

**MVP: Layered**
```
Presentation → Application → Domain → Infrastructure
```

**Vollversion: Hexagonal**
```
         ┌─────────────────┐
         │   Application   │
         │      Core       │
         │    (Domain)     │
         └─────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│ REST  │   │ SimPy │   │  DB   │
│  API  │   │Adapter│   │Adapter│
└───────┘   └───────┘   └───────┘
```

**Migration Steps:**
1. Definiere Port Interfaces
2. Implementiere Adapter
3. Dependency Injection Setup
4. Refactore Services
5. Update Tests

---

## Phase 3: Infrastruktur-Erweiterung (3-4 Wochen)

### 3.1 Database Integration

**Aufwand:** 1 Woche | **Priorität:** High

**MVP: File-based**
```python
# JSON/CSV Files
config = json.load(open("scenario.json"))
results.to_csv("results.csv")
```
---

### 3.2 REST API

**Aufwand:** 1 Woche | **Priorität:** High

**MVP: CLI only**
```bash
python main.py --config config/ --output results/
```

**Vollversion: FastAPI**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.post("/api/v1/scenarios")
async def create_scenario(scenario: ScenarioConfig):
    scenario_id = scenario_service.create(scenario)
    return {"scenario_id": scenario_id}

@app.post("/api/v1/simulations")
async def run_simulation(request: SimulationRequest):
    run_id = simulation_service.start(request.scenario_id)
    return {"run_id": run_id, "status": "started"}

@app.get("/api/v1/simulations/{run_id}")
async def get_simulation_status(run_id: str):
    status = simulation_service.get_status(run_id)
    return {"run_id": run_id, "status": status}

@app.get("/api/v1/simulations/{run_id}/results")
async def get_simulation_results(run_id: str):
    results = simulation_service.get_results(run_id)
    return results
```

**Migration Steps:**
1. Setup FastAPI
2. Definiere API Endpoints
3. Implementiere Request/Response Models
4. Add API Documentation (OpenAPI)
5. Integration Tests

---

### 3.3 Frontend (Vue.js)

**Aufwand:** 3-4 Wochen | **Priorität:** Medium

**Features:**
- Scenario Management (CRUD)
- Simulation Control (Start/Stop/Monitor)
- Real-time Progress Tracking
- Interactive Charts (Plotly.js)
- Results Comparison
- Export Functionality

**Tech Stack:**
- Vue.js 3 + TypeScript
- Pinia (State Management)
- Vue Router
- Axios (HTTP Client)
- Plotly.js (Charts)
- Tailwind CSS (Styling)

**Migration Steps:**
1. **Woche 1:** Setup + Scenario Management
2. **Woche 2:** Simulation Control + Monitoring
3. **Woche 3:** Charts + Visualisierung
4. **Woche 4:** Polish + Testing

---

### 3.4 Monitoring & Observability

**Aufwand:** 1 Woche | **Priorität:** Low

**MVP: Logs only**

**Vollversion: Prometheus + Grafana**
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
simulations_total = Counter('simulations_total', 'Total simulations run')
simulation_duration = Histogram('simulation_duration_seconds', 'Simulation duration')
active_simulations = Gauge('active_simulations', 'Currently running simulations')

# Instrumentation
@simulation_duration.time()
def run_simulation(scenario_id: str):
    simulations_total.inc()
    active_simulations.inc()
    try:
        # Run simulation
        pass
    finally:
        active_simulations.dec()
```

**Dashboards:**
- Simulation Throughput
- Average Duration
- Error Rate
- Resource Usage (CPU, Memory)

---

## Phase 4: Error Handling & Resilience (1 Woche)

### 4.1 Custom Error Hierarchy

**Aufwand:** 2-3 Tage | **Priorität:** Medium

**MVP: Standard Exceptions**
```python
raise ValueError("Invalid configuration")
raise RuntimeError("Simulation failed")
```

**Vollversion: Custom Hierarchy**
```python
class PopUpSimError(Exception):
    """Base exception"""
    pass

class ConfigurationError(PopUpSimError):
    """Configuration-related errors"""
    pass

class InvalidScenarioError(ConfigurationError):
    """Invalid scenario configuration"""
    def __init__(self, scenario_id: str, reason: str):
        self.scenario_id = scenario_id
        self.reason = reason
        super().__init__(f"Invalid scenario {scenario_id}: {reason}")

class SimulationError(PopUpSimError):
    """Simulation-related errors"""
    pass

class TrackCapacityExceededError(SimulationError):
    """Track capacity exceeded"""
    def __init__(self, track_id: str, capacity: int, requested: int):
        self.track_id = track_id
        self.capacity = capacity
        self.requested = requested
        super().__init__(
            f"Track {track_id} capacity {capacity} exceeded (requested: {requested})"
        )
```

---

### 4.2 Retry Logic & Circuit Breaker

**Aufwand:** 2-3 Tage | **Priorität:** Low

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def run_simulation_with_retry(scenario_id: str):
    return simulation_service.run(scenario_id)
```

---

## Migration Roadmap

### Timeline

```
Monat 1: Domain Model + Architektur
├── Woche 1-2: Station-basiertes Model
├── Woche 3: Wagon Types + Workers
└── Woche 4: Event-Driven Architecture

Monat 2: Infrastruktur
├── Woche 5-6: Database + Repository Pattern
├── Woche 7: REST API
└── Woche 8: Authentication

Monat 3-4: Frontend + Polish
├── Woche 9-12: Vue.js Frontend
├── Woche 13: Monitoring
├── Woche 14: Error Handling
└── Woche 15: Testing + Documentation
```

---

## Prioritäten

### Must-Have (Monat 1-2)
1. Station-basiertes Model
2. Event-Driven Architecture
3. Database Integration
4. REST API

### Should-Have (Monat 3)
5. Frontend (Basic)
6. Wagon Types
7. Workers

### Nice-to-Have (Monat 4)
8. Monitoring
9. Advanced Frontend Features
10. Custom Error Hierarchy
11. Performance Optimizations

---

## Backward Compatibility

### Configuration Migration Tool

```python
# migrate_config.py
def migrate_mvp_to_v1(mvp_config: dict) -> dict:
    """Migriere MVP Config zu Vollversion"""

    # Track → Stations
    tracks = []
    for track in mvp_config["workshop"]["tracks"]:
        tracks.append({
            "id": track["id"],
            "stations": [
                {
                    "id": f"{track['id']}_S{i:02d}",
                    "position": i,
                    "capacity": 1,
                    "workers": [
                        {
                            "id": f"W{i:03d}",
                            "name": f"Worker {i}",
                            "skill_level": 1.0
                        }
                    ],
                    "retrofit_time_min": track["retrofit_time_min"]
                }
                for i in range(track["capacity"])
            ]
        })

    return {
        "version": "1.0",
        "duration_hours": mvp_config["duration_hours"],
        "workshop": {"tracks": tracks},
        "trains": mvp_config["trains"]
    }
```

---

## Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking Changes** | High | High | Versioned API, Migration Tools |
| **Performance Degradation** | Medium | High | Performance Tests, Profiling |
| **Timeline Overrun** | Medium | Medium | Phased Rollout, MVP First |
| **Team Capacity** | Medium | Medium | Prioritization, External Help |

---

**Navigation:** [← Deployment](09-mvp-deployment.md) | [Domain Models →](domain-models.md)
