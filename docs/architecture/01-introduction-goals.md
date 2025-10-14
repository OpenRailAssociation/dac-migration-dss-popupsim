# 1. Einführung und Ziele (MVP)

## 1.1 MVP Aufgabenstellung

PopUpSim MVP simuliert die schlagartige Umrüstung von Güterwagen von Schraubkupplung auf Digitale Automatische Kupplung (DAK) in einer **vereinfachten, dateibasierten Implementierung** für schnelle Prototypenerstellung.

### MVP Kernfunktionen
- **Mikroskopische Simulation** von Umrüstungsprozessen (vereinfacht)
- **Deterministische, diskrete ereignisorientierte Simulation** unter Nutzung des *SimPy* Frameworks
- **Matplotlib-basierte Visualisierung** (keine Web-Interface)
- **Szenario-basierte Kapazitätsplanung** für Pop-Up-Werkstätten
- **Zentrale KPI-Berechnung** im Backend mit CSV/JSON Ausgabe
- **Automatische Engpass-Identifikation** (grundlegend)

### MVP Vereinfachungen
- **3 Bounded Contexts** statt 7 (Configuration, Workshop, Simulation Control)
- **Dateibasierte Datenhaltung** (CSV/JSON) statt Datenbank
- **Matplotlib Plots** statt Web-Frontend
- **Direkte Service-Aufrufe** statt Event-driven Architecture
- **Single-User Desktop-Anwendung**

## 1.2 MVP Qualitätsziele

| Priorität | Qualitätsziel | MVP Szenario | Messbarkeit |
|-----------|---------------|--------------|-------------|
| 1 | **Schnelle Entwicklung** | MVP in 4-5 Wochen entwickelbar | Funktionsfähiger Prototyp |
| 2 | **Determinismus** | Gleiche Eingaben führen zu identischen Ergebnissen | Reproduzierbare Simulationsläufe |
| 3 | **Einfachheit** | Keine komplexe Installation erforderlich | Single Executable |
| 4 | **Testbarkeit** | Domänen-Logik testbar | Unit Tests für Geschäftslogik |
| 5 | **Erweiterbarkeit** | Ausbau zur Vollversion möglich | Saubere Architektur-Basis |

## 1.3 MVP Stakeholder

### Primäre MVP Stakeholder

| Rolle | MVP Erwartungshaltung | Kontakt |
|-------|----------------------|---------|
| **Entwicklungsteam** | Schneller Prototyp, Machbarkeitsbeweis | 3 Senior Backend Entwickler |
| **Fachexperten** | Erste Simulationsergebnisse, Feedback-Möglichkeit | DB Cargo Team |
| **Projektleitung** | Demonstrierbare Ergebnisse, Risiko-Minimierung | Projektmanagement |

## 1.4 MVP User Stories (Reduziert)

PopUpSim MVP unterstützt **4 Hauptanwendungsfälle**:

### MVP Phase 1: Grundfunktionen
- **US-001**: Einfache Werkstatt-Konfiguration laden
- **US-002**: Grundlegende Simulation durchführen

### MVP Phase 2: Auswertung
- **US-003**: KPI-Berechnung und CSV-Export
- **US-004**: Matplotlib-Visualisierung generieren

**Vollständige User Stories:** [requirements/use-cases.md](../requirements/use-cases.md)

## 1.5 MVP Abgrenzung

### Was MVP PopUpSim IST
- ✅ **Proof of Concept** für Simulationslogik
- ✅ **Dateibasierte Konfiguration** (JSON/CSV)
- ✅ **Matplotlib-Ausgabe** für Visualisierung
- ✅ **3-Context Architektur** (vereinfacht)
- ✅ **Desktop-Anwendung** (Single User)

### Was MVP PopUpSim NICHT ist
- ❌ **Web-Anwendung** (kommt in Vollversion)
- ❌ **Event-driven Architecture** (direkte Aufrufe)
- ❌ **Datenbank-Integration** (nur Dateien)
- ❌ **Real-time Updates** (Batch-Verarbeitung)

## 1.6 MVP Erfolgsmetriken

### MVP Technische Metriken
- **Entwicklungszeit:** 4-5 Wochen mit 3 Entwicklern
- **Simulationsgeschwindigkeit:** 1 Simulationsstunde in < 60 Sekunden
- **Skalierbarkeit:** Bis zu 1.000 Wagen pro Simulation
- **Portabilität:** Läuft auf Windows/Mac/Linux mit uv

### MVP Fachliche Metriken
- **Funktionalität:** Grundlegende Umrüstungssimulation funktioniert
- **Ausgabe:** KPIs werden korrekt berechnet und ausgegeben
- **Visualisierung:** Matplotlib-Charts zeigen Simulationsergebnisse
- **Erweiterbarkeit:** Architektur-Basis für Vollversion geschaffen

## 1.7 MVP Entwicklungsstrategie

### Team-Aufteilung (3 Entwickler)
- **Developer 1**: Configuration Context + File I/O
- **Developer 2**: Workshop Context + SimPy Integration
- **Developer 3**: Simulation Control + Analytics/Matplotlib

### MVP Timeline (4-5 Wochen)
- **Woche 1-2**: Grundarchitektur + Configuration Context
- **Woche 2-3**: Workshop Context + Simulation Logic
- **Woche 3-4**: Simulation Control + Integration
- **Woche 4-5**: Analytics + Matplotlib + Testing

### Migration zur Vollversion
```
MVP (3 Contexts) → Vollversion (7 Contexts)
Matplotlib → Web-Frontend
Direkte Aufrufe → Event-driven
```

---

**Navigation:** [← README](README.md) | [MVP Randbedingungen →](02-constraints.md)