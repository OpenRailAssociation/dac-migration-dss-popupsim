# 1. MVP System-Überblick

## 1.1 MVP Scope und Ziele

### Primäres Ziel
Funktionsfähiger Prototyp für Pop-Up-Werkstatt Simulation, der **reale fachliche Probleme löst** und als Basis für Community-Entwicklung dient.

### MVP User Stories (Priorität 1)
- **US-001**: Standardisierte Pop-Up-Werkstätten entwickeln (Templates)
- **US-002**: Durchsatz-Abschätzung für Werkstatt-Layouts
- **US-003**: Infrastrukturdaten importieren (CSV/JSON)
- **US-004**: Kapazitätsabschätzung für geplante Werkstatt

### Nicht im MVP Scope
- **US-005-008**: Erweiterte Visualisierung und Real-time Features

- **Advanced Security**: Lokale Anwendung ohne Authentifizierung
- **Complex UI**: Datei-basierte Konfiguration

## 1.2 System Context

```mermaid
graph TB
    subgraph "PopUpSim MVP System"
        PopUpSim[PopUpSim MVP<br/>Pop-Up-Werkstatt Simulation]
    end

    subgraph "Benutzer"
        Planer[Strategische Planer<br/>Werkstatt-Templates]
        Detailplaner[Detail-Planer<br/>Kapazitätsabschätzung]
    end

    subgraph "Externe Systeme"
        Files[Konfigurationsdateien<br/>JSON, CSV]
        ExtSys[Externe Systeme<br/>Infrastrukturdaten]
        Results[Ergebnis-Export<br/>CSV, JSON]
    end

    Planer -->|Erstellt Templates| PopUpSim
    Detailplaner -->|Konfiguriert Szenarien| PopUpSim

    PopUpSim -->|Lädt Konfiguration| Files
    PopUpSim -->|Importiert Infrastruktur| ExtSys
    PopUpSim -->|Exportiert Ergebnisse| Results

    classDef system fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef user fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class PopUpSim system
    class Planer,Detailplaner user
    class Files,ExtSys,Results external
```

## 1.3 Container-Architektur (C4 Level 2)

```mermaid
graph TB
    subgraph "PopUpSim MVP - Desktop Application"
        subgraph "Python Application"
            Setup[Configuration Context<br/>JSON/CSV Reader<br/>CONTAINER]
            Core[Workshop Context<br/>SimPy Integration<br/>CONTAINER]
            Control[Simulation Control<br/>KPI Calculation<br/>CONTAINER]
            Output[Output Generator<br/>CSV + Matplotlib<br/>CONTAINER]
        end

        subgraph "Data (File System)"
            ConfigFiles[Input Files<br/>JSON/CSV<br/>DATA]
            ResultFiles[Output Files<br/>CSV/PNG<br/>DATA]
        end

        subgraph "External Libraries"
            SimPy[SimPy Framework<br/>EXTERNAL]
            Matplotlib[Matplotlib<br/>EXTERNAL]
            Pydantic[Pydantic<br/>EXTERNAL]
        end
    end

    subgraph "User"
        Developer[Entwickler<br/>CLI/Editor<br/>PERSON]
    end

    Developer -->|Erstellt Config| ConfigFiles
    Developer -->|Startet| Setup
    Developer -->|Analysiert| ResultFiles

    Setup -->|Liest| ConfigFiles
    Setup -->|Validiert| Pydantic
    Setup -->|Übergibt Config| Core

    Core -->|Nutzt| SimPy
    Core -->|Liefert Events| Control

    Control -->|Berechnet KPIs| Output
    Output -->|Nutzt| Matplotlib
    Output -->|Schreibt| ResultFiles

    classDef container fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#fff
    classDef data fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef external fill:#999999,stroke:#6b6b6b,stroke-width:2px,color:#fff
    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff

    class Setup,Core,Control,Output container
    class ConfigFiles,ResultFiles data
    class SimPy,Matplotlib,Pydantic external
    class Developer person
```

## 1.4 Technologie-Stack

### Core
- **Python 3.13**: Hauptsprache
- **SimPy**: Discrete Event Simulation
- **Pydantic**: Datenvalidierung
- **Matplotlib**: Visualisierung (Charts)
- **Pandas**: Datenverarbeitung (CSV)

### Development
- **uv**: Package Manager
- **pytest**: Testing Framework
- **Black**: Code Formatting
- **mypy**: Type Checking

### Nicht im MVP
- ❌ **Web-Frontend**: Nur CLI/Desktop
- ❌ **REST API**: Direkte Python-Aufrufe

## 1.5 Deployment-Architektur

```mermaid
graph TB
    subgraph "Entwickler Laptop"
        subgraph "PopUpSim MVP"
            Python[Python 3.13<br/>SimPy + Matplotlib]
        end

        subgraph "File System"
            Input[config/<br/>scenario.json<br/>train_schedule.csv]
            Output[results/<br/>*.csv<br/>charts/*.png]
        end

        CLI[Terminal/IDE<br/>python main.py]
    end

    CLI -->|Startet| Python
    Python -->|Liest| Input
    Python -->|Schreibt| Output
    CLI -->|Öffnet| Output

    classDef process fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef files fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef user fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Python process
    class Input,Output files
    class CLI user
```

### Installation Requirements
- **Python 3.13** mit uv
- **4GB RAM** für 1.000 Wagen Szenarien
- **500MB Festplatte** für Installation und Daten
- **Kein Web-Browser** erforderlich

## 1.6 Qualitätsattribute MVP

### Performance Ziele
- **Startup Zeit**: < 5 Sekunden
- **Simulation Speed**: 1.000 Wagen in < 30 Sekunden
- **Chart Generation**: < 5 Sekunden
- **Memory Usage**: < 1GB für typische Szenarien

### Funktionale Ziele
- **Determinismus**: Identische Ergebnisse bei gleichen Eingaben
- **Accuracy**: Plausible Durchsatz-Abschätzungen
- **Completeness**: Alle MVP User Stories abgedeckt
- **Usability**: < 1 Stunde für erstes Szenario

### Technische Ziele
- **Testability**: > 80% Code Coverage für Domain Logic
- **Maintainability**: Klare Trennung zwischen Contexts
- **Extensibility**: Einfache Erweiterung um neue Features
- **Portability**: Läuft auf Windows, macOS, Linux

## 1.7 Constraints und Annahmen

### Technische Constraints
- **Desktop Application**: Keine Web-Oberfläche
- **File-based I/O**: Keine Datenbank
- **CLI-basiert**: Keine grafische Benutzeroberfläche
- **Synchronous Processing**: Keine Async/Parallel Verarbeitung

### Fachliche Constraints
- **Pop-Up-Werkstätten**: Fokus auf DAK-Umrüstung
- **Mikroskopische Simulation**: Einzelne Wagen und Ressourcen
- **Deterministic**: Reproduzierbare Ergebnisse
- **Planning Tool**: Nicht für Real-time Betriebsführung

### Annahmen
- **Benutzer**: Entwickler und technische Planer
- **Datenqualität**: Korrekte und vollständige Eingabedaten
- **Hardware**: Standard Business Laptop (4GB RAM, i5 CPU)
- **Network**: Keine Netzwerk-Abhängigkeiten
- **Editor**: Benutzer können JSON/CSV manuell bearbeiten

## 1.8 Risiken und Mitigation

### Technische Risiken
| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **Performance bei 1.000 Wagen** | Mittel | Hoch | Frühes Benchmarking in Woche 3 |
| **SimPy Learning Curve** | Hoch | Mittel | Prototyping und Dokumentation |
| **Matplotlib Limitierungen** | Niedrig | Niedrig | Einfache 2D Charts ausreichend |

### Fachliche Risiken
| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **Unvollständige Domain Model** | Mittel | Hoch | Enge Abstimmung mit Fachexperten |
| **Unrealistische Ergebnisse** | Mittel | Hoch | Validierung mit realen Daten |
| **User Acceptance** | Niedrig | Hoch | Fokus auf Visualisierung |

## 1.9 Success Criteria

### Erfolgskriterien
- ✅ **Template Creation**: Standardisierte Werkstatt-Templates erstellbar
- ✅ **Throughput Estimation**: Plausible Durchsatz-Berechnungen
- ✅ **Data Import**: CSV/JSON Import funktioniert fehlerfrei
- ✅ **Capacity Analysis**: Kapazitätsengpässe werden identifiziert

### Technische Kriterien
- ✅ **Performance**: 1.000 Wagen Szenario in < 30 Sekunden
- ✅ **Stability**: Mehrere Simulationen hintereinander ohne Crash
- ✅ **Usability**: Entwickler erstellt Szenario in < 30 Minuten
- ✅ **Extensibility**: Neue Werkstatt-Typen einfach hinzufügbar

### Business Kriterien
- ✅ **Expert Validation**: Positive Bewertung durch Fachexperten
- ✅ **Real Usage**: Mindestens 1 echtes Planungsszenario
- ✅ **Next Steps**: Klarer Plan für Post-MVP Entwicklung

---

**Navigation:** [← MVP README](README.md) | [3 Contexts →](02-mvp-contexts.md)
