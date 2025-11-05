# PopUpSim MVP - Context Map

## Übersicht

Die PopUpSim MVP-Version besteht aus **3 Bounded Contexts** für schnelle Prototypenerstellung (4-5 Wochen Entwicklungszeit).

## MVP Context Map Diagramm

```mermaid
graph TB
    %% MVP Bounded Contexts
    CONFIG[Configuration Context]
    WORKSHOP[Workshop Context]
    SIMCTRL[Simulation Control Context]

    %% Direct Service Calls (Monolith)
    CONFIG -->|Direct Call| WORKSHOP
    CONFIG -->|Direct Call| SIMCTRL
    WORKSHOP -->|Direct Call| SIMCTRL

    %% File System Integration
    FILES[File System<br/>JSON/CSV]
    OUTPUT[Output Files<br/>CSV/PNG]

    FILES -->|Read| CONFIG
    SIMCTRL -->|Write| OUTPUT

    %% Styling
    classDef coreDomain fill:#4caf50,stroke:#2e7d32,stroke-width:3px,color:#fff
    classDef supportingDomain fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    classDef genericDomain fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#fff
    classDef external fill:#9e9e9e,stroke:#616161,stroke-width:2px

    class WORKSHOP coreDomain
    class CONFIG supportingDomain
    class SIMCTRL genericDomain
    class FILES,OUTPUT external
```

## MVP Context Relationships

### **Core Domain** (Geschäftskritisch)

#### **Workshop Context**
- **DDD-Klassifikation**: Core Domain
- **Rolle**: Kern-Geschäftslogik
- **Verantwortung**:
  - DAK-Umrüstungsprozesse
  - SimPy-Integration für Werkstatt-Simulation
  - Arbeitsplanung und Ressourcenzuweisung
- **Abhängigkeiten**: Configuration Context (für Setup-Daten)
- **Integration**: Direkte Service-Aufrufe
- **SimPy**: Workshop Processes, Worker Scheduling, Station Resources
- **Vereinfachung**: Kombiniert Workshop + Train Operations + Resource Management aus Vollversion

### **Supporting Subdomain** (Notwendig)

#### **Configuration Context**
- **DDD-Klassifikation**: Supporting Subdomain
- **Rolle**: Gateway & Validation Context
- **Verantwortung**:
  - JSON/CSV Import
  - Datenvalidierung (syntaktisch + fachlich)
  - Szenario-Setup
- **Kunden**: Workshop Context, Simulation Control Context
- **Integration**: Direkte Service-Aufrufe, Pydantic Models
- **Validierung**: Eingabedaten-Konsistenz, Plausibilitätsprüfungen
- **Vereinfachung**: Kombiniert Configuration + Infrastructure aus Vollversion

### **Generic Subdomain** (Standard)

#### **Simulation Control Context**
- **DDD-Klassifikation**: Generic Subdomain
- **Rolle**: Orchestrator & Output Generator
- **Verantwortung**:
  - SimPy Environment Management
  - Orchestrierung der Simulation
  - KPI-Berechnung
  - Matplotlib-Visualisierung
  - CSV-Export
- **Abhängigkeiten**: Configuration Context, Workshop Context
- **Integration**: Direkte Service-Aufrufe
- **SimPy**: Environment, Process Orchestration, Time Management
- **Vereinfachung**: Kombiniert Simulation Control + Analytics aus Vollversion

## DDD Context Map Patterns (MVP)

### **1. Customer/Supplier Development** ✅
**Angewendet zwischen**: Configuration → Workshop, Configuration → Simulation Control
- **Upstream**: Configuration Context
- **Downstream**: Workshop Context, Simulation Control Context
- **Implementierung**: Direkte Python-Methodenaufrufe
- **Charakteristik**: Configuration stellt Setup-Daten bereit

### **2. Conformist** ✅
**Angewendet zwischen**: Workshop → Configuration
- **Downstream**: Workshop Context
- **Upstream**: Configuration Context
- **Charakteristik**: Workshop akzeptiert Configuration-Modelle ohne Anpassung
- **Grund**: Einfachheit für MVP

### **3. Published Language** ✅
**Angewendet für**: Pydantic Models als gemeinsame Datenstrukturen
- **Sprache**: Pydantic-basierte DTOs
- **Bereiche**: ScenarioConfig, WorkshopConfig, SimulationResults
- **Format**: Type-safe Python Dataclasses

### **Nicht angewendete Patterns (MVP):**
- **Anti-Corruption Layer**: Zu komplex für MVP
- **Open Host Service**: Keine externen Consumer
- **Separate Ways**: Monolithische Architektur
- **Partnership**: Keine gegenseitigen Abhängigkeiten
- **Shared Kernel**: Vermieden zugunsten klarer Grenzen

## Team-Beziehungen (3 Entwickler)

### **Team Structure & Responsibilities**

#### **Developer 1: Configuration Team**
**Verantwortung**: Configuration Context
- **Team-Beziehung**: **Upstream** (andere abhängig)
- **Zeitkritisch**: Muss zuerst fertig werden
- **Deliverables**:
  - JSON/CSV Reader
  - Pydantic Models
  - Validierungslogik
  - File I/O Utilities

#### **Developer 2: Core Simulation Team**
**Verantwortung**: Workshop Context
- **Team-Beziehung**: **Downstream** von Dev 1, **Upstream** von Dev 3
- **Kern-Rolle**: SimPy-Integration und Geschäftslogik
- **Deliverables**:
  - Workshop Domain Models
  - SimPy Processes
  - Umrüstungslogik
  - Worker Scheduling

#### **Developer 3: Control & Output Team**
**Verantwortung**: Simulation Control Context
- **Team-Beziehung**: **Downstream** (abhängig von beiden)
- **Spezialisierung**: Orchestrierung und Visualisierung
- **Deliverables**:
  - SimPy Environment Management
  - KPI-Berechnung
  - Matplotlib Charts
  - CSV Export

### **Koordinations-Matrix**

| Team Pair | Beziehung | Koordinationsaufwand | Kritische Interfaces |
|-----------|-----------|---------------------|---------------------|
| Dev 1 ↔ Dev 2 | Upstream/Downstream | Hoch | Pydantic Models, Configuration DTOs |
| Dev 2 ↔ Dev 3 | Upstream/Downstream | Mittel | SimPy State, Workshop Results |
| Dev 1 ↔ Dev 3 | Upstream/Downstream | Niedrig | Configuration DTOs |

### **Entwicklungsreihenfolge**

#### **Woche 1-2: Foundation (Dev 1 führt)**
- **Dev 1**: Configuration Context (JSON/CSV Import, Validation)
- **Dev 2**: Workshop Domain Models, SimPy Setup
- **Dev 3**: Simulation Control Framework, Output-Design

#### **Woche 2-3: Core Implementation (Dev 2 führt)**
- **Dev 1**: Configuration finalisieren, Test-Daten
- **Dev 2**: Workshop Context, SimPy Integration
- **Dev 3**: KPI-Berechnung, Matplotlib Setup

#### **Woche 3-4: Integration (Dev 3 führt)**
- **Dev 1**: Validierung erweitern
- **Dev 2**: Workshop-Logik finalisieren
- **Dev 3**: Orchestrierung, Output-Generierung

#### **Woche 4-5: Testing & Polish (Alle parallel)**
- **Alle**: Integration Testing, Bug Fixes, Dokumentation

## Integration Patterns (MVP)

### **Direkte Service-Aufrufe**
```python
# Configuration → Workshop
class WorkshopService:
    def __init__(self, config_service: ConfigurationService):
        self._config = config_service

    def setup_workshop(self):
        scenario = self._config.load_scenario()  # Direkter Aufruf
        return self._create_workshop(scenario)

# Workshop → Simulation Control
class SimulationService:
    def __init__(self, workshop_service: WorkshopService):
        self._workshop = workshop_service

    def run_simulation(self):
        workshop = self._workshop.setup_workshop()  # Direkter Aufruf
        return self._execute_simulation(workshop)
```

### **Pydantic Models als Shared Language**
```python
from pydantic import BaseModel

class ScenarioConfig(BaseModel):
    duration_hours: int
    random_seed: int

class WorkshopConfig(BaseModel):
    stations: int
    workers_per_station: int
    retrofit_time_minutes: int

class SimulationResults(BaseModel):
    total_wagons_processed: int
    throughput_per_hour: float
    average_waiting_time: float
```

## Context Boundaries (MVP)

### **Fachliche Abgrenzung**

#### **Configuration Context**
- **Innerhalb**: JSON/CSV Import, Datenvalidierung, Szenario-Setup
- **Außerhalb**: Geschäftslogik, Simulation, Visualisierung

#### **Workshop Context**
- **Innerhalb**: DAK-Umrüstung, SimPy Processes, Arbeitsplanung
- **Außerhalb**: Datenimport, Orchestrierung, Output-Generierung

#### **Simulation Control Context**
- **Innerhalb**: SimPy Environment, Orchestrierung, KPI-Berechnung, Output
- **Außerhalb**: Geschäftslogik, Datenimport

### **Technische Abgrenzung**
- **Separate Python-Module** pro Context
- **Eigene Domain Models** und Services
- **Direkte Methodenaufrufe** (keine APIs)
- **Dateibasierte Persistierung** (CSV/JSON)
- **Keine Datenbank** erforderlich

## Vereinfachungen gegenüber Vollversion

| Vollversion (7 Contexts) | MVP (3 Contexts) | Begründung |
|--------------------------|------------------|------------|
| Infrastructure Context | → Configuration Context | Einfache Topologie in Config-Dateien |
| Resource Management Context | → Workshop Context | Ressourcen direkt in Workshop verwaltet |
| Train Operations Context | → Workshop Context | Vereinfachte Zugabfertigung |
| Analytics Context | → Simulation Control Context | KPIs direkt berechnen |
| Configuration Context | ✅ Configuration Context | Beibehalten |
| Workshop Context | ✅ Workshop Context | Beibehalten (Core Domain) |
| Simulation Control Context | ✅ Simulation Control Context | Beibehalten |

## Migration zur Vollversion

### **MVP → Vollversion Mapping**

```mermaid
graph LR
    subgraph "MVP (3 Contexts)"
        MVPC[Configuration]
        MVPW[Workshop]
        MVPS[Simulation Control]
    end

    subgraph "Vollversion (7 Contexts)"
        FC[Configuration]
        FI[Infrastructure]
        FR[Resource Management]
        FT[Train Operations]
        FW[Workshop]
        FS[Simulation Control]
        FA[Analytics]
    end

    MVPC --> FC
    MVPC --> FI
    MVPW --> FR
    MVPW --> FT
    MVPW --> FW
    MVPS --> FS
    MVPS --> FA
```

### **Migration Path**
1. **Phase 1**: Configuration Context aufteilen → Configuration + Infrastructure
2. **Phase 2**: Workshop Context aufteilen → Workshop + Train Operations + Resource Management
3. **Phase 3**: Simulation Control aufteilen → Simulation Control + Analytics
4. **Phase 4**: Event-driven Architecture einführen
5. **Phase 5**: Hexagonal Architecture implementieren

## Technical Stack (MVP)

### **Backend**
- **Python 3.13** - Einfache Entwicklung
- **SimPy** - Discrete Event Simulation
- **Pydantic** - Type-safe Models
- **Matplotlib** - Visualisierung
- **Pandas** - CSV-Verarbeitung (optional)

### **Datenhaltung**
- **JSON** - Konfigurationsdateien
- **CSV** - Tabellarische Daten
- **PNG** - Matplotlib-Charts
- **Keine Datenbank** - Nur Dateien

### **Deployment**
- **Python Script** - Einfache Ausführung
- **uv** - Schneller Paketmanager
- **Cross-Platform** - Windows/Mac/Linux

## Nächste Schritte

1. ✅ **MVP Context Map erstellt**
2. **Python-Projekt** Setup mit 3 Modulen
3. **Configuration Context** implementieren (Dev 1)
4. **Workshop Context** implementieren (Dev 2)
5. **Simulation Control Context** implementieren (Dev 3)
6. **Integration Testing** (Alle)
7. **Dokumentation** finalisieren

Die **3 MVP Contexts** sind bereit für **schnelle Implementierung** mit **direkten Service-Aufrufen** und **dateibasierter Speicherung**.
